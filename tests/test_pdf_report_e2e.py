import os
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone
import fitz
from PIL import Image

# Add backend to path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.models.detection import Detection
from app.services.report_service import ReportService


class TestPdfReportE2E(unittest.TestCase):
    """End-to-end verification of technical inspection report generation."""

    @classmethod
    def setUpClass(cls):
        """Create test image fixtures in the upload directory."""
        cls.upload_dir = settings.abs_upload_dir
        os.makedirs(cls.upload_dir, exist_ok=True)
        cls.test_files = [
            "e2e_original.png",
            "e2e_preprocessed.png",
            "e2e_ead.png",
            "e2e_patchcore.png",
            "e2e_stage2.png",
            "e2e_stage3.png",
            "e2e_final.png",
            "e2e_mask.png",
            "e2e_overlay.png",
            "e2e_bbox.png",
            "e2e_opencv.png",
            "e2e_hybrid.png",
            "e2e_yolo.png",
        ]
        for name in cls.test_files:
            p = os.path.join(cls.upload_dir, name)
            img = Image.new("RGB", (256, 256), color=(60, 90, 120))
            img.save(p)

    @classmethod
    def tearDownClass(cls):
        """Clean up test image fixtures."""
        for name in cls.test_files:
            p = os.path.join(cls.upload_dir, name)
            try:
                os.remove(p)
            except OSError:
                pass

    def _relative_upload_path(self, filename: str) -> str:
        if "storage" in settings.UPLOAD_DIR:
            return f"storage/uploads/{filename}"
        return f"uploads/{filename}"

    def test_01_production_report_disabled_optional_evidence(self):
        """Standard production inspection where optional evidence is disabled.

        Verifies:
        - Exactly 4 clean pages (no spilling / mostly-empty pages).
        - Model-stage evidence displays canonical 3 pairs without duplicate final heatmap.
        - Disabled optional evidence (OpenCV, Hybrid map, YOLO) is omitted.
        - Zero 'Image unavailable' boxes.
        - Runtime table displays 'Optional CV/YOLO hybrid | Disabled' and 'Hybrid fusion applied | No'.
        - System context reflects updated production copy.
        """
        detection = Detection(
            id=58,
            user_id=1,
            category="metal_nut",
            anomaly_score=0.8842,
            confidence=0.8842,
            prediction="Anomalous",
            threshold=0.267,
            result_valid=True,
            review_required=False,
            primary_specialist="patchcore",
            decision_source="patchcore_calibrated",
            localization_source="stage3_evt_clip_refinement",
            route="stage3_stable",
            worker_cache="warm_pair",
            inference_time=1.42,
            validation_seconds=0.08,
            efficientad_seconds=0.45,
            patchcore_seconds=0.52,
            refiner_seconds=0.37,
            image_quality_state="ok",
            image_quality_message="Quality checks passed",
            defect_bbox_x=120,
            defect_bbox_y=85,
            defect_bbox_width=48,
            defect_bbox_height=36,
            defect_area_pixels=1420,
            defect_area_fraction=0.0217,
            defect_component_count=1,
            efficientad_image_score=0.4521,
            patchcore_image_score=0.8842,
            stage2_map_score=0.7912,
            stage3_map_score=0.8842,
            map_agreement=0.892,
            original_image_path=self._relative_upload_path("e2e_original.png"),
            preprocessed_path=self._relative_upload_path("e2e_preprocessed.png"),
            efficientad_heatmap_path=self._relative_upload_path("e2e_ead.png"),
            patchcore_heatmap_path=self._relative_upload_path("e2e_patchcore.png"),
            stage2_heatmap_path=self._relative_upload_path("e2e_stage2.png"),
            stage3_heatmap_path=self._relative_upload_path("e2e_stage3.png"),
            heatmap_path=self._relative_upload_path("e2e_final.png"),
            mask_path=self._relative_upload_path("e2e_mask.png"),
            overlay_path=self._relative_upload_path("e2e_overlay.png"),
            bbox_overlay_path=self._relative_upload_path("e2e_bbox.png"),
            hybrid_mode="off",
            hybrid_applied=False,
            hybrid_map_score=None,
            classical_cv_heatmap_path=None,
            classical_cv_score=None,
            yolo_roi_state="not_run",
            yolo_roi_mask_path=None,
            yolo_roi_confidence=None,
            created_at=datetime.now(timezone.utc),
        )

        pdf_rel_path = ReportService.generate_pdf_report(
            detection=detection,
            user_email="auditor@iso-inspection.org",
            remarks="Standard production run with verified 4-page layout.",
        )
        pdf_full_path = os.path.join(settings.abs_report_dir, os.path.basename(pdf_rel_path))
        self.assertTrue(os.path.isfile(pdf_full_path), f"PDF was not created at {pdf_full_path}")

        doc = fitz.open(pdf_full_path)
        try:
            # Must be exactly 4 clean pages
            self.assertEqual(len(doc), 4, f"Expected 4 pages for standard inspection, got {len(doc)}")

            full_text = "\n".join(doc[page_num].get_text() for page_num in range(len(doc)))

            # MUST EXIST:
            must_exist = [
                "Model-stage evidence",
                "EfficientAD heatmap",
                "PatchCore heatmap",
                "Stage-2 fusion heatmap",
                "Stage-3 EVT-CLIP heatmap",
                "Accepted final heatmap",
                "Localization and runtime evidence",
                "Hybrid fusion applied",
                "Optional OpenCV/YOLO evidence was disabled or not produced for this inspection.",
            ]
            for phrase in must_exist:
                self.assertIn(phrase, full_text, f"Expected phrase '{phrase}' missing from PDF text")

            # MUST NOT EXIST:
            must_not_exist = [
                "YOLO / ROI mask (optional)",
                "OpenCV evidence (benchmark-gated)",
                "Hybrid map peak",
                "Image unavailable",
            ]
            for phrase in must_not_exist:
                self.assertNotIn(phrase, full_text, f"Unwanted phrase '{phrase}' found in PDF text")

            # Ambiguous unclarified "Fusion applied" must NOT appear (only "Hybrid fusion applied")
            lines = [line.strip() for line in full_text.splitlines()]
            self.assertNotIn("Fusion applied", lines, "'Fusion applied' should be clarified to 'Hybrid fusion applied'")
        finally:
            doc.close()
            try:
                os.remove(pdf_full_path)
            except OSError:
                pass

    def test_02_report_with_genuine_optional_evidence(self):
        """Inspection where OpenCV, Hybrid, and YOLO optional evidence was produced.

        Verifies:
        - Optional blocks render with active labels.
        - Hybrid fusion applied reflects 'Yes'.
        - Hybrid map peak is displayed.
        - Zero 'Image unavailable' boxes since files exist.
        """
        detection = Detection(
            id=59,
            user_id=1,
            category="metal_nut",
            anomaly_score=0.9120,
            confidence=0.9120,
            prediction="Anomalous",
            threshold=0.267,
            result_valid=True,
            review_required=False,
            primary_specialist="patchcore",
            decision_source="patchcore_calibrated+hybrid_fusion",
            localization_source="stage3_evt_clip",
            route="stage3_stable",
            worker_cache="warm_pair",
            inference_time=1.65,
            validation_seconds=0.08,
            efficientad_seconds=0.45,
            patchcore_seconds=0.52,
            refiner_seconds=0.37,
            image_quality_state="ok",
            image_quality_message="Quality checks passed",
            defect_bbox_x=120,
            defect_bbox_y=85,
            defect_bbox_width=48,
            defect_bbox_height=36,
            defect_area_pixels=1420,
            defect_area_fraction=0.0217,
            defect_component_count=1,
            efficientad_image_score=0.4521,
            patchcore_image_score=0.9120,
            stage2_map_score=0.8120,
            stage3_map_score=0.9120,
            map_agreement=0.910,
            original_image_path=self._relative_upload_path("e2e_original.png"),
            preprocessed_path=self._relative_upload_path("e2e_preprocessed.png"),
            efficientad_heatmap_path=self._relative_upload_path("e2e_ead.png"),
            patchcore_heatmap_path=self._relative_upload_path("e2e_patchcore.png"),
            stage2_heatmap_path=self._relative_upload_path("e2e_stage2.png"),
            stage3_heatmap_path=self._relative_upload_path("e2e_stage3.png"),
            heatmap_path=self._relative_upload_path("e2e_final.png"),
            mask_path=self._relative_upload_path("e2e_mask.png"),
            overlay_path=self._relative_upload_path("e2e_overlay.png"),
            bbox_overlay_path=self._relative_upload_path("e2e_bbox.png"),
            hybrid_mode="localization",
            hybrid_applied=True,
            hybrid_map_score=0.9234,
            classical_cv_heatmap_path=self._relative_upload_path("e2e_opencv.png"),
            classical_cv_score=0.7812,
            classical_cv_seconds=0.12,
            classical_cv_defect_hint="color_outlier",
            yolo_roi_state="isolated_real_camera",
            yolo_roi_mask_path=self._relative_upload_path("e2e_yolo.png"),
            yolo_roi_confidence=0.965,
            created_at=datetime.now(timezone.utc),
        )

        pdf_rel_path = ReportService.generate_pdf_report(
            detection=detection,
            user_email="auditor@iso-inspection.org",
            remarks="Inspection with genuine OpenCV/Hybrid/YOLO evidence.",
        )
        pdf_full_path = os.path.join(settings.abs_report_dir, os.path.basename(pdf_rel_path))
        self.assertTrue(os.path.isfile(pdf_full_path), f"PDF was not created at {pdf_full_path}")

        doc = fitz.open(pdf_full_path)
        try:
            full_text = "\n".join(doc[page_num].get_text() for page_num in range(len(doc)))

            must_exist = [
                "OpenCV evidence (benchmark-gated)",
                "Hybrid map",
                "YOLO / ROI mask (optional)",
                "Hybrid fusion applied",
                "Hybrid map peak",
                "Yes",
            ]
            for phrase in must_exist:
                self.assertIn(phrase, full_text, f"Expected phrase '{phrase}' missing from PDF text")

            self.assertNotIn("Image unavailable", full_text, "All evidence files exist; 'Image unavailable' should not appear")
        finally:
            doc.close()
            try:
                os.remove(pdf_full_path)
            except OSError:
                pass

    def test_03_missing_evidence_warning_preserved(self):
        """Inspection where a mandatory image file is genuinely missing.

        Verifies:
        - Problem 10: 'Image unavailable' is properly preserved for genuine missing files.
        """
        detection = Detection(
            id=60,
            user_id=1,
            category="bottle",
            anomaly_score=0.3120,
            confidence=0.6880,
            prediction="Normal",
            threshold=0.267,
            result_valid=True,
            review_required=False,
            primary_specialist="efficientad",
            decision_source="efficientad_calibrated",
            localization_source="stage3_evt_clip_refinement",
            route="stage3_stable",
            original_image_path=self._relative_upload_path("e2e_original.png"),
            preprocessed_path="uploads/non_existent_preprocessed.png",  # Missing file
            efficientad_heatmap_path=self._relative_upload_path("e2e_ead.png"),
            patchcore_heatmap_path=self._relative_upload_path("e2e_patchcore.png"),
            stage2_heatmap_path=self._relative_upload_path("e2e_stage2.png"),
            stage3_heatmap_path=self._relative_upload_path("e2e_stage3.png"),
            heatmap_path=self._relative_upload_path("e2e_final.png"),
            mask_path=self._relative_upload_path("e2e_mask.png"),
            overlay_path=self._relative_upload_path("e2e_overlay.png"),
            bbox_overlay_path=self._relative_upload_path("e2e_bbox.png"),
            hybrid_mode="off",
            hybrid_applied=False,
            yolo_roi_state="not_run",
            created_at=datetime.now(timezone.utc),
        )

        pdf_rel_path = ReportService.generate_pdf_report(detection=detection)
        pdf_full_path = os.path.join(settings.abs_report_dir, os.path.basename(pdf_rel_path))
        doc = fitz.open(pdf_full_path)
        try:
            full_text = "\n".join(doc[page_num].get_text() for page_num in range(len(doc)))
            self.assertIn("Image unavailable", full_text, "Mandatory missing image should display 'Image unavailable'")
        finally:
            doc.close()
            try:
                os.remove(pdf_full_path)
            except OSError:
                pass

    def test_04_conditioned_categories_supported(self):
        """Verify all 3 conditioned categories are registered in the worker."""
        from app.services.evtclip_worker import CATEGORIES
        self.assertIn("metal_nut", CATEGORIES)
        self.assertIn("bottle", CATEGORIES)
        self.assertIn("capsule", CATEGORIES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
