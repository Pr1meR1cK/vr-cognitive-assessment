from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cognitive_algorithm_core import (
    FEATURE_IMPORTANCE_COLUMNS,
    METRIC_COLUMNS,
    PREDICTION_COLUMNS,
    REGRESSION_METRIC_COLUMNS,
    SCORE_TARGET_COLUMNS,
    TrainingConfig,
    candidate_feature_columns,
    classification_metrics,
    load_merged_dataset,
    loocv_moca_model,
    loocv_score_model,
    regression_metrics,
    save_json,
    train_moca_risk_model,
    train_score_model,
    with_columns,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train available cognitive models from merged_dataset.csv."
    )
    parser.add_argument("--input", default="examples/mock_merged_dataset.csv")
    parser.add_argument("--model-dir", default="outputs/trained_models")
    parser.add_argument("--min-n", type=int, default=10)
    parser.add_argument("--model-top-k", type=int, default=12)
    parser.add_argument("--l2", type=float, default=1.0)
    parser.add_argument("--epochs", type=int, default=2500)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    config = TrainingConfig(
        min_n=args.min_n,
        model_top_k=args.model_top_k,
        l2=args.l2,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
    )
    df = load_merged_dataset(args.input)
    feature_cols = candidate_feature_columns(df)

    registry: dict[str, object] = {
        "input": str(args.input),
        "candidate_feature_count": int(len(feature_cols)),
        "models": [],
    }

    regression_metric_rows = []
    score_prediction_frames = []
    for target in SCORE_TARGET_COLUMNS:
        model = train_score_model(df, feature_cols, target, config)
        file_name = f"{target.lower()}_score_model.json"
        save_json(model_dir / file_name, model)
        registry["models"].append(
            {
                "target": target,
                "type": "score",
                "file": file_name,
                "trained": bool(model.get("trained")),
                "reason": model.get("reason"),
            }
        )

        score_predictions = loocv_score_model(df, feature_cols, target, config)
        if not score_predictions.empty:
            score_prediction_frames.append(score_predictions)
            regression_metric_rows.append(
                regression_metrics(
                    score_predictions["true_score"].to_numpy(dtype=float),
                    score_predictions["predicted_score"].to_numpy(dtype=float),
                    target,
                )
            )

    loocv_predictions, feature_frequency = loocv_moca_model(df, feature_cols, config)
    loocv_predictions = with_columns(loocv_predictions, PREDICTION_COLUMNS)
    feature_frequency = with_columns(feature_frequency, FEATURE_IMPORTANCE_COLUMNS)

    classification_metrics_df = pd.DataFrame(columns=METRIC_COLUMNS)
    if not loocv_predictions.empty:
        classification_metrics_df = pd.DataFrame(
            [
                classification_metrics(
                    loocv_predictions["true_moca_risk"].to_numpy(dtype=int),
                    loocv_predictions["risk_probability"].to_numpy(dtype=float),
                )
            ]
        )

    risk_model = train_moca_risk_model(df, feature_cols, config)
    save_json(model_dir / "moca_risk_model.json", risk_model)
    registry["models"].append(
        {
            "target": "MOCA < 26",
            "type": "risk",
            "file": "moca_risk_model.json",
            "trained": bool(risk_model.get("trained")),
            "reason": risk_model.get("reason"),
        }
    )

    if score_prediction_frames:
        score_predictions_df = pd.concat(score_prediction_frames, ignore_index=True)
    else:
        score_predictions_df = pd.DataFrame(
            columns=[
                "subject_id",
                "target",
                "true_score",
                "predicted_score",
                "absolute_error",
                "selected_features",
            ]
        )
    regression_metrics_df = with_columns(
        pd.DataFrame(regression_metric_rows), REGRESSION_METRIC_COLUMNS
    )

    regression_quality = {
        row["target"]: row for row in regression_metrics_df.to_dict(orient="records")
    }
    risk_quality = (
        classification_metrics_df.iloc[0].to_dict()
        if not classification_metrics_df.empty
        else {}
    )
    for entry in registry["models"]:
        if not entry.get("trained"):
            entry["enabled_for_user"] = False
            entry["quality_note"] = "model_not_trained"
            continue
        if entry["type"] == "score":
            metrics = regression_quality.get(entry["target"], {})
            r2 = float(metrics.get("r2", -999))
            pearson = abs(float(metrics.get("pearson_r", 0)))
            entry["validation"] = metrics
            entry["enabled_for_user"] = bool(r2 > 0 and pearson >= 0.3)
            entry["quality_note"] = (
                "enabled" if entry["enabled_for_user"] else "held_back_low_loocv_quality"
            )
        else:
            auc = float(risk_quality.get("auc", 0))
            entry["validation"] = risk_quality
            entry["enabled_for_user"] = bool(auc >= 0.6)
            entry["quality_note"] = (
                "enabled" if entry["enabled_for_user"] else "held_back_low_loocv_auc"
            )
    save_json(model_dir / "model_registry.json", registry)

    score_predictions_df.to_csv(
        model_dir / "score_loocv_predictions.csv", index=False, encoding="utf-8-sig"
    )
    regression_metrics_df.to_csv(
        model_dir / "score_model_metrics.csv", index=False, encoding="utf-8-sig"
    )
    loocv_predictions.to_csv(
        model_dir / "loocv_predictions.csv", index=False, encoding="utf-8-sig"
    )
    classification_metrics_df.to_csv(
        model_dir / "model_metrics.csv", index=False, encoding="utf-8-sig"
    )
    feature_frequency.to_csv(
        model_dir / "feature_importance.csv", index=False, encoding="utf-8-sig"
    )

    trained_models = [m for m in registry["models"] if m["trained"]]
    enabled_models = [m for m in registry["models"] if m.get("enabled_for_user")]
    summary = {
        "input": str(args.input),
        "model_dir": str(model_dir),
        "rows": int(len(df)),
        "candidate_feature_count": int(len(feature_cols)),
        "trained_model_count": int(len(trained_models)),
        "enabled_user_model_count": int(len(enabled_models)),
        "available_models": trained_models,
        "enabled_user_models": enabled_models,
        "loocv_prediction_rows": int(len(loocv_predictions)),
        "score_prediction_rows": int(len(score_predictions_df)),
    }
    save_json(model_dir / "training_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
