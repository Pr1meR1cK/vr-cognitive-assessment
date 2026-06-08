from __future__ import annotations

import json
import math
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


TARGET_COLUMNS = ["MMSE", "MOCA", "CDR_global", "CDR_SB", "HIS"]
ID_COLUMNS = ["subject_id"]
REQUIRED_COLUMNS = ID_COLUMNS + TARGET_COLUMNS
MOCA_RISK_TARGET = "MOCA < 26"

CORRELATION_COLUMNS = [
    "target",
    "feature",
    "n",
    "pearson_r",
    "spearman_r",
    "abs_spearman_r",
    "sample_note",
]
TWO_FEATURE_COLUMNS = [
    "target",
    "feature_a",
    "feature_b",
    "n",
    "R",
    "R2",
    "adjusted_R2",
    "F_stat",
    "note",
]
PREDICTION_COLUMNS = [
    "subject_id",
    "MOCA",
    "true_moca_risk",
    "risk_probability",
    "risk_score",
    "risk_level",
    "predicted_label",
    "selected_features",
]
METRIC_COLUMNS = [
    "target",
    "model",
    "validation",
    "n",
    "positive_count",
    "negative_count",
    "auc",
    "accuracy",
    "sensitivity",
    "specificity",
    "precision",
    "f1",
    "tp",
    "tn",
    "fp",
    "fn",
]
FEATURE_IMPORTANCE_COLUMNS = ["feature", "selected_in_loocv_folds"]
SCORE_TARGET_COLUMNS = ["MMSE", "MOCA", "CDR_global", "CDR_SB", "HIS"]
USER_REPORT_NOTE = "探索性辅助评估，不代表临床诊断。"
REGRESSION_METRIC_COLUMNS = [
    "target",
    "model",
    "validation",
    "n",
    "mae",
    "rmse",
    "r2",
    "pearson_r",
]


@dataclass(frozen=True)
class TrainingConfig:
    min_n: int = 10
    top_k: int = 20
    model_top_k: int = 12
    l2: float = 1.0
    epochs: int = 2500
    learning_rate: float = 0.05


def load_merged_dataset(input_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    validate_required_columns(df)
    return safe_numeric_frame(df)


def validate_required_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            "Input dataset is missing required columns: " + ", ".join(missing)
        )


def safe_numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    converted = df.copy()
    for col in converted.columns:
        if col not in ID_COLUMNS:
            converted[col] = pd.to_numeric(converted[col], errors="coerce")
    return converted


def with_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if df.empty and len(df.columns) == 0:
        return pd.DataFrame(columns=columns)
    return df


def candidate_feature_columns(df: pd.DataFrame) -> list[str]:
    excluded = set(ID_COLUMNS + TARGET_COLUMNS)
    cols: list[str] = []
    for col in df.columns:
        if col in excluded:
            continue
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique(dropna=True) >= 2:
            cols.append(col)
    return cols


def pearson_corr(x: pd.Series, y: pd.Series) -> float:
    pair = pd.concat([x, y], axis=1).dropna()
    if len(pair) < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return math.nan
    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1], method="pearson"))


def spearman_corr(x: pd.Series, y: pd.Series) -> float:
    pair = pd.concat([x, y], axis=1).dropna()
    if len(pair) < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return math.nan
    xr = pair.iloc[:, 0].rank(method="average")
    yr = pair.iloc[:, 1].rank(method="average")
    return float(xr.corr(yr, method="pearson"))


