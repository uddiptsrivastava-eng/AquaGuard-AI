"""Run the complete AquaGuard AI Stage 2 processing pipeline."""

import hashlib
import json
from pathlib import Path

from anomaly_detection import MODEL_FEATURES, detect_anomalies
from evaluation import evaluate_predictions, save_report
from explanations import add_explanations
from feature_engineering import RAW_DATA_PATH, build_features
from risk_scoring import add_risk_scores


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed_water_network.csv"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pipeline() -> dict:
    """Create features, predictions, scores, explanations, and validation."""
    raw_hash_before = _file_hash(RAW_DATA_PATH)
    data = build_features()
    data, _ = detect_anomalies(data)
    data = add_risk_scores(data)
    data = add_explanations(data)

    if _file_hash(RAW_DATA_PATH) != raw_hash_before:
        raise RuntimeError("The original dataset changed during processing")
    if not data["risk_score"].between(0, 100).all():
        raise RuntimeError("A risk score fell outside 0–100")
    if data["risk_category"].isna().any() or data["explanation"].isna().any():
        raise RuntimeError("A row is missing a category or explanation")

    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.sort_values(["timestamp", "zone_id"]).to_csv(
        PROCESSED_DATA_PATH, index=False, date_format="%Y-%m-%d %H:%M:%S"
    )
    report = evaluate_predictions(data)
    report["model_features"] = MODEL_FEATURES
    report["raw_data_sha256"] = raw_hash_before
    save_report(report)
    return report


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2))
