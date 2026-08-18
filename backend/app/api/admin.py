import asyncio
import os
import sqlite3
import time
import uuid
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.config import settings
from app.core.database import engine, get_db
from app.models.dataset import Dataset
from app.models.detection import Detection
from app.models.log import Log
from app.models.report import Report
from app.models.user import User
from app.schemas.admin import LogListResponse, SystemHealthResponse, SystemStatsResponse
from app.services.history_service import HistoryService

router = APIRouter(prefix="/admin", tags=["Admin & System Metrics"])
START_TIME = time.time()


def _create_verified_sqlite_backup(source_path: str, backup_path: str) -> None:
    """Create and integrity-check a consistent SQLite snapshot off the event loop."""
    source = sqlite3.connect(source_path, timeout=30)
    target = sqlite3.connect(backup_path, timeout=30)
    try:
        source.backup(target, pages=256, sleep=0.01)
        target.commit()
    finally:
        target.close()
        source.close()

    verify = sqlite3.connect(backup_path, timeout=30)
    try:
        status_row = verify.execute("PRAGMA integrity_check").fetchone()
        if not status_row or str(status_row[0]).lower() != "ok":
            raise RuntimeError("Generated SQLite backup failed integrity_check.")
    finally:
        verify.close()


@router.get("/logs", response_model=LogListResponse, dependencies=[Depends(require_role(["Admin"]))])
async def get_logs(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    items = (await db.execute(select(Log).order_by(Log.timestamp.desc()).offset(skip).limit(limit))).scalars().all()
    total = (await db.execute(select(func.count(Log.id)))).scalar() or 0
    return LogListResponse(total=total, items=items)


@router.get("/statistics", response_model=SystemStatsResponse)
async def get_statistics(current_user: User = Depends(require_role(["Admin"])), db: AsyncSession = Depends(get_db)):
    users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    detections_count = (await db.execute(select(func.count(Detection.id)))).scalar() or 0
    reports_count = (await db.execute(select(func.count(Report.id)))).scalar() or 0
    datasets_count = (await db.execute(select(func.count(Dataset.id)))).scalar() or 0
    normal_count = (await db.execute(select(func.count(Detection.id)).where(Detection.prediction == "Normal"))).scalar() or 0
    anomalous_count = (await db.execute(select(func.count(Detection.id)).where(Detection.prediction == "Anomalous"))).scalar() or 0
    avg_inference = (await db.execute(select(func.avg(Detection.inference_time)))).scalar() or 0.0
    return SystemStatsResponse(
        total_users=users_count,
        total_detections=detections_count,
        total_reports=reports_count,
        total_datasets=datasets_count,
        normal_detections=normal_count,
        anomalous_detections=anomalous_count,
        average_inference_time_sec=round(float(avg_inference), 4),
        system_status="Operational",
    )


@router.get("/system-health", response_model=SystemHealthResponse)
async def get_system_health(current_user: User = Depends(require_role(["Admin"])), db: AsyncSession = Depends(get_db)):
    db_connected = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_connected = False
    upload_ok = os.access(settings.abs_upload_dir, os.W_OK)
    report_ok = os.access(settings.abs_report_dir, os.W_OK)
    mem_mb = round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 2) if psutil else 0.0
    status_str = "Healthy" if (db_connected and upload_ok and report_ok) else "Degraded"
    return SystemHealthResponse(
        status=status_str,
        database_connected=db_connected,
        upload_dir_writable=upload_ok,
        report_dir_writable=report_ok,
        ml_model_loaded=settings.MODAL_JOB_QUEUE or settings.DEMO_MODE or settings.trained_models_ready,
        pytorch_device="cpu",
        memory_usage_mb=mem_mb,
        uptime_seconds=round(time.time() - START_TIME, 2),
    )


@router.get("/backup/database")
async def download_database_backup(
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Create a consistent admin-only SQLite backup without stopping the app."""
    database_path = engine.url.database
    if not settings.DATABASE_URL.startswith("sqlite+") or not database_path:
        raise HTTPException(status_code=409, detail="Database backup endpoint is available only for the SQLite deployment.")
    database_candidate = Path(database_path)
    if not database_candidate.is_absolute():
        database_candidate = Path(settings.BASE_DIR, database_candidate)
    source_path = os.path.realpath(database_candidate)
    if not os.path.isfile(source_path):
        raise HTTPException(status_code=404, detail="SQLite database file is unavailable.")

    backup_name = f"evtclip-db-backup-{uuid.uuid4().hex[:10]}.sqlite3"
    backup_path = os.path.realpath(os.path.join(settings.abs_report_dir, backup_name))
    report_root = os.path.realpath(settings.abs_report_dir)
    if os.path.commonpath([backup_path, report_root]) != report_root:
        raise HTTPException(status_code=500, detail="Backup destination validation failed.")

    try:
        await asyncio.to_thread(_create_verified_sqlite_backup, source_path, backup_path)
    except Exception as error:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise HTTPException(status_code=500, detail=f"Database backup failed: {type(error).__name__}") from error

    await HistoryService.log_action(db, current_user.id, "BACKUP_DATABASE", "Downloaded a consistent SQLite metadata backup")
    return FileResponse(
        backup_path,
        media_type="application/vnd.sqlite3",
        filename=f"evt-clip-v2-database-{time.strftime('%Y%m%d-%H%M%S')}.sqlite3",
        background=BackgroundTask(lambda: os.path.exists(backup_path) and os.remove(backup_path)),
    )
