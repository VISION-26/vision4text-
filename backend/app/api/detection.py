import asyncio
import base64
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.detection import Detection
from app.models.detection_job import DetectionJob
from app.models.report import Report
from app.models.user import User
from app.schemas.detection import DetectionJobListItem, DetectionJobListResponse, DetectionJobResponse, DetectionListResponse, DetectionRequest, DetectionResponse, UploadResponse
from app.services.history_service import HistoryService
from app.services.image_service import ImageService

router = APIRouter(prefix="", tags=["Anomaly Detection"])
JOB_TIMEOUT_SECONDS = max(120, int(os.getenv("DETECTION_JOB_TIMEOUT_SECONDS", "900")))


def _safe_absolute_path(relative_path: str) -> Path:
    if not relative_path or ".." in Path(relative_path).parts:
        raise HTTPException(status_code=400, detail="Invalid stored image path.")
    candidate = Path(relative_path)
    resolved = (candidate if candidate.is_absolute() else Path(settings.BASE_DIR, candidate)).resolve()
    allowed_roots = {
        Path(settings.BASE_DIR).resolve(),
        Path(settings.abs_upload_dir).resolve(),
        Path(settings.abs_report_dir).resolve(),
    }
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        raise HTTPException(status_code=400, detail="Stored path is outside application storage.")
    return resolved


def _relative_upload_path(filename: str) -> str:
    return str(Path(settings.UPLOAD_DIR, filename)).replace("\\", "/")


