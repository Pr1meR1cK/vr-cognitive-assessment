from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build static JSON payloads for frontend integration from B result files."
    )
    parser.add_argument(
        "--results-dir",
        default="outputs/cognitive_pipeline_interim_drawing_quality/results",
    )
    parser.add_argument("--output-dir", default="outputs/frontend_api")
    parser.add_argument("--top-n", type=int, default=20)
    return parser.parse_args()


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def records_from_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    df = pd.read_csv(path)
    return [
        {key: clean_value(value) for key, value in row.items()}
        for row in df.to_dict(orient="records")
    ]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_correlation_payload(results_dir: Path, top_n: int) -> dict[str, Any]:
    rows = records_from_csv(results_dir / "correlations_reliable_n10.csv")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        target = str(row.get("target"))
        grouped.setdefault(target, []).append(row)
    top_by_target = {
        target: sorted(
            items,
            key=lambda item: abs(float(item.get("spearman_r") or 0)),
            reverse=True,
        )[:top_n]
        for target, items in grouped.items()
    }
    return {
        "summary": {
            "row_count": len(rows),
            "targets": sorted(grouped),
            "top_n": top_n,
        },
        "top_by_target": top_by_target,
        "all": rows,
    }


def build_model_payload(results_dir: Path) -> dict[str, Any]:
    registry = read_json(results_dir / "model_registry.json")
    return {
        "registry": registry,
        "risk_metrics": records_from_csv(results_dir / "model_metrics.csv"),
        "score_metrics": records_from_csv(results_dir / "score_model_metrics.csv"),
        "feature_importance": records_from_csv(results_dir / "feature_importance.csv"),
    }


def build_subject_payloads(results_dir: Path, output_dir: Path) -> list[dict[str, Any]]:
    prediction_rows = records_from_csv(results_dir / "model_predictions.csv")
    prediction_by_subject = {
        str(row.get("subject_id")): row for row in prediction_rows if row.get("subject_id")
    }
    subjects: list[dict[str, Any]] = []
    risk_dir = results_dir / "subject_risk"
    for subject_id, prediction in sorted(prediction_by_subject.items()):
        risk_payload = read_json(risk_dir / f"{subject_id}.json")
        report = {
            "subject_id": subject_id,
            "risk": risk_payload.get("risk"),
            "risks": risk_payload.get("risks", []),
            "prediction": prediction,
            "model_basis": risk_payload.get("model_basis"),
            "selected_features": risk_payload.get("selected_features", []),
        }
        write_json(output_dir / "subjects" / f"{subject_id}.json", report)
        subjects.append(
            {
                "subject_id": subject_id,
                "risk": report["risk"],
                "detail_url": f"subjects/{subject_id}.json",
            }
        )
    return subjects


def main() -> None:
    args = parse_args()
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    correlations = build_correlation_payload(results_dir, args.top_n)
    models = build_model_payload(results_dir)
    two_feature = records_from_csv(results_dir / "two_feature_analysis.csv")
    subjects = build_subject_payloads(results_dir, output_dir)
    run_summary = read_json(results_dir / "run_summary.json")

    write_json(output_dir / "correlations.json", correlations)
    write_json(output_dir / "models.json", models)
    write_json(
        output_dir / "two_feature_analysis.json",
        {
            "summary": {"row_count": len(two_feature)},
            "top": two_feature[: args.top_n],
            "all": two_feature,
        },
    )
    write_json(output_dir / "subjects.json", {"subjects": subjects})
    write_json(output_dir / "run_summary.json", run_summary)

    index = {
        "api_version": "static-v1",
        "source_results_dir": str(results_dir),
        "files": {
            "correlations": "correlations.json",
            "models": "models.json",
            "two_feature_analysis": "two_feature_analysis.json",
            "subjects": "subjects.json",
            "run_summary": "run_summary.json",
        },
        "subject_detail_pattern": "subjects/{subject_id}.json",
        "notes": [
            "These JSON files are the frontend contract for C.",
            "They can later be served by FastAPI without changing the response shape.",
        ],
    }
    write_json(output_dir / "index.json", index)
    print(json.dumps({"output_dir": str(output_dir), "subjects": len(subjects)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
