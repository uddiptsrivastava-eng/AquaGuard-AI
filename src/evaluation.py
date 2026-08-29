"""Synthetic prototype validation, performed only after predictions exist."""

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import precision_recall_fscore_support


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "data" / "synthetic_validation.json"


def evaluate_predictions(data: pd.DataFrame) -> dict:
    """Compare completed predictions with labels hidden during model fitting."""
    truth = data["is_synthetic_anomaly"].astype(bool)
    predicted = data["model_is_anomaly"].astype(bool)
    precision, recall, f1, _ = precision_recall_fscore_support(
        truth, predicted, average="binary", zero_division=0
    )

    # Each non-normal anomaly_type/zone pair represents one documented event in
    # this synthetic dataset. Evaluation labels are read only at this late stage.
    anomaly_rows = data.loc[truth]
    event_detection = anomaly_rows.groupby(["zone_id", "anomaly_type"], sort=True).agg(
        start=("timestamp", "min"),
        end=("timestamp", "max"),
        readings=("timestamp", "size"),
        isolation_forest_detected=("model_is_anomaly", "any"),
        monitor_or_high_detected=("risk_category", lambda s: s.isin(["MONITOR", "HIGH RISK"]).any()),
    ).reset_index()

    report = {
        "title": "Synthetic prototype validation results",
        "known_anomalous_readings": int(truth.sum()),
        "isolation_forest_anomalies": int(predicted.sum()),
        "known_anomalous_readings_flagged_by_isolation_forest": int((truth & predicted).sum()),
        "known_anomalous_readings_monitor_or_high_risk": int(
            (truth & data["risk_category"].isin(["MONITOR", "HIGH RISK"])).sum()
        ),
        "known_anomalous_readings_high_risk": int(
            (truth & (data["risk_category"] == "HIGH RISK")).sum()
        ),
        "normal_readings_incorrectly_flagged_by_isolation_forest": int((~truth & predicted).sum()),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "total_anomaly_events": int(len(event_detection)),
        "events_detected_by_isolation_forest": int(event_detection["isolation_forest_detected"].sum()),
        "events_detected_as_monitor_or_high": int(event_detection["monitor_or_high_detected"].sum()),
        "total_high_risk_readings": int((data["risk_category"] == "HIGH RISK").sum()),
        "event_details": event_detection.assign(
            start=lambda x: x["start"].astype(str), end=lambda x: x["end"].astype(str)
        ).to_dict(orient="records"),
        "warning": "These results measure performance on synthetic patterns only; they are not real-world accuracy.",
    }
    return report


def save_report(report: dict, path: Path = REPORT_PATH) -> None:
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
