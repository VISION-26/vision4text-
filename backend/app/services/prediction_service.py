"""Real EVT-CLIP adapter for non-queued/local CPU execution.

The hardened production build intentionally contains no simulated anomaly
predictor. Modal production uses the asynchronous CPU worker class. This adapter
keeps the legacy synchronous `/detect` contract aligned with the same worker
semantics when the full ML dependency stack and `/models/production` are
available locally.
"""
from __future__ import annotations

import base64
import os
import time
import uuid
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.utils.logger import logger


class PredictionService:
    @staticmethod
    def _resolve_image_path(image_path: str) -> str:
        candidate = Path(image_path)
        full_path = candidate if candidate.is_absolute() else Path(settings.BASE_DIR, candidate)
        if not full_path.is_file():
            raise ValueError("Image for prediction was not found.")
        return str(full_path)

    @staticmethod
    def _relative_upload_path(filename: str) -> str:
        return str(Path(settings.UPLOAD_DIR, filename)).replace("\\", "/")

    @classmethod
    def _save_worker_images(cls, images: dict[str, str | None], result_valid: bool) -> dict[str, str]:
        # Mirror the production fail-closed evidence policy: invalid inputs never
        # persist derived heatmaps/masks/overlays as accepted visual evidence.
        if not result_valid:
            return {}
        result: dict[str, str] = {}
        for name in (
            "preprocessed", "efficientad_heatmap", "patchcore_heatmap",
            "stage2_heatmap", "stage3_heatmap", "classical_cv_heatmap", "yolo_roi_mask",
            "hybrid_heatmap", "bbox_overlay", "heatmap", "mask", "overlay",
        ):
            encoded = images.get(name)
            if not encoded:
                continue
            filename = f"{name}_{uuid.uuid4().hex[:12]}.png"
            Path(settings.abs_upload_dir, filename).write_bytes(base64.b64decode(encoded))
            result[f"{name}_path"] = cls._relative_upload_path(filename)
        return result

    @classmethod
    def predict(cls, image_path: str, category: str | None = None, _threshold: float | None = None) -> dict[str, Any]:
        if settings.DEMO_MODE:
            raise RuntimeError(
                "DEMO_MODE is disabled in the hardened EVT-CLIP build. "
                "Use the verified model runtime or Modal CPU queue."
            )

        started = time.perf_counter()
        full_image_path = cls._resolve_image_path(image_path)
        selected_category = (category or "").strip().lower()
        if selected_category not in settings.SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported category. Select one of: {', '.join(sorted(settings.SUPPORTED_CATEGORIES))}.")

        os.environ.setdefault("EVT_MODEL_ROOT", settings.abs_model_dir)
        from app.services.evtclip_worker import infer_image_bytes

        payload = infer_image_bytes(Path(full_image_path).read_bytes(), Path(full_image_path).name, selected_category)
        meta = payload["metadata"]
        result_valid = bool(meta.get("result_valid", False))
        raw_decision = meta.get("raw_anomaly_decision")
        if raw_decision == "invalid":
            prediction = "Invalid Input"
        elif raw_decision == "anomaly":
            prediction = "Anomalous"
        else:
            prediction = "Normal"

        score = float(meta.get("score") or 0.0)
        confidence_raw = meta.get("confidence")
        confidence = float(confidence_raw if confidence_raw is not None else 0.0)
        model_result = {
            **cls._save_worker_images(payload.get("images_base64_png") or {}, result_valid),
            "anomaly_score": score,
            "confidence": confidence,
            "prediction": prediction,
            "threshold": float(meta.get("final_threshold", 0.267)),
            "result_valid": result_valid,
            "review_required": bool(meta.get("review_required", True)),
            "review_reason": meta.get("review_reason"),
            "decision_source": meta.get("decision_source"),
            "route": meta.get("route"),
            "localization_source": meta.get("localization_source"),
            "primary_specialist": meta.get("primary_specialist"),
            "predicted_category": meta.get("predicted_category"),
            "category_validation_message": meta.get("category_validation_message"),
            "category_validator": meta.get("category_validator"),
            "rejection_code": meta.get("rejection_code"),
            "worker_cache": meta.get("worker_cache"),
            "validation_seconds": meta.get("validation_seconds"),
            "efficientad_seconds": meta.get("efficientad_seconds"),
            "patchcore_seconds": meta.get("patchcore_seconds"),
            "refiner_seconds": meta.get("refiner_seconds"),
            "image_quality_state": meta.get("image_quality_state"),
            "image_quality_message": meta.get("image_quality_message"),
            "efficientad_image_score": meta.get("efficientad_image_score"),
            "patchcore_image_score": meta.get("patchcore_image_score"),
            "stage2_map_score": meta.get("stage2_map_score"),
            "stage3_map_score": meta.get("stage3_map_score"),
            "classical_cv_score": meta.get("classical_cv_score"),
            "classical_cv_seconds": meta.get("classical_cv_seconds"),
            "classical_cv_defect_hint": meta.get("classical_cv_defect_hint"),
            "hybrid_mode": meta.get("hybrid_mode"),
            "hybrid_applied": meta.get("hybrid_applied"),
            "hybrid_map_score": meta.get("hybrid_map_score"),
            "yolo_roi_state": meta.get("yolo_roi_state"),
            "yolo_roi_confidence": meta.get("yolo_roi_confidence"),
            "yolo_roi_class": meta.get("yolo_roi_class"),
            "map_agreement": meta.get("map_agreement"),
            "defect_area_pixels": meta.get("defect_area_pixels"),
            "defect_area_fraction": meta.get("defect_area_fraction"),
            "defect_component_count": meta.get("defect_component_count"),
            "defect_bbox_x": (meta.get("defect_bbox") or {}).get("x") if isinstance(meta.get("defect_bbox"), dict) else None,
            "defect_bbox_y": (meta.get("defect_bbox") or {}).get("y") if isinstance(meta.get("defect_bbox"), dict) else None,
            "defect_bbox_width": (meta.get("defect_bbox") or {}).get("width") if isinstance(meta.get("defect_bbox"), dict) else None,
            "defect_bbox_height": (meta.get("defect_bbox") or {}).get("height") if isinstance(meta.get("defect_bbox"), dict) else None,
        }

        result = {
            "original_image_path": image_path.replace("\\", "/"),
            **model_result,
            "anomaly_score": round(score, 4),
            "confidence": round(confidence, 4),
            "inference_time": round(float(meta.get("elapsed_seconds") or (time.perf_counter() - started)), 4),
        }
        logger.info("Prediction completed for '%s' (%s).", image_path, result["prediction"])
        return result