def compute_correlations(
    df: pd.DataFrame, feature_cols: list[str], min_n: int
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for target in TARGET_COLUMNS:
        for feature in feature_cols:
            pair = df[[feature, target]].dropna()
            if len(pair) < 3 or pair[feature].nunique() < 2 or pair[target].nunique() < 2:
                continue
            sp = spearman_corr(pair[feature], pair[target])
            rows.append(
                {
                    "target": target,
                    "feature": feature,
                    "n": len(pair),
                    "pearson_r": pearson_corr(pair[feature], pair[target]),
                    "spearman_r": sp,
                    "abs_spearman_r": abs(sp) if pd.notna(sp) else math.nan,
                    "sample_note": "reliable_candidate"
                    if len(pair) >= min_n
                    else "low_n_exploratory",
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["target", "abs_spearman_r"], ascending=[True, False])


def fit_ols_metrics(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    x_design = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(x_design, y, rcond=None)
    pred = x_design @ beta
    residual = y - pred
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else math.nan
    n = len(y)
    p = x.shape[1]
    adjusted_r2 = (
        1.0 - (1.0 - r2) * (n - 1) / (n - p - 1)
        if n > p + 1 and pd.notna(r2)
        else math.nan
    )
    if p > 0 and n > p + 1 and pd.notna(r2) and r2 < 1:
        f_stat = (r2 / p) / ((1.0 - r2) / (n - p - 1))
    else:
        f_stat = math.nan
    return {
        "R": math.sqrt(max(r2, 0.0)) if pd.notna(r2) else math.nan,
        "R2": r2,
        "adjusted_R2": adjusted_r2,
        "F_stat": f_stat,
    }


def compute_two_feature_analysis(
    df: pd.DataFrame,
    correlations: pd.DataFrame,
    top_k: int,
    min_n: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if correlations.empty:
        return pd.DataFrame(rows)
    for target in TARGET_COLUMNS:
        top_features = (
            correlations[
                (correlations["target"] == target)
                & (correlations["sample_note"] == "reliable_candidate")
            ]
            .head(top_k)["feature"]
            .tolist()
        )
        for feature_a, feature_b in combinations(top_features, 2):
            pair = df[[target, feature_a, feature_b]].dropna()
            if len(pair) < min_n:
                continue
            x = pair[[feature_a, feature_b]].to_numpy(dtype=float)
            y = pair[target].to_numpy(dtype=float)
            rows.append(
                {
                    "target": target,
                    "feature_a": feature_a,
                    "feature_b": feature_b,
                    "n": len(pair),
                    **fit_ols_metrics(x, y),
                    "note": "F_p_value_not_computed_without_scipy",
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["target", "adjusted_R2"], ascending=[True, False])


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -40, 40)))


def standardize_fit(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    means = np.nanmean(x, axis=0)
    means = np.where(np.isnan(means), 0.0, means)
    filled = np.where(np.isnan(x), means, x)
    stds = np.std(filled, axis=0)
    stds = np.where(stds < 1e-8, 1.0, stds)
    return (filled - means) / stds, means, stds


def standardize_apply(x: np.ndarray, means: np.ndarray, stds: np.ndarray) -> np.ndarray:
    filled = np.where(np.isnan(x), means, x)
    return (filled - means) / stds


def train_logistic_l2(
    x: np.ndarray,
    y: np.ndarray,
    l2: float,
    learning_rate: float,
    epochs: int,
) -> tuple[float, np.ndarray]:
    n, p = x.shape
    positive_rate = float(np.clip(np.mean(y), 1e-4, 1 - 1e-4))
    intercept = math.log(positive_rate / (1 - positive_rate))
    weights = np.zeros(p, dtype=float)
    for _ in range(epochs):
        pred = sigmoid(intercept + x @ weights)
        error = pred - y
        intercept -= learning_rate * float(np.mean(error))
        weights -= learning_rate * ((x.T @ error) / n + (l2 / n) * weights)
    return intercept, weights


def auc_score(y_true: np.ndarray, scores: np.ndarray) -> float:
    pos = y_true == 1
    n_pos = int(np.sum(pos))
    n_neg = int(np.sum(~pos))
    if n_pos == 0 or n_neg == 0:
        return math.nan
    order = np.argsort(scores)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    rank_sum_pos = float(np.sum(ranks[pos]))
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def classification_metrics(y_true: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    pred = (scores >= 0.5).astype(int)
    tp = int(np.sum((pred == 1) & (y_true == 1)))
    tn = int(np.sum((pred == 0) & (y_true == 0)))
    fp = int(np.sum((pred == 1) & (y_true == 0)))
    fn = int(np.sum((pred == 0) & (y_true == 1)))
    return {
        "target": MOCA_RISK_TARGET,
        "model": "Logistic Regression with L2",
        "validation": "LOOCV",
        "n": float(len(y_true)),
        "positive_count": float(np.sum(y_true == 1)),
        "negative_count": float(np.sum(y_true == 0)),
        "auc": auc_score(y_true, scores),
        "accuracy": (tp + tn) / len(y_true),
        "sensitivity": tp / (tp + fn) if tp + fn else math.nan,
        "specificity": tn / (tn + fp) if tn + fp else math.nan,
        "precision": tp / (tp + fp) if tp + fp else math.nan,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else math.nan,
        "tp": float(tp),
        "tn": float(tn),
        "fp": float(fp),
        "fn": float(fn),
    }


def select_features_for_target(
    train_df: pd.DataFrame,
    feature_cols: list[str],
    y: pd.Series,
    top_k: int,
    min_n: int,
) -> list[str]:
    rows: list[tuple[str, float]] = []
    for feature in feature_cols:
        pair = pd.concat([train_df[feature], y], axis=1).dropna()
        if len(pair) < min_n or pair.iloc[:, 0].nunique() < 2:
            continue
        corr = spearman_corr(pair.iloc[:, 0], pair.iloc[:, 1])
        if pd.notna(corr):
            rows.append((feature, abs(corr)))
    rows.sort(key=lambda item: item[1], reverse=True)
    return [feature for feature, _ in rows[:top_k]]


def risk_level(probability: float) -> str:
    score = probability * 100
    if score >= 70:
        return "高风险"
    if score >= 40:
        return "中风险"
    return "低风险"


def loocv_moca_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    config: TrainingConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_df = df[df["MOCA"].notna()].reset_index(drop=True)
    if len(model_df) < max(8, config.min_n):
        return pd.DataFrame(), pd.DataFrame()
    y_all = (model_df["MOCA"] < 26).astype(int)
    if y_all.nunique() < 2:
        return pd.DataFrame(), pd.DataFrame()

    predictions: list[dict[str, Any]] = []
    selected_counts: dict[str, int] = {}
    for test_idx in range(len(model_df)):
        train_mask = np.ones(len(model_df), dtype=bool)
        train_mask[test_idx] = False
        train_df = model_df.loc[train_mask].reset_index(drop=True)
        test_df = model_df.loc[[test_idx]].reset_index(drop=True)
        y_train = (train_df["MOCA"] < 26).astype(int)
        selected = select_features_for_target(
            train_df,
            feature_cols,
            y_train,
            config.model_top_k,
            min_n=max(3, config.min_n - 1),
        )
        if not selected:
            continue
        for feature in selected:
            selected_counts[feature] = selected_counts.get(feature, 0) + 1
        x_train, means, stds = standardize_fit(train_df[selected].to_numpy(dtype=float))
        x_test = standardize_apply(test_df[selected].to_numpy(dtype=float), means, stds)
        intercept, weights = train_logistic_l2(
            x_train,
            y_train.to_numpy(dtype=float),
            l2=config.l2,
            learning_rate=config.learning_rate,
            epochs=config.epochs,
        )
        probability = float(sigmoid(intercept + x_test @ weights)[0])
        predictions.append(
            {
                "subject_id": test_df.loc[0, "subject_id"],
                "MOCA": float(test_df.loc[0, "MOCA"]),
                "true_moca_risk": int(test_df.loc[0, "MOCA"] < 26),
                "risk_probability": probability,
                "risk_score": round(probability * 100, 2),
                "risk_level": risk_level(probability),
                "predicted_label": int(probability >= 0.5),
                "selected_features": ";".join(selected),
            }
        )

    pred_df = pd.DataFrame(predictions)
    freq_df = pd.DataFrame(
        [
            {"feature": feature, "selected_in_loocv_folds": count}
            for feature, count in selected_counts.items()
        ]
    )
    if not freq_df.empty:
        freq_df = freq_df.sort_values("selected_in_loocv_folds", ascending=False)
    return pred_df, freq_df


def train_final_moca_risk_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    config: TrainingConfig,
) -> dict[str, Any]:
    model_df = df[df["MOCA"].notna()].reset_index(drop=True)
    if len(model_df) < max(8, config.min_n):
        return {"trained": False, "reason": "not_enough_samples"}
    y = (model_df["MOCA"] < 26).astype(int)
    if y.nunique() < 2:
        return {"trained": False, "reason": "target_has_single_class"}

    selected = select_features_for_target(
        model_df, feature_cols, y, config.model_top_k, min_n=config.min_n
    )
    if not selected:
        return {"trained": False, "reason": "no_reliable_features"}

    x_train, means, stds = standardize_fit(model_df[selected].to_numpy(dtype=float))
    intercept, weights = train_logistic_l2(
        x_train,
        y.to_numpy(dtype=float),
        l2=config.l2,
        learning_rate=config.learning_rate,
        epochs=config.epochs,
    )
    return {
        "trained": True,
        "target": MOCA_RISK_TARGET,
        "model": "Logistic Regression with L2",
        "selected_features": selected,
        "intercept": float(intercept),
        "weights": [float(v) for v in weights],
        "feature_means": [float(v) for v in means],
        "feature_stds": [float(v) for v in stds],
        "config": config.__dict__,
        "training_rows": int(len(model_df)),
        "positive_count": int(np.sum(y == 1)),
        "negative_count": int(np.sum(y == 0)),
        "note": "探索性风险评估，不代表临床诊断。",
    }


def predict_with_saved_model(df: pd.DataFrame, model: dict[str, Any]) -> pd.DataFrame:
    if not model.get("trained"):
        return pd.DataFrame(columns=PREDICTION_COLUMNS)
    selected = model["selected_features"]
    missing = [feature for feature in selected if feature not in df.columns]
    if missing:
        raise ValueError("Prediction dataset is missing model features: " + ", ".join(missing))

    model_df = df[df["MOCA"].notna()].reset_index(drop=True)
    means = np.array(model["feature_means"], dtype=float)
    stds = np.array(model["feature_stds"], dtype=float)
    weights = np.array(model["weights"], dtype=float)
    x = standardize_apply(model_df[selected].to_numpy(dtype=float), means, stds)
    probabilities = sigmoid(float(model["intercept"]) + x @ weights)

    rows = []
    for idx, probability in enumerate(probabilities):
        row = model_df.loc[idx]
        rows.append(
            {
                "subject_id": row["subject_id"],
                "MOCA": float(row["MOCA"]),
                "true_moca_risk": int(row["MOCA"] < 26),
                "risk_probability": float(probability),
                "risk_score": round(float(probability) * 100, 2),
                "risk_level": risk_level(float(probability)),
                "predicted_label": int(probability >= 0.5),
                "selected_features": ";".join(selected),
            }
        )
    return pd.DataFrame(rows)


def save_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_subject_risk_json(predictions: pd.DataFrame, output_dir: str | Path) -> None:
    if predictions.empty:
        return
    risk_dir = Path(output_dir) / "subject_risk"
    risk_dir.mkdir(parents=True, exist_ok=True)
    for _, row in predictions.iterrows():
        payload = {
            "subject_id": row["subject_id"],
            "risk": {
                "probability": float(row["risk_probability"]),
                "score": float(row["risk_score"]),
                "level": row["risk_level"],
            },
            "model_basis": {
                "target": MOCA_RISK_TARGET,
                "model": "Logistic Regression with L2",
                "validation": "saved_model_prediction",
                "note": "探索性风险评估，不代表临床诊断。",
            },
            "selected_features": str(row["selected_features"]).split(";")
            if row.get("selected_features")
            else [],
        }
        save_json(risk_dir / f"{row['subject_id']}.json", payload)


# The functions below power the user-facing prediction flow. They keep model
# targets extensible while preserving the older MoCA-risk validation workflow.
def risk_level(probability: float) -> str:
    score = probability * 100
    if score >= 70:
        return "高风险"
    if score >= 40:
        return "中风险"
    return "低风险"


def train_ridge_l2(x: np.ndarray, y: np.ndarray, l2: float) -> tuple[float, np.ndarray]:
    x_design = np.column_stack([np.ones(len(x)), x])
    penalty = np.eye(x_design.shape[1]) * l2
    penalty[0, 0] = 0.0
    beta = np.linalg.solve(x_design.T @ x_design + penalty, x_design.T @ y)
    return float(beta[0]), beta[1:].astype(float)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray, target: str) -> dict[str, float | str]:
    residual = y_true - y_pred
    mae = float(np.mean(np.abs(residual)))
    rmse = float(np.sqrt(np.mean(residual**2)))
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else math.nan
    pearson = float(pd.Series(y_true).corr(pd.Series(y_pred))) if len(y_true) >= 3 else math.nan
    return {
        "target": target,
        "model": "Ridge Regression with L2",
        "validation": "LOOCV",
        "n": float(len(y_true)),
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "pearson_r": pearson,
    }


def loocv_score_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    target: str,
    config: TrainingConfig,
) -> pd.DataFrame:
    model_df = df[df[target].notna()].reset_index(drop=True)
    if len(model_df) < max(8, config.min_n) or model_df[target].nunique(dropna=True) < 2:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for test_idx in range(len(model_df)):
        train_mask = np.ones(len(model_df), dtype=bool)
        train_mask[test_idx] = False
        train_df = model_df.loc[train_mask].reset_index(drop=True)
        test_df = model_df.loc[[test_idx]].reset_index(drop=True)
        y_train = train_df[target]
        selected = select_features_for_target(
            train_df,
            feature_cols,
            y_train,
            config.model_top_k,
            min_n=max(3, config.min_n - 1),
        )
        if not selected:
            continue
        x_train, means, stds = standardize_fit(train_df[selected].to_numpy(dtype=float))
        x_test = standardize_apply(test_df[selected].to_numpy(dtype=float), means, stds)
        intercept, weights = train_ridge_l2(x_train, y_train.to_numpy(dtype=float), config.l2)
        predicted = float(intercept + x_test @ weights)
        rows.append(
            {
                "subject_id": test_df.loc[0, "subject_id"],
                "target": target,
                "true_score": float(test_df.loc[0, target]),
                "predicted_score": round(predicted, 3),
                "absolute_error": round(abs(float(test_df.loc[0, target]) - predicted), 3),
                "selected_features": ";".join(selected),
            }
        )
    return pd.DataFrame(rows)


def train_score_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    target: str,
    config: TrainingConfig,
) -> dict[str, Any]:
    model_df = df[df[target].notna()].reset_index(drop=True)
    if len(model_df) < max(8, config.min_n):
        return {"trained": False, "target": target, "type": "score", "reason": "not_enough_samples"}
    if model_df[target].nunique(dropna=True) < 2:
        return {"trained": False, "target": target, "type": "score", "reason": "target_has_single_value"}

    selected = select_features_for_target(
        model_df, feature_cols, model_df[target], config.model_top_k, min_n=config.min_n
    )
    if not selected:
        return {"trained": False, "target": target, "type": "score", "reason": "no_reliable_features"}

    x_train, means, stds = standardize_fit(model_df[selected].to_numpy(dtype=float))
    intercept, weights = train_ridge_l2(
        x_train, model_df[target].to_numpy(dtype=float), config.l2
    )
    return {
        "trained": True,
        "target": target,
        "type": "score",
        "model": "Ridge Regression with L2",
        "selected_features": selected,
        "intercept": float(intercept),
        "weights": [float(v) for v in weights],
        "feature_means": [float(v) for v in means],
        "feature_stds": [float(v) for v in stds],
        "config": config.__dict__,
        "training_rows": int(len(model_df)),
        "note": USER_REPORT_NOTE,
    }


