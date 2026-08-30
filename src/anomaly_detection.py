"""Unsupervised anomaly detection for AquaGuard AI."""

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from feature_engineering import GROUND_TRUTH_COLUMNS


# This is the complete and explicit model input list. Ground-truth labels are
# deliberately absent: they are revealed only after predictions for evaluation.
MODEL_FEATURES = [
    "flow_volume_m3",
    "outflow_volume_m3",
    "consumption_m3",
    "pressure_m_head",
    "unaccounted_water_pct",
    "flow_deviation_pct",
    "consumption_deviation_pct",
    "pressure_deviation_pct",
    "hour_sin",
    "hour_cos",
]

ISOLATION_FOREST_PARAMETERS = {
    "n_estimators": 200,
    "contamination": 0.02,
    "random_state": 42,
    "n_jobs": -1,
}


def detect_anomalies(data: pd.DataFrame) -> tuple[pd.DataFrame, Pipeline]:
    """Fit Isolation Forest and return its continuous and binary signals.

    ``model_anomaly_score`` is the negative decision function, so larger values
    mean more abnormal behaviour. ``model_is_anomaly`` is the model's binary
    decision and does not use the hidden synthetic labels.
    """
    overlap = set(MODEL_FEATURES).intersection(GROUND_TRUTH_COLUMNS)
    if overlap:
        raise AssertionError(f"Ground truth leaked into model features: {overlap}")
    features = data[MODEL_FEATURES]
    if features.isna().any().any():
        raise ValueError("Model features contain unexpected missing values")

    model = Pipeline(
        [
            ("standardize", StandardScaler()),
            ("isolation_forest", IsolationForest(**ISOLATION_FOREST_PARAMETERS)),
        ]
    )
    model.fit(features)
    result = data.copy()
    result["model_anomaly_score"] = -model.decision_function(features)
    result["model_is_anomaly"] = model.predict(features) == -1
    return result, model