def _save_job_assets(images: dict[str, str | None]) -> dict[str, str | None]:
    """Persist trusted worker PNG outputs atomically with bounded decoding."""
    paths: dict[str, str | None] = {
        "heatmap_path": None, "mask_path": None, "overlay_path": None,
        "preprocessed_path": None, "efficientad_heatmap_path": None,
        "patchcore_heatmap_path": None, "stage2_heatmap_path": None, "stage3_heatmap_path": None,
        "classical_cv_heatmap_path": None, "yolo_roi_mask_path": None, "hybrid_heatmap_path": None,
        "bbox_overlay_path": None,
    }
    max_asset_bytes = 25 * 1024 * 1024
    created: list[Path] = []
    try:
        for name in (
            "heatmap", "mask", "overlay", "preprocessed",
            "efficientad_heatmap", "patchcore_heatmap", "stage2_heatmap", "stage3_heatmap",
            "classical_cv_heatmap", "yolo_roi_mask", "hybrid_heatmap", "bbox_overlay",
        ):
            encoded = images.get(name)
            if not encoded:
                continue
            raw = base64.b64decode(encoded, validate=True)
            if len(raw) > max_asset_bytes:
                raise ValueError(f"Worker {name} asset exceeds the 25 MB safety limit")
            filename = f"{name}_{uuid.uuid4().hex[:12]}.png"
            target = Path(settings.abs_upload_dir, filename)
            temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
            with temporary.open("wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            created.append(target)
            paths[f"{name}_path"] = _relative_upload_path(filename)
        return paths
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise


def _cleanup_job_assets(paths: dict[str, str | None]) -> None:
    for stored_path in paths.values():
        if not stored_path:
            continue
        try:
            _safe_absolute_path(stored_path).unlink(missing_ok=True)
        except Exception:
            pass


async def _spawn_cpu_inference_call(image_path: Path, category: str):
    import modal

    image_bytes = await asyncio.to_thread(image_path.read_bytes)
    if settings.MODAL_WORKER_CLASS:
        Worker = modal.Cls.from_name(settings.MODAL_APP_NAME, settings.MODAL_WORKER_CLASS)
        worker = Worker()
        method = getattr(worker, settings.MODAL_WORKER_METHOD)
        return await method.spawn.aio(image_bytes, image_path.name, category.lower())
    worker = modal.Function.from_name(settings.MODAL_APP_NAME, settings.MODAL_WORKER_FUNCTION)
    return await worker.spawn.aio(image_bytes, image_path.name, category.lower())


async def _run_cpu_precheck_call(image_bytes: bytes, filename: str, category: str):
    import modal

    if settings.MODAL_WORKER_CLASS:
        Worker = modal.Cls.from_name(settings.MODAL_APP_NAME, settings.MODAL_WORKER_CLASS)
        worker = Worker()
        method = getattr(worker, "precheck")
        return await method.remote.aio(image_bytes, filename, category.lower())
    raise RuntimeError("Precheck requires the configured Modal worker class.")


async def _store_detection(db: AsyncSession, user_id: int, req: DetectionRequest, result: dict) -> Detection:
    detection = Detection(
        user_id=user_id,
        original_image_path=result["original_image_path"],
        heatmap_path=result.get("heatmap_path"),
        mask_path=result.get("mask_path"),
        overlay_path=result.get("overlay_path"),
        anomaly_score=float(result["anomaly_score"]),
        confidence=float(result["confidence"]),
        prediction=result["prediction"],
        inference_time=float(result["inference_time"]),
        dataset_name=req.dataset_name or "MVTec AD Industrial Inspection",
        category=req.category.lower(),
        threshold=result.get("threshold"),
        result_valid=bool(result.get("result_valid", True)),
        review_required=bool(result.get("review_required", False)),
        review_reason=result.get("review_reason"),
        decision_source=result.get("decision_source"),
        route=result.get("route"),
        localization_source=result.get("localization_source"),
        primary_specialist=result.get("primary_specialist"),
        predicted_category=result.get("predicted_category"),
        category_validation_message=result.get("category_validation_message"),
        category_validator=result.get("category_validator"),
        rejection_code=result.get("rejection_code"),
        worker_cache=result.get("worker_cache"),
        validation_seconds=result.get("validation_seconds"),
        efficientad_seconds=result.get("efficientad_seconds"),
        patchcore_seconds=result.get("patchcore_seconds"),
        refiner_seconds=result.get("refiner_seconds"),
        image_quality_state=result.get("image_quality_state"),
        image_quality_message=result.get("image_quality_message"),
        preprocessed_path=result.get("preprocessed_path"),
        efficientad_heatmap_path=result.get("efficientad_heatmap_path"),
        patchcore_heatmap_path=result.get("patchcore_heatmap_path"),
        stage2_heatmap_path=result.get("stage2_heatmap_path"),
        stage3_heatmap_path=result.get("stage3_heatmap_path"),
        classical_cv_heatmap_path=result.get("classical_cv_heatmap_path"),
        yolo_roi_mask_path=result.get("yolo_roi_mask_path"),
        hybrid_heatmap_path=result.get("hybrid_heatmap_path"),
        bbox_overlay_path=result.get("bbox_overlay_path"),
        efficientad_image_score=result.get("efficientad_image_score"),
        patchcore_image_score=result.get("patchcore_image_score"),
        stage2_map_score=result.get("stage2_map_score"),
        stage3_map_score=result.get("stage3_map_score"),
        classical_cv_score=result.get("classical_cv_score"),
        classical_cv_seconds=result.get("classical_cv_seconds"),
        classical_cv_defect_hint=result.get("classical_cv_defect_hint"),
        hybrid_mode=result.get("hybrid_mode"),
        hybrid_applied=bool(result.get("hybrid_applied", False)),
        hybrid_map_score=result.get("hybrid_map_score"),
        yolo_roi_state=result.get("yolo_roi_state"),
        yolo_roi_confidence=result.get("yolo_roi_confidence"),
        yolo_roi_class=result.get("yolo_roi_class"),
        map_agreement=result.get("map_agreement"),
        defect_area_pixels=result.get("defect_area_pixels"),
        defect_area_fraction=result.get("defect_area_fraction"),
        defect_component_count=result.get("defect_component_count"),
        defect_bbox_x=result.get("defect_bbox_x"),
        defect_bbox_y=result.get("defect_bbox_y"),
        defect_bbox_width=result.get("defect_bbox_width"),
        defect_bbox_height=result.get("defect_bbox_height"),
    )
    db.add(detection)
    # Flush only: callers decide the transaction boundary. In queued mode this
    # lets detection creation and job completion commit atomically.
    await db.flush()
    await db.refresh(detection)
    return detection


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    saved_path, size_bytes, content_type = await ImageService.save_uploaded_image(file)
    await HistoryService.log_action(db, current_user.id, "UPLOAD_IMAGE", f"Uploaded image: {file.filename} -> {saved_path}")
    return UploadResponse(image_path=saved_path, filename=file.filename or "upload", size_bytes=size_bytes, content_type=content_type, message="Image uploaded successfully.")


@router.post("/detect/precheck")
async def precheck_detection_input(
    category: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    del current_user  # authentication is intentionally required even though no DB row is created
    selected = category.strip().lower()
    if selected not in settings.SUPPORTED_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unsupported category.")

    raw = await file.read(20 * 1024 * 1024 + 1)
    if not raw:
        raise HTTPException(status_code=400, detail="Image payload is empty.")
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds the 20 MB limit.")

    try:
        return await _run_cpu_precheck_call(raw, file.filename or "upload.png", selected)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Input precheck unavailable: {exc}") from exc


@router.post("/detect", response_model=DetectionResponse, status_code=status.HTTP_201_CREATED)
async def run_detection(req: DetectionRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if settings.MODAL_JOB_QUEUE:
        raise HTTPException(status_code=409, detail="This deployment uses queued CPU inference. Submit /detect/jobs and poll the returned job.")
    if not req.image_path.startswith(f"{settings.UPLOAD_DIR.rstrip('/')}/") or ".." in req.image_path:
        raise HTTPException(status_code=400, detail="image_path must reference an uploaded image.")
    try:
        from app.services.prediction_service import PredictionService
        result = PredictionService.predict(req.image_path, req.category, req.threshold)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    detection = await _store_detection(db, current_user.id, req, result)
    await db.commit()
    await db.refresh(detection)
    await HistoryService.log_action(db, current_user.id, "RUN_DETECTION", f"Ran detection ID {detection.id}. Result: {detection.prediction}")
    return detection


@router.post("/detect/jobs", response_model=DetectionJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_detection_job(req: DetectionRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.category.lower() not in settings.SUPPORTED_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unsupported category.")
    upload_prefix = f"{settings.UPLOAD_DIR.rstrip('/')}/"
    if not req.image_path.startswith(upload_prefix) or ".." in req.image_path:
        raise HTTPException(status_code=400, detail="image_path must reference an uploaded image.")
    image_path = _safe_absolute_path(req.image_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded image not found.")

    if not settings.MODAL_JOB_QUEUE:
        # Local compatibility: execute immediately but expose the same job-shaped response.
        from app.services.prediction_service import PredictionService
        result = PredictionService.predict(req.image_path, req.category, req.threshold)
        detection = await _store_detection(db, current_user.id, req, result)
        job = DetectionJob(call_id=f"local-{uuid.uuid4().hex}", user_id=current_user.id, image_path=req.image_path, dataset_name=req.dataset_name, category=req.category.lower(), threshold=req.threshold, status="complete", detection_id=detection.id)
        db.add(job)
        await db.commit(); await db.refresh(job)
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="complete", detection=detection)

    try:
        # Keep the FastAPI event loop responsive while reading the upload and
        # submitting the long-running Modal call.
        call = await _spawn_cpu_inference_call(image_path, req.category.lower())
    except Exception as exc:
        # No job owns this freshly uploaded file if submission itself failed.
        # Remove it so repeated transient failures do not leak orphan uploads.
        try:
            image_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise HTTPException(status_code=503, detail=f"Unable to submit CPU inference job: {exc}") from exc

    job = DetectionJob(call_id=call.object_id, user_id=current_user.id, image_path=req.image_path, dataset_name=req.dataset_name, category=req.category.lower(), threshold=req.threshold, status="queued")
    db.add(job)
    await db.commit(); await db.refresh(job)
    await HistoryService.log_action(db, current_user.id, "QUEUE_DETECTION", f"Queued CPU detection job {job.call_id} for {req.category}.")
    return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="queued")


def _job_list_item(job: DetectionJob) -> DetectionJobListItem:
    return DetectionJobListItem(
        job_id=job.id,
        call_id=job.call_id,
        status=job.status,
        category=job.category,
        dataset_name=job.dataset_name,
        detection_id=job.detection_id,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/detect/jobs", response_model=DetectionJobListResponse)
async def list_detection_jobs(
    limit: int = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(int(limit), 100))
    base = select(DetectionJob)
    count_stmt = select(func.count(DetectionJob.id))
    if current_user.role != "Admin":
        base = base.where(DetectionJob.user_id == current_user.id)
        count_stmt = count_stmt.where(DetectionJob.user_id == current_user.id)
    jobs = (await db.execute(base.order_by(DetectionJob.created_at.desc()).limit(limit))).scalars().all()
    total = int((await db.execute(count_stmt)).scalar() or 0)
    return DetectionJobListResponse(total=total, items=[_job_list_item(job) for job in jobs])


@router.post("/detect/jobs/{job_id}/cancel", response_model=DetectionJobResponse)
async def cancel_detection_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DetectionJob).where(DetectionJob.id == job_id)
    if current_user.role != "Admin":
        stmt = stmt.where(DetectionJob.user_id == current_user.id)
    job = (await db.execute(stmt)).scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Detection job not found.")
    if job.detection_id or job.status == "complete":
        detection = None
        if job.detection_id:
            detection = (await db.execute(select(Detection).where(Detection.id == job.detection_id))).scalars().first()
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="complete", detection=detection)
    if job.status in {"cancelled", "failed", "timed_out"}:
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status=job.status, error=job.error)

    if not job.call_id.startswith("local-"):
        try:
            import modal
            function_call = modal.FunctionCall.from_id(job.call_id)
            await asyncio.to_thread(function_call.cancel)
        except Exception:
            # Cancellation is best-effort. The persistent state still prevents
            # the UI from treating this job as an active inspection.
            pass
    job.status = "cancelled"
    job.error = "Cancelled by operator."
    await db.commit()
    await HistoryService.log_action(db, current_user.id, "CANCEL_DETECTION", f"Cancelled CPU detection job {job.id}.")
    return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="cancelled", error=job.error)


@router.post("/detect/jobs/{job_id}/retry", response_model=DetectionJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_detection_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DetectionJob).where(DetectionJob.id == job_id)
    if current_user.role != "Admin":
        stmt = stmt.where(DetectionJob.user_id == current_user.id)
    source = (await db.execute(stmt)).scalars().first()
    if not source:
        raise HTTPException(status_code=404, detail="Detection job not found.")
    if source.status not in {"failed", "timed_out", "cancelled"}:
        raise HTTPException(status_code=409, detail="Only failed, timed-out, or cancelled jobs can be retried.")
    image_path = _safe_absolute_path(source.image_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="The original uploaded image is no longer available for retry.")
    try:
        call = await _spawn_cpu_inference_call(image_path, source.category)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Unable to retry CPU inference job: {exc}") from exc

    retry = DetectionJob(
        call_id=call.object_id,
        user_id=source.user_id,
        image_path=source.image_path,
        dataset_name=source.dataset_name,
        category=source.category,
        threshold=source.threshold,
        status="queued",
    )
    db.add(retry)
    await db.commit()
    await db.refresh(retry)
    await HistoryService.log_action(db, current_user.id, "RETRY_DETECTION", f"Retried CPU detection job {source.id} as job {retry.id}.")
    return DetectionJobResponse(job_id=retry.id, call_id=retry.call_id, status="queued")


@router.get("/detect/jobs/{job_id}", response_model=DetectionJobResponse)
async def poll_detection_job(job_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(DetectionJob).where(DetectionJob.id == job_id)
    if current_user.role != "Admin":
        stmt = stmt.where(DetectionJob.user_id == current_user.id)
    job = (await db.execute(stmt)).scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Detection job not found.")
    if job.status in {"cancelled", "timed_out"}:
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status=job.status, error=job.error)

    created = job.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_seconds = max(0.0, (datetime.now(timezone.utc) - created).total_seconds())
    if not job.detection_id and job.status not in {"failed", "complete"} and age_seconds > JOB_TIMEOUT_SECONDS:
        if not job.call_id.startswith("local-"):
            try:
                import modal
                function_call = modal.FunctionCall.from_id(job.call_id)
                await asyncio.to_thread(function_call.cancel)
            except Exception:
                pass
        job.status = "timed_out"
        job.error = f"Inspection exceeded the {JOB_TIMEOUT_SECONDS}-second queue/runtime limit."
        await db.commit()
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="timed_out", error=job.error)

    if job.detection_id:
        detection = (await db.execute(select(Detection).where(Detection.id == job.detection_id))).scalars().first()
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="complete", detection=detection)
    if job.status == "failed":
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="failed", error=job.error)
    if job.call_id.startswith("local-"):
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status=job.status)

    try:
        import modal
        function_call = modal.FunctionCall.from_id(job.call_id)
        payload = await function_call.get.aio(timeout=0)
    except TimeoutError:
        pending_status = "starting" if age_seconds < 8 else "running"
        if job.status != pending_status:
            job.status = pending_status
            await db.commit()
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status=pending_status)
    except Exception as exc:
        job.status = "failed"; job.error = str(exc)[:2000]; await db.commit()
        return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="failed", error=job.error)

    assets: dict[str, str | None] = {
        "heatmap_path": None, "mask_path": None, "overlay_path": None,
        "preprocessed_path": None, "efficientad_heatmap_path": None,
        "patchcore_heatmap_path": None, "stage2_heatmap_path": None, "stage3_heatmap_path": None,
        "classical_cv_heatmap_path": None, "yolo_roi_mask_path": None, "hybrid_heatmap_path": None,
        "bbox_overlay_path": None,
    }
    try:
        if not isinstance(payload, dict) or not isinstance(payload.get("metadata"), dict):
            raise ValueError("CPU worker returned a malformed payload")
        meta = payload["metadata"]
        result_valid = bool(meta.get("result_valid", False))
        # Defense in depth: even if a future worker accidentally returns maps
        # with an invalid result, the web layer will not persist them.
        if result_valid:
            images = payload.get("images_base64_png") or {}
            if not isinstance(images, dict):
                raise ValueError("CPU worker returned malformed image evidence")
            assets = _save_job_assets(images)

        raw_decision = meta.get("raw_anomaly_decision")
        if raw_decision == "invalid":
            prediction = "Invalid Input"
        elif raw_decision == "anomaly":
            prediction = "Anomalous"
        elif raw_decision == "normal":
            prediction = "Normal"
        else:
            raise ValueError("CPU worker returned an unknown decision state")

        score = float(meta.get("score") or 0.0)
        confidence_value = meta.get("confidence")
        # Do not synthesize confidence from anomaly score; they are different
        # quantities. Missing confidence is recorded conservatively as zero.
        confidence = float(confidence_value) if confidence_value is not None else 0.0
        result = {
            "original_image_path": job.image_path,
            **assets,
            "anomaly_score": score,
            "confidence": confidence,
            "prediction": prediction,
            "inference_time": float(meta.get("elapsed_seconds") or 0.0),
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
            "hybrid_applied": bool(meta.get("hybrid_applied", False)),
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
        req = DetectionRequest(image_path=job.image_path, dataset_name=job.dataset_name, category=job.category, threshold=job.threshold)
        detection = await _store_detection(db, job.user_id, req, result)
        job.status = "complete"
        job.detection_id = detection.id
        await db.commit()
    except Exception as exc:
        _cleanup_job_assets(assets)
        try:
            await db.rollback()
        except Exception:
            pass
        # Re-fetch after rollback so the job can be marked terminal instead of
        # becoming a permanently spinning client poll.
        failed_job = (await db.execute(select(DetectionJob).where(DetectionJob.id == job_id))).scalars().first()
        if failed_job and not failed_job.detection_id:
            failed_job.status = "failed"
            failed_job.error = f"Result processing failed: {type(exc).__name__}"[:2000]
            await db.commit()
            return DetectionJobResponse(job_id=failed_job.id, call_id=failed_job.call_id, status="failed", error=failed_job.error)
        raise

    action = "REJECT_INPUT" if detection.prediction == "Invalid Input" else "RUN_DETECTION"
    await HistoryService.log_action(db, job.user_id, action, f"CPU detection ID {detection.id} completed. Result: {detection.prediction}")
    return DetectionJobResponse(job_id=job.id, call_id=job.call_id, status="complete", detection=detection)


@router.get("/detection/{id}", response_model=DetectionResponse)
async def get_detection_by_id(id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Detection).where(Detection.id == id)
    if current_user.role != "Admin": stmt = stmt.where(Detection.user_id == current_user.id)
    detection = (await db.execute(stmt)).scalars().first()
    if not detection: raise HTTPException(status_code=404, detail=f"Detection with ID {id} not found.")
    return detection


@router.get("/detection/{id}/asset/{asset_name}")
async def get_detection_asset(id: int, asset_name: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    fields = {
        "original": "original_image_path",
        "preprocessed": "preprocessed_path",
        "efficientad_heatmap": "efficientad_heatmap_path",
        "patchcore_heatmap": "patchcore_heatmap_path",
        "stage2_heatmap": "stage2_heatmap_path",
        "stage3_heatmap": "stage3_heatmap_path",
        "classical_cv_heatmap": "classical_cv_heatmap_path",
        "yolo_roi_mask": "yolo_roi_mask_path",
        "hybrid_heatmap": "hybrid_heatmap_path",
        "bbox_overlay": "bbox_overlay_path",
        "heatmap": "heatmap_path",
        "mask": "mask_path",
        "overlay": "overlay_path",
    }
    field = fields.get(asset_name)
    if not field: raise HTTPException(status_code=404, detail="Unknown asset.")
    stmt = select(Detection).where(Detection.id == id)
    if current_user.role != "Admin": stmt = stmt.where(Detection.user_id == current_user.id)
    detection = (await db.execute(stmt)).scalars().first()
    if not detection:
        raise HTTPException(status_code=404, detail=f"Detection with ID {id} not found.")
    if asset_name != "original" and not detection.result_valid:
        raise HTTPException(
            status_code=409,
            detail="AI visualization withheld because this inspection did not pass input/category validation.",
        )
    relative_path = getattr(detection, field, None)
    if not relative_path: raise HTTPException(status_code=404, detail="Asset not found.")
    absolute_path = _safe_absolute_path(relative_path)
    if not absolute_path.is_file(): raise HTTPException(status_code=404, detail="Asset not found.")
    return FileResponse(absolute_path)


@router.get("/detections", response_model=DetectionListResponse)
async def list_detections(skip: int = 0, limit: int = 50, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    limit = min(max(limit, 1), 100)
    stmt = select(Detection); total_stmt = select(func.count(Detection.id))
    if current_user.role != "Admin":
        stmt = stmt.where(Detection.user_id == current_user.id); total_stmt = total_stmt.where(Detection.user_id == current_user.id)
    items = (await db.execute(stmt.order_by(Detection.created_at.desc()).offset(max(skip, 0)).limit(limit))).scalars().all()
    total = (await db.execute(total_stmt)).scalar_one()
    return DetectionListResponse(total=total, items=items)


@router.delete("/detection/{id}")
async def delete_detection(id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Detection).where(Detection.id == id)
    if current_user.role != "Admin": stmt = stmt.where(Detection.user_id == current_user.id)
    detection = (await db.execute(stmt)).scalars().first()
    if not detection: raise HTTPException(status_code=404, detail=f"Detection record ID {id} not found.")
    reports = (await db.execute(select(Report).where(Report.detection_id == detection.id))).scalars().all()
    jobs = (await db.execute(select(DetectionJob).where(DetectionJob.detection_id == detection.id))).scalars().all()
    paths = [
        detection.original_image_path, detection.preprocessed_path,
        detection.efficientad_heatmap_path, detection.patchcore_heatmap_path,
        detection.stage2_heatmap_path, detection.stage3_heatmap_path, detection.classical_cv_heatmap_path,
        detection.yolo_roi_mask_path, detection.hybrid_heatmap_path, detection.bbox_overlay_path,
        detection.heatmap_path, detection.mask_path, detection.overlay_path,
        *(report.pdf_path for report in reports),
    ]
    for stored_path in paths:
        if not stored_path:
            continue
        try:
            _safe_absolute_path(stored_path).unlink(missing_ok=True)
        except Exception:
            pass
    for job in jobs:
        await db.delete(job)
    for report in reports:
        await db.delete(report)
    await db.delete(detection)
    await db.commit()
    await HistoryService.log_action(db, current_user.id, "DELETE_DETECTION", f"Deleted detection record ID {id}")
    return {"success": True, "message": f"Detection record ID {id} deleted successfully."}
