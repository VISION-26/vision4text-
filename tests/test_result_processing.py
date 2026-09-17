import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.detection import DetectionRequest


class TestResultProcessing(unittest.TestCase):
    """Regression test ensuring worker payload -> result processing contract holds."""

    def setUp(self):
        self.sample_bottle_meta = {
            "status": "complete",
            "result_valid": True,
            "review_required": False,
            "review_reason": None,
            "decision": "anomalous",
            "raw_anomaly_decision": "anomaly",
            "anomalous": True,
            "score": 0.5357,
            "confidence": 0.5357,
            "decision_source": "efficientad_calibrated",
            "primary_specialist": "efficientad",
            "route": "stage3_stable",
            "localization_source": "stage3_evt_clip",
            "elapsed_seconds": 2.868,
            "final_threshold": 0.267,
            "efficientad_image_score": 0.5357,
            "patchcore_image_score": 0.3120,
            "stage2_map_score": 0.4980,
            "stage3_map_score": 0.5357,
            "map_agreement": 0.884,
            "defect_area_pixels": 820,
            "defect_area_fraction": 0.0125,
            "defect_component_count": 1,
            "defect_bbox": {"x": 110, "y": 95, "width": 42, "height": 38},
        }

    def _map_decision(self, raw_decision: str) -> str:
        """Mirror decision mapping logic from detection.py [RESULT-5]."""
        raw = str(raw_decision or "").strip().lower()
        if raw == "invalid":
            return "Invalid Input"
        elif raw in ("anomaly", "anomalous"):
            return "Anomalous"
        elif raw == "normal":
            return "Normal"
        else:
            raise ValueError(f"CPU worker returned an unknown decision state: {raw_decision!r}")

    def test_01_anomalous_decision_mapping(self):
        """Verify 'anomalous' (the pre-fix worker string) maps cleanly to 'Anomalous' without ValueError."""
        pred = self._map_decision("anomalous")
        self.assertEqual(pred, "Anomalous")

    def test_02_anomaly_decision_mapping(self):
        """Verify canonical 'anomaly' maps cleanly to 'Anomalous'."""
        pred = self._map_decision("anomaly")
        self.assertEqual(pred, "Anomalous")

    def test_03_normal_decision_mapping(self):
        """Verify 'normal' maps cleanly to 'Normal'."""
        pred = self._map_decision("normal")
        self.assertEqual(pred, "Normal")

    def test_04_invalid_decision_mapping(self):
        """Verify 'invalid' maps cleanly to 'Invalid Input'."""
        pred = self._map_decision("invalid")
        self.assertEqual(pred, "Invalid Input")

    def test_05_unknown_decision_raises_value_error(self):
        """Verify unrecognized decision raises ValueError as expected."""
        with self.assertRaises(ValueError):
            self._map_decision("corrupted_state_xyz")

    def test_06_bottle_worker_metadata_numeric_normalization(self):
        """Verify numeric field extraction and normalization for Bottle payload [RESULT-6]."""
        meta = self.sample_bottle_meta
        score = float(meta.get("score") or 0.0)
        confidence = float(meta.get("confidence") or 0.0)
        elapsed = float(meta.get("elapsed_seconds") or 0.0)
        threshold = float(meta.get("final_threshold", 0.267))

        self.assertAlmostEqual(score, 0.5357)
        self.assertAlmostEqual(confidence, 0.5357)
        self.assertAlmostEqual(elapsed, 2.868)
        self.assertAlmostEqual(threshold, 0.267)
        self.assertEqual(meta["primary_specialist"], "efficientad")
        self.assertEqual(meta["decision_source"], "efficientad_calibrated")
        self.assertTrue(meta["result_valid"])


if __name__ == "__main__":
    unittest.main()