def train_moca_risk_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    config: TrainingConfig,
) -> dict[str, Any]:
    model = train_final_moca_risk_model(df, feature_cols, config)
    model["type"] = "risk"
    model["target"] = MOCA_RISK_TARGET
    model["note"] = USER_REPORT_NOTE
    return model


def predict_user_with_model(
    model: dict[str, Any],
    features: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not model.get("trained"):
        return None, {"missing_model_features": [], "used_feature_count": 0}

    selected = model["selected_features"]
    values: list[float] = []
    missing: list[str] = []
    for feature in selected:
        raw = features.get(feature)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = math.nan
            missing.append(feature)
        values.append(value)

    means = np.array(model["feature_means"], dtype=float)
    stds = np.array(model["feature_stds"], dtype=float)
    weights = np.array(model["weights"], dtype=float)
    x = standardize_apply(np.array([values], dtype=float), means, stds)
    raw_prediction = float(float(model["intercept"]) + x @ weights)

    if model.get("type") == "risk":
        probability = float(sigmoid(np.array([raw_prediction]))[0])
        prediction = {
            "target": model.get("target", MOCA_RISK_TARGET),
            "type": "risk",
            "probability": probability,
            "score": round(probability * 100, 2),
            "level": risk_level(probability),
        }
    else:
        prediction = {
            "target": model["target"],
            "type": "score",
            "value": round(raw_prediction, 2),
            "label": f"预测 {model['target']} 分数",
        }

    data_quality = {
        "missing_model_features": missing,
        "used_feature_count": int(len(selected) - len(missing)),
        "required_feature_count": int(len(selected)),
    }
    return prediction, data_quality


def build_key_findings(
    features: dict[str, Any],
    models: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    findings: list[dict[str, Any]] = []
    feature_text = {
        "diff_success_rate": "复杂任务成功率较简单任务下降",
        "diff_wrong_pickup_rate": "复杂任务错误拾取率较简单任务升高",
        "diff_map_ratio": "复杂任务地图依赖较简单任务增加",
        "diff_stop_ratio": "复杂任务停顿比例较简单任务增加",
        "diff_path_distance": "复杂任务路径距离较简单任务增加",
        "grid9_stop_ratio": "九宫格复杂任务停顿比例较高",
        "grid9_wrong_pickup_rate": "九宫格复杂任务错误拾取率较高",
        "grid9_map_ratio": "九宫格复杂任务地图依赖较高",
        "grid9_success_rate": "九宫格复杂任务成功率偏低",
        "overall_success_rate": "总体任务成功率偏低",
    }

    for model in models:
        for feature in model.get("selected_features", []):
            if feature in seen or feature not in features:
                continue
            try:
                value = float(features[feature])
            except (TypeError, ValueError):
                continue
            seen.add(feature)
            text = feature_text.get(feature, f"{feature} 是模型使用的关键行为特征")
            findings.append(
                {
                    "feature": feature,
                    "value": value,
                    "text": text,
                }
            )
            if len(findings) >= limit:
                return findings
    return findings


def predict_user_from_registry(
    subject_id: str,
    features: dict[str, Any],
    model_dir: str | Path,
) -> dict[str, Any]:
    model_dir = Path(model_dir)
    registry = load_json(model_dir / "model_registry.json")
    predictions: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    loaded_models: list[dict[str, Any]] = []

    for entry in registry.get("models", []):
        if not entry.get("trained"):
            continue
        if not entry.get("enabled_for_user", True):
            continue
        model = load_json(model_dir / entry["file"])
        prediction, quality = predict_user_with_model(model, features)
        if prediction is None:
            continue
        predictions.append(prediction)
        loaded_models.append(model)
        quality_rows.append({"target": model["target"], **quality})

    missing_all = sorted(
        {
            missing
            for row in quality_rows
            for missing in row.get("missing_model_features", [])
        }
    )
    return {
        "subject_id": subject_id,
        "predictions": predictions,
        "key_findings": build_key_findings(features, loaded_models),
        "data_quality": {
            "input_feature_count": len(features),
            "model_count": len(predictions),
            "missing_model_features": missing_all,
            "models": quality_rows,
        },
        "model_basis": {
            "input": "VR log behavior features",
            "registry": str(model_dir / "model_registry.json"),
            "note": USER_REPORT_NOTE,
        },
    }


def render_user_report_html(report: dict[str, Any]) -> str:
    subject_id = report.get("subject_id", "")
    prediction_items = []
    for item in report.get("predictions", []):
        if item.get("type") == "risk":
            text = (
                f"{item.get('target')}: {item.get('level')} "
                f"({item.get('score')}分, 概率 {item.get('probability'):.3f})"
            )
        else:
            text = f"{item.get('label', item.get('target'))}: {item.get('value')}"
        prediction_items.append(f"<li>{text}</li>")

    finding_items = [
        f"<li>{row['text']}：{row['feature']} = {row['value']}</li>"
        for row in report.get("key_findings", [])
    ]
    if not finding_items:
        finding_items = ["<li>当前模型未生成明确的关键行为解释。</li>"]

    missing = report.get("data_quality", {}).get("missing_model_features", [])
    missing_text = "无" if not missing else "、".join(missing)
    note = report.get("model_basis", {}).get("note", USER_REPORT_NOTE)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>VR认知预测报告 - {subject_id}</title>
  <style>
    body {{ font-family: Arial, "Microsoft YaHei", sans-serif; margin: 40px; color: #1f2933; line-height: 1.6; }}
    h1 {{ font-size: 26px; margin-bottom: 8px; }}
    h2 {{ font-size: 18px; margin-top: 28px; border-bottom: 1px solid #d8dee4; padding-bottom: 6px; }}
    .meta {{ color: #52606d; }}
    .note {{ margin-top: 28px; padding: 12px 14px; background: #f5f7fa; border-left: 4px solid #627d98; }}
  </style>
</head>
<body>
  <h1>VR认知预测报告</h1>
  <p class="meta">被试编号：{subject_id}</p>
  <h2>预测结果</h2>
  <ul>{''.join(prediction_items)}</ul>
  <h2>关键行为依据</h2>
  <ul>{''.join(finding_items)}</ul>
  <h2>数据质量</h2>
  <p>输入特征数：{report.get('data_quality', {}).get('input_feature_count', 0)}</p>
  <p>缺失模型特征：{missing_text}</p>
  <div class="note">{note}</div>
</body>
</html>
"""


def write_subject_risk_json(predictions: pd.DataFrame, output_dir: str | Path) -> None:
    if predictions.empty:
        return
    risk_dir = Path(output_dir) / "subject_risk"
    risk_dir.mkdir(parents=True, exist_ok=True)
    for _, row in predictions.iterrows():
        payload = {
            "subject_id": row["subject_id"],
            "risk": {
                "probability": float(row["risk_probability"]),
                "score": float(row["risk_score"]),
                "level": row["risk_level"],
            },
            "model_basis": {
                "target": MOCA_RISK_TARGET,
                "model": "Logistic Regression with L2",
                "validation": "saved_model_prediction",
                "note": USER_REPORT_NOTE,
            },
            "selected_features": str(row["selected_features"]).split(";")
            if row.get("selected_features")
            else [],
        }
        save_json(risk_dir / f"{row['subject_id']}.json", payload)
