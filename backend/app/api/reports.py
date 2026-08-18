import hashlib
import hmac
import json
import os
import uuid
import zipfile
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.permissions import owner_filter, require_owner
from app.models.user import User
from app.models.detection import Detection
from app.models.report import Report
from app.schemas.report import (
    ReportCreate, ReportResponse, ReportListResponse
)
from app.services.report_service import ReportService
from app.services.history_service import HistoryService

router = APIRouter(prefix="", tags=["Reports"])


@router.post(
    "/generate-report",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate PDF Report for a detection",
    description="Compiles professional ReportLab PDF report containing logo, visual analytics (original, heatmap, mask, overlay), prediction metrics, and remarks."
)
async def generate_report(
    req: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = owner_filter(select(Detection).where(Detection.id == req.detection_id), Detection, current_user)
    res = await db.execute(stmt)
    detection = res.scalars().first()

    if not detection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Detection with ID {req.detection_id} not found.")

    # Always regenerate the PDF from the current detection metadata so branding,
    # validator policy, and report layout changes are reflected immediately.
    # Remove the most recent duplicate record/file first to avoid accumulating
    # stale report copies for the same detection and remarks.
    existing_stmt = (
        select(Report)
        .where(Report.detection_id == detection.id, Report.user_id == current_user.id, Report.remarks == req.remarks)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    existing_report = (await db.execute(existing_stmt)).scalars().first()
    if existing_report:
        existing_abs = os.path.realpath(os.path.join(settings.BASE_DIR, existing_report.pdf_path))
        report_root = os.path.realpath(settings.abs_report_dir)
        if os.path.commonpath([existing_abs, report_root]) == report_root and os.path.isfile(existing_abs):
            try:
                os.remove(existing_abs)
            except OSError:
                pass
        await db.delete(existing_report)
        await db.flush()

    pdf_rel_path = ReportService.generate_pdf_report(
        detection=detection,
        user_email=current_user.email,
        remarks=req.remarks or "Standard Inspection PDF Report"
    )

    report = Report(
        detection_id=detection.id,
        user_id=current_user.id,
        pdf_path=pdf_rel_path,
        remarks=req.remarks
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    await HistoryService.log_action(
        db, current_user.id, "GENERATE_REPORT", f"Generated PDF report ID {report.id} for detection ID {detection.id}"
    )

    return report


@router.get(
    "/reports",
    response_model=ReportListResponse,
    summary="List generated reports",
    description="Retrieve paginated list of compiled PDF reports."
)
async def list_reports(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = owner_filter(select(Report), Report, current_user).order_by(Report.created_at.desc()).offset(max(skip, 0)).limit(min(max(limit, 1), 100))
    res = await db.execute(stmt)
    items = res.scalars().all()

    total_stmt = owner_filter(select(func.count(Report.id)), Report, current_user)
    total = (await db.execute(total_stmt)).scalar_one()

    return ReportListResponse(total=total, items=items)


@router.get(
    "/reports/{id}",
    response_model=ReportResponse,
    summary="Get report metadata by ID",
    description="Retrieve report details by report ID."
)
async def get_report_by_id(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = owner_filter(select(Report).where(Report.id == id), Report, current_user)
    res = await db.execute(stmt)
    report = res.scalars().first()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report with ID {id} not found.")

    return report


@router.get(
    "/download-report/{id}",
    summary="Download PDF report file",
    description="Download PDF document file directly for a report ID."
)
async def download_report(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = owner_filter(select(Report).where(Report.id == id), Report, current_user)
    res = await db.execute(stmt)
    report = res.scalars().first()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report with ID {id} not found.")

    abs_path = os.path.realpath(os.path.join(settings.BASE_DIR, report.pdf_path))
    report_root = os.path.realpath(settings.abs_report_dir)
    if os.path.commonpath([abs_path, report_root]) != report_root:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report path.")
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF report file does not exist on disk.")

    filename = os.path.basename(abs_path)
    return FileResponse(
        path=abs_path,
        media_type="application/pdf",
        filename=filename
    )


@router.delete(
    "/reports/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete report by ID",
    description="Delete report record and remove PDF file."
)
async def delete_report(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = owner_filter(select(Report).where(Report.id == id), Report, current_user)
    res = await db.execute(stmt)
    report = res.scalars().first()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report with ID {id} not found.")

    abs_path = os.path.realpath(os.path.join(settings.BASE_DIR, report.pdf_path))
    report_root = os.path.realpath(settings.abs_report_dir)
    if os.path.commonpath([abs_path, report_root]) != report_root:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report path.")
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except Exception:
            pass

    await db.delete(report)
    await db.commit()

    await HistoryService.log_action(db, current_user.id, "DELETE_REPORT", f"Deleted report ID {id}")

    return {"success": True, "message": f"Report ID {id} deleted successfully."}


@router.get(
    "/export-evidence/{detection_id}",
    summary="Download a complete inspection evidence bundle",
    description="Creates a ZIP containing PDF, JSON metadata, visual evidence, SHA-256 hashes, and an HMAC signature.",
)
async def export_evidence_bundle(
    detection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = owner_filter(select(Detection).where(Detection.id == detection_id), Detection, current_user)
    detection = (await db.execute(stmt)).scalars().first()
    if not detection:
        raise HTTPException(status_code=404, detail=f"Detection with ID {detection_id} not found.")

    report_root = os.path.realpath(settings.abs_report_dir)
    bundle_name = f"evtclip_evidence_{detection.id}_{uuid.uuid4().hex[:8]}.zip"
    bundle_path = os.path.join(report_root, bundle_name)
    temp_pdf_rel = ReportService.generate_pdf_report(
        detection=detection,
        user_email=current_user.email,
        remarks="EVT-CLIP evidence bundle",
    )
    temp_pdf_abs = os.path.realpath(os.path.join(settings.BASE_DIR, temp_pdf_rel))

    metadata = {
        "schema_version": "evtclip-evidence-v1",
        "detection_id": detection.id,
        "created_at": detection.created_at.isoformat() if detection.created_at else None,
        "operator": current_user.email,
        "dataset": detection.dataset_name,
        "selected_category": detection.category,
        "predicted_category": detection.predicted_category,
        "prediction": detection.prediction,
        "result_valid": detection.result_valid,
        "review_required": detection.review_required,
        "review_reason": detection.review_reason,
        "rejection_code": detection.rejection_code,
        "category_validator": detection.category_validator,
        "category_validation_message": detection.category_validation_message,
        "image_quality_state": detection.image_quality_state,
        "image_quality_message": detection.image_quality_message,
        "anomaly_score": detection.anomaly_score,
        "confidence": detection.confidence,
        "threshold": detection.threshold,
        "inference_time_seconds": detection.inference_time,
        "worker_cache": detection.worker_cache,
        "timings_seconds": {
            "category_validation": detection.validation_seconds,
            "efficientad": detection.efficientad_seconds,
            "patchcore": detection.patchcore_seconds,
            "evt_clip_refiner": detection.refiner_seconds,
        },
        "primary_specialist": detection.primary_specialist,
        "decision_source": detection.decision_source,
        "route": detection.route,
        "localization_source": detection.localization_source,
        "scores": {
            "efficientad": detection.efficientad_image_score,
            "patchcore": detection.patchcore_image_score,
            "stage2_peak": detection.stage2_map_score,
            "stage3_peak": detection.stage3_map_score,
            "map_agreement": detection.map_agreement,
        },
        "defect_analysis": {
            "mask_pixels": detection.defect_area_pixels,
            "mask_fraction": detection.defect_area_fraction,
            "component_count": detection.defect_component_count,
            "bounding_box": {
                "x": detection.defect_bbox_x,
                "y": detection.defect_bbox_y,
                "width": detection.defect_bbox_width,
                "height": detection.defect_bbox_height,
            } if detection.defect_bbox_width and detection.defect_bbox_height else None,
        },
        "ground_truth_policy": "Not available for ordinary uploads/camera images; evaluation metrics require labelled benchmark data.",
    }

    files_to_add = []
    # Evidence bundles obey the same fail-closed display policy as the UI/PDF:
    # invalid or unconfirmed inspections retain the original input and metadata,
    # but generated anomaly visualizations are withheld from the export.
    asset_map = {
        "original": detection.original_image_path,
        "preprocessed": detection.preprocessed_path if detection.result_valid else None,
        "efficientad_heatmap": detection.efficientad_heatmap_path if detection.result_valid else None,
        "patchcore_heatmap": detection.patchcore_heatmap_path if detection.result_valid else None,
        "stage2_heatmap": detection.stage2_heatmap_path if detection.result_valid else None,
        "stage3_heatmap": detection.stage3_heatmap_path if detection.result_valid else None,
        "defect_location": detection.bbox_overlay_path if detection.result_valid else None,
        "final_heatmap": detection.heatmap_path if detection.result_valid else None,
        "mask": detection.mask_path if detection.result_valid else None,
        "overlay": detection.overlay_path if detection.result_valid else None,
    }
    upload_root = os.path.realpath(settings.abs_upload_dir)
    for label, rel_path in asset_map.items():
        if not rel_path:
            continue
        candidate = os.path.realpath(os.path.join(settings.BASE_DIR, rel_path))
        if os.path.commonpath([candidate, upload_root]) == upload_root and os.path.isfile(candidate):
            extension = os.path.splitext(candidate)[1] or ".bin"
            files_to_add.append((candidate, f"evidence/{label}{extension}"))

    manifest = {}
    metadata_bytes = json.dumps(metadata, indent=2, sort_keys=True).encode("utf-8")
    manifest["metadata.json"] = hashlib.sha256(metadata_bytes).hexdigest()

    try:
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            archive.writestr("metadata.json", metadata_bytes)
            if os.path.isfile(temp_pdf_abs):
                archive.write(temp_pdf_abs, "inspection-report.pdf")
                with open(temp_pdf_abs, "rb") as stream:
                    manifest["inspection-report.pdf"] = hashlib.sha256(stream.read()).hexdigest()
            for source, archive_name in files_to_add:
                archive.write(source, archive_name)
                with open(source, "rb") as stream:
                    manifest[archive_name] = hashlib.sha256(stream.read()).hexdigest()
            manifest_document = {
                "schema_version": "evtclip-evidence-manifest-v2",
                "algorithm": "SHA-256",
                "files": manifest,
            }
            manifest_bytes = json.dumps(manifest_document, indent=2, sort_keys=True).encode("utf-8")
            archive.writestr("manifest.sha256.json", manifest_bytes)

            # HMAC signs the canonical manifest so accidental corruption and
            # deliberate file/hash edits are detectable by a verifier that
            # possesses the deployment signing secret. A domain-separated key
            # is derived instead of using the JWT secret directly.
            signing_source = settings.EVIDENCE_SIGNING_SECRET or settings.JWT_SECRET
            signing_key = hashlib.sha256(("evtclip-evidence-signing-v1:" + signing_source).encode("utf-8")).digest()
            canonical_manifest = json.dumps(manifest_document, sort_keys=True, separators=(",", ":")).encode("utf-8")
            signature = hmac.new(signing_key, canonical_manifest, hashlib.sha256).hexdigest()
            key_id = hashlib.sha256(signing_key).hexdigest()[:16]
            archive.writestr(
                "manifest.signature.json",
                json.dumps({
                    "schema_version": "evtclip-evidence-signature-v1",
                    "algorithm": "HMAC-SHA256",
                    "key_id": key_id,
                    "signature": signature,
                    "signed_object": "manifest.sha256.json",
                }, indent=2, sort_keys=True).encode("utf-8"),
            )
    finally:
        if os.path.isfile(temp_pdf_abs):
            try:
                os.remove(temp_pdf_abs)
            except OSError:
                pass

    await HistoryService.log_action(
        db,
        current_user.id,
        "EXPORT_EVIDENCE",
        f"Exported signed evidence bundle for detection ID {detection.id}",
    )
    return FileResponse(
        path=bundle_path,
        media_type="application/zip",
        filename=f"evt-clip-v2-evidence-{detection.id}.zip",
        background=BackgroundTask(lambda: os.path.exists(bundle_path) and os.remove(bundle_path)),
    )
