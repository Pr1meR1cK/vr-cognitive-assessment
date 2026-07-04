from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from cognitive_algorithm_core import (
    PREDICTION_COLUMNS,
    load_json,
    load_merged_dataset,
    predict_with_saved_model,
    save_json,
    with_columns,
    write_subject_risk_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full B workflow: analysis, model training, prediction, and result files."
    )
    parser.add_argument("--input", default="examples/mock_merged_dataset.csv")
    parser.add_argument("--output-dir", default="outputs/cognitive_pipeline")
    parser.add_argument("--min-n", type=int, default=10)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--model-top-k", type=int, default=5)
    parser.add_argument("--l2", type=float, default=1.0)
    parser.add_argument("--epochs", type=int, default=2500)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument(
        "--feature-set",
        choices=["all", "core", "selected"],
        default="selected",
        help="Candidate feature pool used by analysis and training.",
    )
    return parser.parse_args()


def run_step(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    analysis_dir = output_dir / "analysis"
    model_dir = output_dir / "model"
    results_dir = output_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    script_dir = Path(__file__).resolve().parent
    python = sys.executable

    run_step(
        [
            python,
            str(script_dir / "run_cognitive_analysis.py"),
            "--input",
            args.input,
            "--analysis-dir",
            str(analysis_dir),
            "--min-n",
            str(args.min_n),
            "--top-k",
            str(args.top_k),
            "--feature-set",
            args.feature_set,
        ]
    )
    run_step(
        [
            python,
            str(script_dir / "train_cognitive_model.py"),
            "--input",
            args.input,
            "--model-dir",
            str(model_dir),
            "--min-n",
            str(args.min_n),
            "--model-top-k",
            str(args.model_top_k),
            "--l2",
            str(args.l2),
            "--epochs",
            str(args.epochs),
            "--learning-rate",
            str(args.learning_rate),
            "--feature-set",
            args.feature_set,
        ]
    )

    df = load_merged_dataset(args.input)
    registry = load_json(model_dir / "model_registry.json")
    prediction_frames = []
    for entry in registry.get("models", []):
        if entry.get("type") != "risk":
            continue
        if not entry.get("trained") or not entry.get("enabled_for_user"):
            continue
        model = load_json(model_dir / entry["file"])
        model_predictions = predict_with_saved_model(df, model)
        if not model_predictions.empty:
            prediction_frames.append(model_predictions)
    if prediction_frames:
        import pandas as pd

        predictions = pd.concat(prediction_frames, ignore_index=True)
    else:
        predictions = with_columns(type(df)(), PREDICTION_COLUMNS)
    predictions = with_columns(predictions, PREDICTION_COLUMNS)
    predictions.to_csv(
        results_dir / "model_predictions.csv", index=False, encoding="utf-8-sig"
    )
    write_subject_risk_json(predictions, results_dir)

    # Keep the files C expects available in one final folder.
    for name in [
        "correlations.csv",
        "correlations_reliable_n10.csv",
        "two_feature_analysis.csv",
    ]:
        shutil.copyfile(analysis_dir / name, results_dir / name)
    for name in [
        "model_metrics.csv",
        "feature_importance.csv",
        "score_model_metrics.csv",
        "score_loocv_predictions.csv",
        "model_registry.json",
    ]:
        shutil.copyfile(model_dir / name, results_dir / name)

    summary = {
        "input": str(args.input),
        "output_dir": str(output_dir),
        "analysis_dir": str(analysis_dir),
        "model_dir": str(model_dir),
        "results_dir": str(results_dir),
        "feature_set": args.feature_set,
        "prediction_rows": int(len(predictions)),
        "model_trained": any(
            bool(entry.get("trained"))
            for entry in registry.get("models", [])
            if entry.get("type") == "risk"
        ),
        "enabled_user_model_count": int(
            sum(
                1
                for entry in registry.get("models", [])
                if entry.get("type") == "risk" and entry.get("enabled_for_user")
            )
        ),
        "selected_feature_count": int(
            sum(
                len(load_json(model_dir / entry["file"]).get("selected_features", []))
                for entry in registry.get("models", [])
                if entry.get("type") == "risk"
                and entry.get("trained")
                and entry.get("enabled_for_user")
            )
        ),
        "note": "No fixed manual weights are used. Available models are listed in model_registry.json.",
    }
    save_json(results_dir / "run_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
