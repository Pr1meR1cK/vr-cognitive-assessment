from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a mock full merged_dataset.csv by adding synthetic VR features to the interim dataset."
    )
    parser.add_argument("--input", default="outputs/interim_merged_dataset.csv")
    parser.add_argument("--output", default="outputs/mock_full_merged_dataset.csv")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def clip(value: float, low: float, high: float) -> float:
    return float(np.clip(value, low, high))


def add_vr_features(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    out = df.copy()

    moca = pd.to_numeric(out["MOCA"], errors="coerce").fillna(out["MOCA"].median())
    mmse = pd.to_numeric(out["MMSE"], errors="coerce").fillna(out["MMSE"].median())
    cognitive = ((moca / 30.0) * 0.65 + (mmse / 30.0) * 0.35).clip(0, 1)
    impairment = (1.0 - cognitive).clip(0, 1)

    grid4_success = []
    grid9_success = []
    grid4_wrong = []
    grid9_wrong = []
    grid4_map = []
    grid9_map = []
    grid4_stop = []
    grid9_stop = []
    grid4_path = []
    grid9_path = []
    grid4_duration = []
    grid9_duration = []
    grid4_speed_std = []
    grid9_speed_std = []

    for imp in impairment.to_numpy(dtype=float):
        noise = lambda scale: float(rng.normal(0, scale))
        g4_success = clip(0.96 - 0.34 * imp + noise(0.04), 0.25, 1.0)
        g9_success = clip(g4_success - 0.10 - 0.26 * imp + noise(0.05), 0.05, 1.0)
        g4_wrong_rate = clip(0.02 + 0.22 * imp + noise(0.025), 0.0, 0.75)
        g9_wrong_rate = clip(g4_wrong_rate + 0.04 + 0.22 * imp + noise(0.04), 0.0, 0.9)
        g4_map_ratio = clip(0.06 + 0.30 * imp + noise(0.035), 0.0, 0.85)
        g9_map_ratio = clip(g4_map_ratio + 0.04 + 0.23 * imp + noise(0.04), 0.0, 0.95)
        g4_stop_ratio = clip(0.08 + 0.25 * imp + noise(0.035), 0.0, 0.85)
        g9_stop_ratio = clip(g4_stop_ratio + 0.06 + 0.28 * imp + noise(0.04), 0.0, 0.95)
        g4_distance = clip(360 + 470 * imp + noise(35), 220, 1050)
        g9_distance = clip(g4_distance + 210 + 620 * imp + noise(60), 420, 1800)
        g4_time = clip(150 + 290 * imp + noise(25), 80, 720)
        g9_time = clip(g4_time + 120 + 420 * imp + noise(35), 180, 1200)
        g4_speed = clip(0.24 + 0.55 * imp + noise(0.05), 0.05, 1.6)
        g9_speed = clip(g4_speed + 0.08 + 0.36 * imp + noise(0.06), 0.05, 2.1)

        grid4_success.append(g4_success)
        grid9_success.append(g9_success)
        grid4_wrong.append(g4_wrong_rate)
        grid9_wrong.append(g9_wrong_rate)
        grid4_map.append(g4_map_ratio)
        grid9_map.append(g9_map_ratio)
        grid4_stop.append(g4_stop_ratio)
        grid9_stop.append(g9_stop_ratio)
        grid4_path.append(g4_distance)
        grid9_path.append(g9_distance)
        grid4_duration.append(g4_time)
        grid9_duration.append(g9_time)
        grid4_speed_std.append(g4_speed)
        grid9_speed_std.append(g9_speed)

    out["grid4_success_rate"] = grid4_success
    out["grid9_success_rate"] = grid9_success
    out["overall_success_rate"] = (out["grid4_success_rate"] + out["grid9_success_rate"]) / 2
    out["diff_success_rate"] = out["grid9_success_rate"] - out["grid4_success_rate"]

    out["grid4_wrong_pickup_rate"] = grid4_wrong
    out["grid9_wrong_pickup_rate"] = grid9_wrong
    out["overall_wrong_pickup_rate"] = (
        out["grid4_wrong_pickup_rate"] + out["grid9_wrong_pickup_rate"]
    ) / 2
    out["diff_wrong_pickup_rate"] = (
        out["grid9_wrong_pickup_rate"] - out["grid4_wrong_pickup_rate"]
    )

    out["grid4_map_ratio"] = grid4_map
    out["grid9_map_ratio"] = grid9_map
    out["overall_map_ratio"] = (out["grid4_map_ratio"] + out["grid9_map_ratio"]) / 2
    out["diff_map_ratio"] = out["grid9_map_ratio"] - out["grid4_map_ratio"]

    out["grid4_stop_ratio"] = grid4_stop
    out["grid9_stop_ratio"] = grid9_stop
    out["overall_stop_ratio"] = (out["grid4_stop_ratio"] + out["grid9_stop_ratio"]) / 2
    out["diff_stop_ratio"] = out["grid9_stop_ratio"] - out["grid4_stop_ratio"]

    out["grid4_path_distance"] = grid4_path
    out["grid9_path_distance"] = grid9_path
    out["overall_path_distance"] = (
        out["grid4_path_distance"] + out["grid9_path_distance"]
    ) / 2
    out["diff_path_distance"] = out["grid9_path_distance"] - out["grid4_path_distance"]

    out["grid4_duration"] = grid4_duration
    out["grid9_duration"] = grid9_duration
    out["overall_duration"] = (out["grid4_duration"] + out["grid9_duration"]) / 2
    out["grid4_episode_duration_mean"] = out["grid4_duration"] / 10
    out["grid9_episode_duration_mean"] = out["grid9_duration"] / 10
    out["grid4_episode_duration_std"] = out["grid4_episode_duration_mean"] * (
        0.12 + impairment * 0.28
    )
    out["grid9_episode_duration_std"] = out["grid9_episode_duration_mean"] * (
        0.16 + impairment * 0.34
    )
    out["grid4_success_time_mean"] = out["grid4_episode_duration_mean"] * (
        0.72 + impairment * 0.12
    )
    out["grid9_success_time_mean"] = out["grid9_episode_duration_mean"] * (
        0.78 + impairment * 0.14
    )
    out["grid4_fail_time_mean"] = out["grid4_episode_duration_mean"] * (
        1.10 + impairment * 0.20
    )
    out["grid9_fail_time_mean"] = out["grid9_episode_duration_mean"] * (
        1.18 + impairment * 0.24
    )

    out["grid4_speed_std"] = grid4_speed_std
    out["grid9_speed_std"] = grid9_speed_std
    out["overall_speed_std"] = (out["grid4_speed_std"] + out["grid9_speed_std"]) / 2
    out["grid4_speed_mean"] = (out["grid4_path_distance"] / out["grid4_duration"]).clip(
        0.1, 8.0
    )
    out["grid9_speed_mean"] = (out["grid9_path_distance"] / out["grid9_duration"]).clip(
        0.1, 8.0
    )
    out["overall_speed_mean"] = (out["grid4_speed_mean"] + out["grid9_speed_mean"]) / 2
    out["grid4_speed_max"] = out["grid4_speed_mean"] + out["grid4_speed_std"] * 2.2
    out["grid9_speed_max"] = out["grid9_speed_mean"] + out["grid9_speed_std"] * 2.4
    out["grid4_stationary_ratio"] = (out["grid4_stop_ratio"] * 0.72).clip(0, 0.95)
    out["grid9_stationary_ratio"] = (out["grid9_stop_ratio"] * 0.78).clip(0, 0.95)
    out["overall_stationary_ratio"] = (
        out["grid4_stationary_ratio"] + out["grid9_stationary_ratio"]
    ) / 2
    out["grid4_throttle_mean"] = (0.52 - impairment * 0.20).clip(0.05, 0.85)
    out["grid9_throttle_mean"] = (0.48 - impairment * 0.24).clip(0.04, 0.82)
    out["grid4_abs_steer_mean"] = (0.18 + impairment * 0.36).clip(0.04, 0.95)
    out["grid9_abs_steer_mean"] = (0.24 + impairment * 0.42).clip(0.05, 1.0)
    out["grid4_abs_steer_std"] = (out["grid4_abs_steer_mean"] * 0.45).clip(0.01, 0.7)
    out["grid9_abs_steer_std"] = (out["grid9_abs_steer_mean"] * 0.52).clip(0.01, 0.8)

    out["grid4_count_ep_success"] = np.round(out["grid4_success_rate"] * 10).astype(int)
    out["grid9_count_ep_success"] = np.round(out["grid9_success_rate"] * 10).astype(int)
    out["grid4_count_ep_fail"] = 10 - out["grid4_count_ep_success"]
    out["grid9_count_ep_fail"] = 10 - out["grid9_count_ep_success"]
    out["grid4_count_ep_timeout"] = np.round(out["grid4_stop_ratio"] * 3).astype(int)
    out["grid9_count_ep_timeout"] = np.round(out["grid9_stop_ratio"] * 4).astype(int)
    out["grid4_count_pickup_ok"] = np.round(out["grid4_success_rate"] * 20).astype(int)
    out["grid9_count_pickup_ok"] = np.round(out["grid9_success_rate"] * 20).astype(int)
    out["grid4_count_pickup_wrong"] = np.round(out["grid4_wrong_pickup_rate"] * 20).astype(int)
    out["grid9_count_pickup_wrong"] = np.round(out["grid9_wrong_pickup_rate"] * 20).astype(int)
    out["grid4_count_map_on"] = np.round(out["grid4_map_ratio"] * 12).astype(int)
    out["grid9_count_map_on"] = np.round(out["grid9_map_ratio"] * 16).astype(int)
    out["grid4_map_view_duration"] = out["grid4_duration"] * out["grid4_map_ratio"]
    out["grid9_map_view_duration"] = out["grid9_duration"] * out["grid9_map_ratio"]
    out["grid4_map_count_per_min"] = out["grid4_count_map_on"] / (
        out["grid4_duration"] / 60
    )
    out["grid9_map_count_per_min"] = out["grid9_count_map_on"] / (
        out["grid9_duration"] / 60
    )
    out["grid4_count_zone_enter"] = np.round(8 + impairment * 12).astype(int)
    out["grid9_count_zone_enter"] = np.round(14 + impairment * 22).astype(int)
    out["grid4_count_zone_exit"] = out["grid4_count_zone_enter"]
    out["grid9_count_zone_exit"] = out["grid9_count_zone_enter"]
    out["grid4_count_brake_on"] = np.round(4 + impairment * 16).astype(int)
    out["grid9_count_brake_on"] = np.round(7 + impairment * 22).astype(int)
    out["grid4_brake_count_per_min"] = out["grid4_count_brake_on"] / (
        out["grid4_duration"] / 60
    )
    out["grid9_brake_count_per_min"] = out["grid9_count_brake_on"] / (
        out["grid9_duration"] / 60
    )
    out["grid4_count_att_start"] = np.round(1 + impairment * 4).astype(int)
    out["grid9_count_att_start"] = np.round(2 + impairment * 6).astype(int)
    out["grid4_count_att_reset"] = np.round(impairment * 3).astype(int)
    out["grid9_count_att_reset"] = np.round(impairment * 5).astype(int)
    out["grid4_count_stop_start"] = np.round(out["grid4_stop_ratio"] * 8).astype(int)
    out["grid9_count_stop_start"] = np.round(out["grid9_stop_ratio"] * 10).astype(int)
    out["grid4_stop_duration"] = out["grid4_duration"] * out["grid4_stop_ratio"]
    out["grid9_stop_duration"] = out["grid9_duration"] * out["grid9_stop_ratio"]

    return out


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    out = add_vr_features(df, args.seed)
    out.to_csv(output, index=False, encoding="utf-8-sig")

    summary = {
        "input": args.input,
        "output": str(output),
        "rows": int(len(out)),
        "columns": int(len(out.columns)),
        "vr_feature_count": int(
            sum(
                col.startswith(("grid4_", "grid9_", "overall_", "diff_"))
                for col in out.columns
            )
        ),
        "note": "Synthetic VR features are for demo/testing only. Replace with A's real VR features later.",
    }
    (output.parent / "mock_full_merged_dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
