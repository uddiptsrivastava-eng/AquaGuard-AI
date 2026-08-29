"""Transparent prototype risk prioritization for AquaGuard AI."""

import numpy as np
import pandas as pd


RISK_WEIGHTS = {
    "model_anomaly_strength": 35,
    "positive_unaccounted_water": 20,
    "low_pressure_deviation": 15,
    "flow_deviation": 10,
    "consumption_deviation": 10,
    "persistence": 10,
}


def add_risk_scores(data: pd.DataFrame) -> pd.DataFrame:
    """Add an interpretable 0–100 score and past-only persistence.

    This is a prototype prioritization score, not a calibrated probability of
    leakage. Its weights and thresholds are design choices for the prototype,
    not universal water-industry standards.
    """
    result = data.copy().sort_values(["zone_id", "timestamp"], ignore_index=True)

    # Percentile rank maps the unsupervised score onto a stable 0–1 strength.
    model_strength = result["model_anomaly_score"].rank(pct=True).clip(0, 1)
    water_signal = ((result["unaccounted_water_pct"] - 15.0) / 35.0).clip(0, 1)
    pressure_signal = (-result["pressure_deviation_pct"] / 30.0).clip(0, 1)
    flow_signal = (result["flow_deviation_pct"].abs() / 75.0).clip(0, 1)
    consumption_signal = (result["consumption_deviation_pct"].abs() / 75.0).clip(0, 1)

    # An elevated indicator is based only on the current calculated signals.
    # The rolling sum uses the current and seven preceding readings—never future
    # observations. A single elevated reading therefore earns only 1/8 persistence.
    elevated = (
        result["model_is_anomaly"]
        | (water_signal >= 0.5)
        | (pressure_signal >= 0.5)
        | (flow_signal >= 0.7)
        | (consumption_signal >= 0.7)
    ).astype(int)
    result["persistence_count_8"] = elevated.groupby(result["zone_id"]).transform(
        lambda values: values.rolling(window=8, min_periods=1).sum()
    ).astype(int)
    persistence_signal = result["persistence_count_8"] / 8.0

    result["risk_score"] = (
        RISK_WEIGHTS["model_anomaly_strength"] * model_strength
        + RISK_WEIGHTS["positive_unaccounted_water"] * water_signal
        + RISK_WEIGHTS["low_pressure_deviation"] * pressure_signal
        + RISK_WEIGHTS["flow_deviation"] * flow_signal
        + RISK_WEIGHTS["consumption_deviation"] * consumption_signal
        + RISK_WEIGHTS["persistence"] * persistence_signal
    ).clip(0, 100).round(1)

    result["risk_category"] = pd.cut(
        result["risk_score"],
        bins=[-np.inf, 40, 70, np.inf],
        labels=["NORMAL", "MONITOR", "HIGH RISK"],
        right=False,
    ).astype(str)
    return result
