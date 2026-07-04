from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


SCALE_COLUMNS = ["subject_id", "MMSE", "MOCA", "CDR_global", "CDR_SB", "HIS"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an interim merged_dataset.csv from available scale Excel files and drawing features."
    )
    parser.add_argument("--scale-dir", default="MMSE_MoCA")
    parser.add_argument("--drawing", default="A_data/output3/drawing_features.csv")
    parser.add_argument("--output", default="outputs/interim_merged_dataset.csv")
    return parser.parse_args()


def normalize_subject_id(value: Any) -> str:
    text = "" if value is None else str(value)
    digits = re.findall(r"\d+", text)
    if not digits:
        return text.strip()
    return f"ATH{digits[-1][-6:].zfill(6)}"


def parse_cdr(value: Any) -> tuple[float | None, float | None]:
    if value is None or pd.isna(value):
        return None, None
    text = str(value)
    global_match = re.search(r"global-?([0-9.]+)", text, flags=re.IGNORECASE)
    sb_match = re.search(r"SB-?([0-9.]+)", text, flags=re.IGNORECASE)
    cdr_global = float(global_match.group(1)) if global_match else None
    cdr_sb = float(sb_match.group(1)) if sb_match else None
    return cdr_global, cdr_sb


def read_scale_totals(scale_dir: str | Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in sorted(Path(scale_dir).glob("*.xlsx")):
        if path.name.startswith("~$"):
            continue
        subject_id = normalize_subject_id(path.name)
        try:
            totals = pd.read_excel(path, sheet_name=2, header=1)
        except Exception as exc:
            rows.append({"subject_id": subject_id, "read_error": str(exc)})
            continue

        row: dict[str, Any] = {"subject_id": subject_id}
        for _, item in totals.iterrows():
            scale = str(item.iloc[0]).strip()
            value = item.iloc[1]
            if scale == "MMSE":
                row["MMSE"] = value
            elif scale == "MOCA":
                row["MOCA"] = value
            elif scale == "HIS":
                row["HIS"] = value
            elif scale == "CDR":
                row["CDR_global"], row["CDR_SB"] = parse_cdr(value)
        rows.append(row)
    out = pd.DataFrame(rows)
    for col in SCALE_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    return out[SCALE_COLUMNS]


def read_drawing_features(path: str | Path) -> pd.DataFrame:
    drawing = pd.read_csv(path)
    drawing["subject_id"] = drawing["subject_id"].map(normalize_subject_id)
    return drawing


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    scales = read_scale_totals(args.scale_dir)
    drawing = read_drawing_features(args.drawing)
    merged = scales.merge(drawing, on="subject_id", how="left")
    for col in SCALE_COLUMNS[1:]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    merged.to_csv(output, index=False, encoding="utf-8-sig")
    summary = {
        "scale_rows": int(len(scales)),
        "drawing_rows": int(len(drawing)),
        "merged_rows": int(len(merged)),
        "merged_columns": int(len(merged.columns)),
        "matched_drawing_rows": int(merged.filter(like="drawing_").notna().any(axis=1).sum()),
        "output": str(output),
        "note": "Interim dataset includes scale totals and drawing_* features only. VR grid features are still pending.",
    }
    (output.parent / "interim_merged_dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
