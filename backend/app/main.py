from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


APP_ROOT = Path(__file__).resolve().parents[2]
MOCK_DIR = APP_ROOT / "frontend" / "src" / "mock"
FRONTEND_API_DIRS = [
    APP_ROOT / "outputs" / "frontend_api_real",
    APP_ROOT / "outputs" / "frontend_api_mock_full",
    APP_ROOT / "outputs" / "frontend_api",
]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_mock(name: str) -> Any:
    return read_json(MOCK_DIR / name)


def frontend_api_dir() -> Path | None:
    for path in FRONTEND_API_DIRS:
        if (path / "index.json").exists():
            return path
    return None


def load_payload(name: str) -> Any | None:
    payload_dir = frontend_api_dir()
    if payload_dir is None:
        return None
    path = payload_dir / name
    if not path.exists():
        return None
    return read_json(path)


def data_source() -> dict[str, str]:
    payload_dir = frontend_api_dir()
    if payload_dir is None:
        return {"mode": "mock", "path": str(MOCK_DIR.relative_to(APP_ROOT))}
    return {"mode": "frontend_api", "path": str(payload_dir.relative_to(APP_ROOT))}


def risk_score(probability: float) -> int:
    return round(probability * 100)


def risk_level(probability: float) -> str:
    if probability >= 0.75:
        return "高风险"
    if probability >= 0.4:
        return "中风险"
    return "低风险"


def as_number(value: Any, default: float = 0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def feature_label(feature: str | None) -> str:
    labels = {
        "grid4_map_ratio": "四宫格地图查看占比",
        "overall_map_ratio": "总体地图查看占比",
        "grid4_wrong_pickup_rate": "四宫格错误接客率",
        "overall_success_rate": "总体成功率",
        "grid4_path_distance": "四宫格路径距离",
        "grid9_stop_ratio": "九宫格停车比例",
        "drawing_moca_cube_intersection_count": "立方体交叉笔画数",
        "drawing_moca_trail_crossing_count": "连线交叉次数",
        "drawing_moca_trail_duration": "连线任务用时",
    }
    if not feature:
        return ""
    return labels.get(feature, feature)


def static_subjects() -> list[dict[str, Any]] | None:
    payload = load_payload("subjects.json")
    if payload is None:
        return None
    return payload.get("subjects", [])


def build_subject_detail(subject_id: str) -> dict[str, Any]:
    payload_dir = frontend_api_dir()
    if payload_dir is not None:
        path = payload_dir / "subjects" / f"{subject_id}.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Subject not found")
        report = read_json(path)
        prediction = report.get("prediction") or {}
        risk = report.get("risk") or {}
        probability = as_number(
            risk.get("probability", prediction.get("risk_probability")),
            0,
        )
        selected_features = report.get("selected_features") or prediction.get(
            "selected_features", []
        )
        if isinstance(selected_features, str):
            selected_features = [
                item.strip() for item in selected_features.split(",") if item.strip()
            ]
        return {
            "subject_id": subject_id,
            "scale_scores": {
                "MMSE": as_number(prediction.get("MMSE")),
                "MOCA": as_number(prediction.get("MOCA")),
                "CDR_global": as_number(prediction.get("CDR_global")),
                "CDR_SB": as_number(prediction.get("CDR_SB")),
                "HIS": as_number(prediction.get("HIS")),
            },
            "vr_summary": {
                "grid4_success_rate": as_number(prediction.get("grid4_success_rate"), 0),
                "grid9_success_rate": as_number(prediction.get("grid9_success_rate"), 0),
                "grid4_wrong_pickup_rate": as_number(
                    prediction.get("grid4_wrong_pickup_rate"), 0
                ),
                "grid9_wrong_pickup_rate": as_number(
                    prediction.get("grid9_wrong_pickup_rate"), 0
                ),
                "grid4_map_ratio": as_number(prediction.get("grid4_map_ratio"), 0),
                "grid9_map_ratio": as_number(prediction.get("grid9_map_ratio"), 0),
                "grid4_speed_mean": as_number(prediction.get("grid4_speed_mean"), 0),
                "grid9_speed_mean": as_number(prediction.get("grid9_speed_mean"), 0),
                "grid4_path_distance": as_number(
                    prediction.get("grid4_path_distance"), 0
                ),
                "grid9_path_distance": as_number(
                    prediction.get("grid9_path_distance"), 0
                ),
                "grid4_stop_ratio": as_number(prediction.get("grid4_stop_ratio"), 0),
                "grid9_stop_ratio": as_number(prediction.get("grid9_stop_ratio"), 0),
                "grid4_success_time_mean": as_number(
                    prediction.get("grid4_success_time_mean"), 0
                ),
                "grid9_success_time_mean": as_number(
                    prediction.get("grid9_success_time_mean"), 0
                ),
                "grid4_duration": as_number(prediction.get("grid4_duration"), 0),
                "grid9_duration": as_number(prediction.get("grid9_duration"), 0),
            },
            "risk": {
                "probability": probability,
                "score": int(risk.get("score") or prediction.get("risk_score") or risk_score(probability)),
                "level": risk.get("level") or prediction.get("risk_level") or risk_level(probability),
            },
            "explanations": [
                f"{feature_label(item)} 是当前风险解释中的关键特征"
                for item in selected_features[:5]
            ]
            or ["当前静态报告未提供关键特征解释。"],
            "source_report": report,
        }

    subjects = load_mock("subjects.json")
    subject = next((item for item in subjects if item["subject_id"] == subject_id), None)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    detail = load_mock("subject_detail.json")
    detail = {**detail, "subject_id": subject_id}
    detail["scale_scores"] = {
        "MMSE": subject["MMSE"],
        "MOCA": subject["MOCA"],
        "CDR_global": subject["CDR_global"],
        "CDR_SB": subject["CDR_SB"],
        "HIS": subject["HIS"],
    }
    detail["risk"] = {
        "probability": subject["risk_probability"],
        "score": risk_score(subject["risk_probability"]),
        "level": subject["risk_level"],
    }
    return detail


