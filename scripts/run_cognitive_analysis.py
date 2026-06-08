from __future__ import annotations

import argparse
import json
from pathlib import Path

from cognitive_algorithm_core import (
    CORRELATION_COLUMNS,
    TWO_FEATURE_COLUMNS,
    TrainingConfig,
    candidate_feature_columns,
    compute_correlations,
    compute_two_feature_analysis,
    load_merged_dataset,
    save_json,
    with_columns,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run correlation and two-feature analysis for merged_dataset.csv."
    )
    parser.add_argument("--input", default="examples/mock_merged_dataset.csv")
    parser.add_argument("--analysis-dir", default="outputs/analysis_results")
    parser.add_argument("--min-n", type=int, default=10)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analysis_dir = Path(args.analysis_dir)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    config = TrainingConfig(min_n=args.min_n, top_k=args.top_k)
    df = load_merged_dataset(args.input)
    feature_cols = candidate_feature_columns(df)

    correlations = with_columns(
        compute_correlations(df, feature_cols, min_n=config.min_n),
        CORRELATION_COLUMNS,
    )
    reliable = (
        correlations[correlations["sample_note"] == "reliable_candidate"].reset_index(
            drop=True
        )
        if not correlations.empty
        else correlations
    )
    two_feature = with_columns(
        compute_two_feature_analysis(
            df, correlations, top_k=config.top_k, min_n=config.min_n
        ),
        TWO_FEATURE_COLUMNS,
    )

    correlations.to_csv(
        analysis_dir / "correlations.csv", index=False, encoding="utf-8-sig"
    )
    reliable.to_csv(
        analysis_dir / "correlations_reliable_n10.csv",
        index=False,
        encoding="utf-8-sig",
    )
    two_feature.to_csv(
        analysis_dir / "two_feature_analysis.csv", index=False, encoding="utf-8-sig"
    )

    summary = {
        "input": str(args.input),
        "analysis_dir": str(analysis_dir),
        "rows": int(len(df)),
        "candidate_feature_count": int(len(feature_cols)),
        "correlation_rows": int(len(correlations)),
        "reliable_correlation_rows": int(len(reliable)),
        "two_feature_rows": int(len(two_feature)),
    }
    save_json(analysis_dir / "analysis_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
