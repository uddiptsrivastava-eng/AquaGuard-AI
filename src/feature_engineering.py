"""Feature engineering for AquaGuard AI.

All historical baselines use only observations that occurred earlier in time.
Synthetic ground-truth columns remain in the returned table for later evaluation,
but this module never uses them to calculate model features.
"""

from pathlib import Path

import numpy as np
import pandas as pd


RAW_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "water_network.csv"
GROUND_TRUTH_COLUMNS = ["is_synthetic_anomaly", "anomaly_type"]


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load and validate the original synthetic readings."""
    data = pd.read_csv(path)
    required = {
        "timestamp", "zone_id", "flow_m3_per_hour", "pressure_m_head",
        "consumption_m3", *GROUND_TRUTH_COLUMNS,
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Raw data is missing columns: {sorted(missing)}")
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="raise")
    return data.sort_values(["zone_id", "timestamp"], ignore_index=True)


def _past_only_baseline(data: pd.DataFrame, value_column: str) -> pd.Series:
    """Estimate expected values without allowing future readings into the past.

    First preference is the expanding average of earlier readings for the same
    zone and quarter-hour of day. Until that exists, the expanding average of
    all earlier zone readings is used. A zone's first reading has no history, so
    it is bootstrapped to its current value and receives zero baseline deviation.
    """
    same_slot_history = data.groupby(
        ["zone_id", "time_slot"], sort=False
    )[value_column].transform(lambda values: values.shift(1).expanding().mean())
    zone_history = data.groupby("zone_id", sort=False)[value_column].transform(
        lambda values: values.shift(1).expanding().mean()
    )
    return same_slot_history.fillna(zone_history).fillna(data[value_column])


def _safe_deviation_pct(actual: pd.Series, expected: pd.Series) -> pd.Series:
    """Calculate percentage deviation, returning zero for a zero baseline."""
    return np.divide(
        actual - expected,
        expected,
        out=np.zeros(len(actual), dtype=float),
        where=expected.to_numpy() != 0,
    ) * 100.0


def engineer_features(data: pd.DataFrame) -> pd.DataFrame:
    """Add water-balance, time, and past-only historical features."""
    result = data.copy().sort_values(["zone_id", "timestamp"], ignore_index=True)
    if not pd.api.types.is_datetime64_any_dtype(result["timestamp"]):
        result["timestamp"] = pd.to_datetime(result["timestamp"], errors="raise")

    # Flow is an hourly rate; multiplying by 0.25 makes it comparable with the
    # consumption volume measured during each 15-minute interval.
    result["flow_volume_m3"] = result["flow_m3_per_hour"] * 0.25
    result["unaccounted_water_m3"] = result["flow_volume_m3"] - result["consumption_m3"]
    result["unaccounted_water_pct"] = np.divide(
        result["unaccounted_water_m3"],
        result["flow_volume_m3"],
        out=np.zeros(len(result), dtype=float),
        where=result["flow_volume_m3"].to_numpy() != 0,
    ) * 100.0

    result["hour"] = result["timestamp"].dt.hour
    result["day_of_week"] = result["timestamp"].dt.dayofweek
    result["is_weekend"] = (result["day_of_week"] >= 5).astype(int)
    decimal_hour = result["hour"] + result["timestamp"].dt.minute / 60.0
    result["hour_sin"] = np.sin(2 * np.pi * decimal_hour / 24.0)
    result["hour_cos"] = np.cos(2 * np.pi * decimal_hour / 24.0)
    result["time_slot"] = result["timestamp"].dt.hour * 4 + result["timestamp"].dt.minute // 15

    baseline_pairs = {
        "expected_flow": "flow_volume_m3",
        "expected_consumption": "consumption_m3",
        "expected_pressure": "pressure_m_head",
    }
    for expected_column, actual_column in baseline_pairs.items():
        result[expected_column] = _past_only_baseline(result, actual_column)

    result["flow_deviation_pct"] = _safe_deviation_pct(result["flow_volume_m3"], result["expected_flow"])
    result["consumption_deviation_pct"] = _safe_deviation_pct(
        result["consumption_m3"], result["expected_consumption"]
    )
    result["pressure_deviation_pct"] = _safe_deviation_pct(
        result["pressure_m_head"], result["expected_pressure"]
    )
    return result.drop(columns="time_slot")


def build_features(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Convenience function used by the complete pipeline."""
    return engineer_features(load_raw_data(path))