app = FastAPI(
    title="VR Cognitive Assessment API",
    description="基于 VR 行为与笔迹特征的认知风险评估系统演示后端",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "data_source": data_source()}


@app.get("/api/frontend/index")
def frontend_index() -> dict[str, Any]:
    index = load_payload("index.json")
    if index is None:
        return {
            "api_version": "mock-fallback",
            "source": data_source(),
            "files": {},
            "notes": ["No outputs/frontend_api* directory found; serving mock data."],
        }
    return index


@app.get("/api/data/summary")
def data_summary() -> dict[str, Any]:
    run_summary = load_payload("run_summary.json")
    if run_summary:
        return {
            "subject_count": int(run_summary.get("prediction_rows") or 0),
            "matched_count": int(run_summary.get("prediction_rows") or 0),
            "grid4_log_count": 0,
            "grid9_log_count": 0,
            "excluded_log_count": 0,
            "source": data_source(),
        }
    return load_mock("summary.json")


@app.post("/api/data/analyze")
def analyze_data() -> dict[str, Any]:
    summary = data_summary()
    return {
        "status": "completed",
        "message": "已读取当前可用的前端接口产物或 mock fallback。",
        "summary": summary,
    }


@app.get("/api/data/log-manifest")
def log_manifest() -> list[dict[str, Any]]:
    return [
        {"subject_id": "ATH010001", "task_type": "grid4", "log_count": 2, "status": "valid"},
        {"subject_id": "ATH010001", "task_type": "grid9", "log_count": 1, "status": "valid"},
        {"subject_id": "ATH010002", "task_type": "grid4", "log_count": 1, "status": "valid"},
        {"subject_id": "ATH010002", "task_type": "grid9", "log_count": 2, "status": "valid"},
    ]


@app.get("/api/data/features")
def features() -> list[dict[str, Any]]:
    static = static_subjects()
    if static is not None:
        return [
            {
                "subject_id": item["subject_id"],
                "risk_probability": (item.get("risk") or {}).get("probability"),
                "risk_level": (item.get("risk") or {}).get("level"),
            }
            for item in static
        ]
    return [
        {
            "subject_id": item["subject_id"],
            "risk_probability": item["risk_probability"],
            "risk_level": item["risk_level"],
        }
        for item in load_mock("subjects.json")
    ]


