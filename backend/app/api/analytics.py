from __future__ import annotations

from datetime import datetime, timedelta, timezone
import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.detection import Detection
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])

RANGE_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}


def _filters(current_user: User, start: datetime | None):
    conditions = []
    if current_user.role != "Admin":
        conditions.append(Detection.user_id == current_user.id)
    if start is not None:
        conditions.append(Detection.created_at >= start)
    return conditions


@router.get("/overview")
async def analytics_overview(
    range: str = Query(default="week", pattern="^(day|week|month|year|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=RANGE_DAYS[range]) if range in RANGE_DAYS else None
    conditions = _filters(current_user, start)

    totals_stmt = select(
        func.count(Detection.id).label("total"),
        func.sum(case((Detection.result_valid.is_(True), 1), else_=0)).label("valid"),
        func.sum(case((Detection.result_valid.is_(False), 1), else_=0)).label("invalid"),
        func.sum(case(((Detection.review_required.is_(True)) & (Detection.result_valid.is_(True)), 1), else_=0)).label("review"),
        func.sum(case(((Detection.prediction == "Anomalous") & (Detection.result_valid.is_(True)), 1), else_=0)).label("anomalies"),
        func.sum(case(((Detection.prediction == "Normal") & (Detection.result_valid.is_(True)), 1), else_=0)).label("normal"),
        func.avg(Detection.inference_time).label("avg_inference"),
        func.max(Detection.inference_time).label("max_inference"),
    ).where(*conditions)
    total_row = (await db.execute(totals_stmt)).one()

    category_stmt = (
        select(
            Detection.category,
            func.count(Detection.id).label("count"),
            func.sum(case(((Detection.prediction == "Anomalous") & (Detection.result_valid.is_(True)), 1), else_=0)).label("anomalies"),
            func.sum(case((Detection.result_valid.is_(False), 1), else_=0)).label("invalid"),
        )
        .where(*conditions)
        .group_by(Detection.category)
        .order_by(func.count(Detection.id).desc())
    )
    category_rows = (await db.execute(category_stmt)).all()

    # The production DB is SQLite. These buckets keep dashboard payloads tiny
    # even after years of scans instead of downloading every historical record.
    if range == "day":
        bucket = func.strftime("%Y-%m-%d %H:00", Detection.created_at)
    elif range in {"week", "month"}:
        bucket = func.strftime("%Y-%m-%d", Detection.created_at)
    else:
        bucket = func.strftime("%Y-%m", Detection.created_at)

    trend_stmt = (
        select(
            bucket.label("bucket"),
            func.count(Detection.id).label("detections"),
            func.sum(case(((Detection.prediction == "Anomalous") & (Detection.result_valid.is_(True)), 1), else_=0)).label("anomalies"),
            func.sum(case(((Detection.review_required.is_(True)) & (Detection.result_valid.is_(True)), 1), else_=0)).label("review"),
            func.sum(case((Detection.result_valid.is_(False), 1), else_=0)).label("invalid"),
            func.avg(Detection.inference_time).label("avg_inference"),
        )
        .where(*conditions)
        .group_by(bucket)
        .order_by(bucket.asc())
    )
    trend_rows = (await db.execute(trend_stmt)).all()

    total = int(total_row.total or 0)
    anomalies = int(total_row.anomalies or 0)
    valid = int(total_row.valid or 0)
    return {
        "range": range,
        "start": start.isoformat() if start else None,
        "end": now.isoformat(),
        "totals": {
            "total": total,
            "valid": valid,
            "invalid": int(total_row.invalid or 0),
            "review": int(total_row.review or 0),
            "anomalies": anomalies,
            "normal": int(total_row.normal or 0),
            "anomaly_rate": round((anomalies / valid * 100.0) if valid else 0.0, 2),
            "avg_inference_seconds": round(float(total_row.avg_inference or 0.0), 3),
            "max_inference_seconds": round(float(total_row.max_inference or 0.0), 3),
        },
        "trend": [
            {
                "bucket": row.bucket,
                "detections": int(row.detections or 0),
                "anomalies": int(row.anomalies or 0),
                "review": int(row.review or 0),
                "invalid": int(row.invalid or 0),
                "avg_inference_seconds": round(float(row.avg_inference or 0.0), 3),
            }
            for row in trend_rows
        ],
        "categories": [
            {
                "category": row.category or "unknown",
                "count": int(row.count or 0),
                "anomalies": int(row.anomalies or 0),
                "invalid": int(row.invalid or 0),
            }
            for row in category_rows
        ],
    }


@router.get("/export.csv")
async def analytics_export_csv(
    range: str = Query(default="week", pattern="^(day|week|month|year|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export the selected analytics window as a portable UTF-8 CSV."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=RANGE_DAYS[range]) if range in RANGE_DAYS else None
    conditions = _filters(current_user, start)
    stmt = select(Detection).where(*conditions).order_by(Detection.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()

    stream = io.StringIO(newline="")
    # Excel-friendly UTF-8 BOM while remaining standards-compatible CSV text.
    stream.write("\ufeff")
    writer = csv.writer(stream)
    writer.writerow([
        "detection_id", "created_at_utc", "dataset", "selected_category",
        "predicted_category", "prediction", "result_valid", "review_required",
        "review_reason", "rejection_code", "category_validator", "anomaly_score",
        "confidence", "inference_seconds", "worker_cache", "validation_seconds",
        "efficientad_seconds", "patchcore_seconds", "refiner_seconds",
        "primary_specialist", "decision_source", "route", "localization_source",
        "image_quality_state", "image_quality_message",
    ])
    for item in rows:
        writer.writerow([
            item.id, item.created_at.isoformat() if item.created_at else "",
            item.dataset_name or "", item.category or "", item.predicted_category or "",
            item.prediction or "", bool(item.result_valid), bool(item.review_required),
            item.review_reason or "", item.rejection_code or "", item.category_validator or "",
            item.anomaly_score if item.anomaly_score is not None else "",
            item.confidence if item.confidence is not None else "",
            item.inference_time if item.inference_time is not None else "", item.worker_cache or "",
            item.validation_seconds if item.validation_seconds is not None else "",
            item.efficientad_seconds if item.efficientad_seconds is not None else "",
            item.patchcore_seconds if item.patchcore_seconds is not None else "",
            item.refiner_seconds if item.refiner_seconds is not None else "",
            item.primary_specialist or "", item.decision_source or "", item.route or "",
            item.localization_source or "", item.image_quality_state or "",
            item.image_quality_message or "",
        ])
    payload = stream.getvalue().encode("utf-8")
    filename = f"evt-clip-v2-analytics-{range}-{now.date().isoformat()}.csv"
    return StreamingResponse(
        iter([payload]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
