"""Basic safety and output checks for the Stage 2 pipeline."""

import hashlib
import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from anomaly_detection import MODEL_FEATURES  # noqa: E402
from feature_engineering import GROUND_TRUTH_COLUMNS, RAW_DATA_PATH, build_features  # noqa: E402
from run_pipeline import PROCESSED_DATA_PATH, run_pipeline  # noqa: E402


class PipelineChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_hash_before = hashlib.sha256(RAW_DATA_PATH.read_bytes()).hexdigest()
        cls.report = run_pipeline()
        cls.raw_hash_after = hashlib.sha256(RAW_DATA_PATH.read_bytes()).hexdigest()
        cls.processed = pd.read_csv(PROCESSED_DATA_PATH)

    def test_ground_truth_is_not_a_model_feature(self) -> None:
        self.assertTrue(set(MODEL_FEATURES).isdisjoint(GROUND_TRUTH_COLUMNS))

    def test_timestamps_are_valid(self) -> None:
        parsed = pd.to_datetime(self.processed["timestamp"], errors="coerce")
        self.assertFalse(parsed.isna().any())

    def test_model_features_have_no_missing_values(self) -> None:
        features = build_features()
        self.assertFalse(features[MODEL_FEATURES].isna().any().any())

    def test_risk_scores_and_categories_are_complete(self) -> None:
        self.assertTrue(self.processed["risk_score"].between(0, 100).all())
        self.assertFalse(self.processed["risk_category"].isna().any())
        self.assertTrue(
            set(self.processed["risk_category"]).issubset({"NORMAL", "MONITOR", "HIGH RISK"})
        )

    def test_original_dataset_is_unchanged(self) -> None:
        self.assertEqual(self.raw_hash_before, self.raw_hash_after)

    def test_every_row_has_an_explanation(self) -> None:
        self.assertFalse(self.processed["explanation"].isna().any())

    def test_real_dataset_shape_and_source_labels(self) -> None:
        self.assertEqual(len(self.processed), 719)
        self.assertEqual(self.processed["zone_id"].nunique(), 1)
        self.assertEqual(int(self.processed["is_controlled_leak"].sum()), 14)
        self.assertEqual(self.report["total_controlled_leak_tests"], 21)


if __name__ == "__main__":
    unittest.main()