@app.get("/api/subjects")
def subjects() -> list[dict[str, Any]]:
    static = static_subjects()
    if static is not None:
        rows = []
        for item in static:
            detail = build_subject_detail(item["subject_id"])
            scale_scores = detail["scale_scores"]
            risk = item.get("risk") or detail["risk"]
            probability = as_number(risk.get("probability"), 0)
            rows.append(
                {
                    "subject_id": item["subject_id"],
                    "MMSE": scale_scores["MMSE"],
                    "MOCA": scale_scores["MOCA"],
                    "CDR_global": scale_scores["CDR_global"],
                    "CDR_SB": scale_scores["CDR_SB"],
                    "HIS": scale_scores["HIS"],
                    "risk_probability": probability,
                    "risk_level": risk.get("level") or risk_level(probability),
                }
            )
        return rows
    return load_mock("subjects.json")


@app.get("/api/subjects/{subject_id}")
def subject_detail(subject_id: str) -> dict[str, Any]:
    return build_subject_detail(subject_id)


@app.get("/api/correlation")
def correlation() -> list[dict[str, Any]]:
    payload = load_payload("correlations.json")
    if payload is not None:
        rows = payload.get("all", [])
        return [
            {
                "target": row.get("target"),
                "feature": row.get("feature"),
                "feature_label": feature_label(row.get("feature")),
                "n": int(as_number(row.get("n"), 0)),
                "pearson_r": as_number(row.get("pearson_r"), 0),
                "spearman_r": as_number(row.get("spearman_r"), 0),
                "p_value": as_number(row.get("p_value"), 1),
                "significant": as_number(row.get("p_value"), 1) < 0.05
                if row.get("p_value") is not None
                else abs(as_number(row.get("spearman_r"), 0)) >= 0.35,
            }
            for row in rows
        ]
    return load_mock("correlation.json")


@app.get("/api/model/metrics")
def model_metrics() -> dict[str, Any]:
    payload = load_payload("models.json")
    if payload is not None:
        registry = payload.get("registry") or {}
        models = registry.get("models") or []
        enabled = next(
            (
                item
                for item in models
                if item.get("type") == "risk" and item.get("enabled_for_user")
            ),
            models[0] if models else {},
        )
        metrics_rows = payload.get("risk_metrics") or []
        metric = next(
            (
                item
                for item in metrics_rows
                if item.get("target") == enabled.get("target")
            ),
            metrics_rows[0] if metrics_rows else {},
        )
        importance_rows = payload.get("feature_importance") or []
        target_importance = [
            item
            for item in importance_rows
            if not enabled.get("target") or item.get("target") == enabled.get("target")
        ]
        selected = enabled.get("selected_features") or [
            item.get("feature") for item in target_importance if item.get("feature")
        ]
        return {
            "model_name": enabled.get("model_name")
            or enabled.get("algorithm")
            or "Logistic Regression",
            "target": enabled.get("target") or metric.get("target") or "MOCA < 26",
            "cv_method": "留一法交叉验证 (Leave-One-Out)",
            "metrics": {
                "auc": as_number(metric.get("auc"), 0),
                "accuracy": as_number(metric.get("accuracy"), 0),
                "sensitivity": as_number(metric.get("sensitivity"), 0),
                "specificity": as_number(metric.get("specificity"), 0),
                "f1": as_number(metric.get("f1"), 0),
                "precision": as_number(metric.get("precision"), 0),
                "cv_mean_auc": as_number(metric.get("auc"), 0),
                "cv_std_auc": 0,
            },
            "selected_features": selected,
            "feature_importance": [
                {
                    "feature": item.get("feature"),
                    "label": feature_label(item.get("feature")),
                    "coefficient": as_number(
                        item.get("coefficient", item.get("importance")), 0
                    ),
                }
                for item in target_importance[:10]
            ],
            "training_date": registry.get("generated_at") or "",
            "sample_size": int(as_number(metric.get("n"), 0)),
            "raw_registry": registry,
        }
    return load_mock("model_metrics.json")


@app.get("/api/reports/{subject_id}")
def report(subject_id: str) -> dict[str, Any]:
    detail = build_subject_detail(subject_id)
    return {
        "subject_id": subject_id,
        "title": f"{subject_id} 认知风险评估报告",
        "risk": detail["risk"],
        "scale_scores": detail["scale_scores"],
        "explanations": detail["explanations"],
    }
