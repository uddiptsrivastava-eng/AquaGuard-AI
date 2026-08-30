"""Evaluate predictions against documented controlled hydrant tests."""

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
from sklearn.metrics import precision_recall_fscore_support


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "data" / "real_validation.json"
EVENTS_PATH = PROJECT_ROOT / "data" / "controlled_leak_events.csv"


def evaluate_predictions(data: pd.DataFrame) -> dict:
    """Compare completed predictions with labels withheld during fitting."""
    truth = data["is_controlled_leak"].astype(bool)
    predicted = data["model_is_anomaly"].astype(bool)
    precision, recall, f1, _ = precision_recall_fscore_support(
        truth, predicted, average="binary", zero_division=0
    )

    events = pd.read_csv(EVENTS_PATH, parse_dates=["start", "end"])
    details = []
    for event in events.itertuples(index=False):
        interval_end = data["timestamp"] + timedelta(hours=1)
        rows = data.loc[(data["timestamp"] < event.end) & (interval_end > event.start)]
        details.append({
            "leak_event_id": event.leak_event_id,
            "start": str(event.start),
            "end": str(event.end),
            "controlled_leak_flow_m3h": float(event.controlled_leak_flow_m3h),
            "hourly_rows": int(len(rows)),
            "isolation_forest_detected": bool(rows["model_is_anomaly"].any()),
            "monitor_or_high_detected": bool(rows["risk_category"].isin(["MONITOR", "HIGH RISK"]).any()),
        })

    report = {
        "title": "Public field-data controlled-test validation",
        "dataset_type": "Real field measurements with controlled hydrant leak tests",
        "total_hourly_observations": int(len(data)),
        "controlled_test_hours": int(truth.sum()),
        "isolation_forest_anomalies": int(predicted.sum()),
        "controlled_test_hours_flagged": int((truth & predicted).sum()),
        "non_test_hours_flagged": int((~truth & predicted).sum()),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "total_controlled_leak_tests": int(len(details)),
        "tests_detected_by_isolation_forest": int(sum(item["isolation_forest_detected"] for item in details)),
        "tests_detected_as_monitor_or_high": int(sum(item["monitor_or_high_detected"] for item in details)),
        "total_high_risk_hours": int((data["risk_category"] == "HIGH RISK").sum()),
        "event_details": details,
        "warning": (
            "These results describe one public experimental DMA and controlled hydrant tests. "
            "They are not city-wide or production leak-detection accuracy."
        ),
    }
    return report


def save_report(report: dict, path: Path = REPORT_PATH) -> None:
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
