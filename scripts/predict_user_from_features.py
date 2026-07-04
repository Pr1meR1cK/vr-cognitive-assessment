from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cognitive_algorithm_core import (
    load_json,
    predict_user_from_registry,
    render_user_report_html,
    save_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict user cognitive report from one subject's extracted VR features."
    )
    parser.add_argument(
        "--features",
        required=True,
        help="Path to a JSON file with subject_id and features extracted from VR logs.",
    )
    parser.add_argument("--model-dir", default="outputs/trained_models")
    parser.add_argument("--output-dir", default="outputs/user_prediction")
    return parser.parse_args()


def normalize_feature_payload(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    subject_id = str(payload.get("subject_id") or payload.get("id") or "unknown_subject")
    features = payload.get("features")
    if isinstance(features, dict):
        return subject_id, features

    excluded = {"subject_id", "id", "features"}
    flat_features = {k: v for k, v in payload.items() if k not in excluded}
    return subject_id, flat_features


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = load_json(args.features)
    subject_id, features = normalize_feature_payload(payload)
    report = predict_user_from_registry(subject_id, features, args.model_dir)

    save_json(output_dir / "user_prediction.json", report)
    (output_dir / "user_report.html").write_text(
        render_user_report_html(report), encoding="utf-8"
    )

    summary = {
        "subject_id": subject_id,
        "input_features": str(args.features),
        "model_dir": str(args.model_dir),
        "output_dir": str(output_dir),
        "prediction_count": len(report.get("predictions", [])),
        "missing_model_features": report.get("data_quality", {}).get(
            "missing_model_features", []
        ),
    }
    save_json(output_dir / "prediction_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
