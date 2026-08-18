import logging
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger("evt_clip")
Base = declarative_base()

engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,
}
if not settings.DATABASE_URL.startswith("sqlite+"):
    engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

if settings.DATABASE_URL.startswith("sqlite+"):
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("Database session rollback: %s", exc)
            raise


async def init_db() -> None:
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.DATABASE_URL.startswith("sqlite+"):
            # Small additive migration layer for users who redeploy onto an
            # existing SQLite app-data volume created by an earlier build.
            additions = {
                "datasets": {"tags": "TEXT"},
                "detections": {
                    "result_valid": "BOOLEAN NOT NULL DEFAULT 1",
                    "review_required": "BOOLEAN NOT NULL DEFAULT 0",
                    "review_reason": "VARCHAR(255)",
                    "decision_source": "VARCHAR(255)",
                    "route": "VARCHAR(128)",
                    "localization_source": "VARCHAR(255)",
                    "primary_specialist": "VARCHAR(64)",
                    "predicted_category": "VARCHAR(64)",
                    "category_validation_message": "VARCHAR(512)",
                    "category_validator": "VARCHAR(255)",
                    "rejection_code": "VARCHAR(128)",
                    "worker_cache": "VARCHAR(64)",
                    "validation_seconds": "FLOAT",
                    "efficientad_seconds": "FLOAT",
                    "patchcore_seconds": "FLOAT",
                    "refiner_seconds": "FLOAT",
                    "image_quality_state": "VARCHAR(64)",
                    "image_quality_message": "VARCHAR(512)",
                    "preprocessed_path": "VARCHAR(500)",
                    "efficientad_heatmap_path": "VARCHAR(500)",
                    "patchcore_heatmap_path": "VARCHAR(500)",
                    "stage2_heatmap_path": "VARCHAR(500)",
                    "stage3_heatmap_path": "VARCHAR(500)",
                    "classical_cv_heatmap_path": "VARCHAR(500)",
                    "yolo_roi_mask_path": "VARCHAR(500)",
                    "hybrid_heatmap_path": "VARCHAR(500)",
                    "bbox_overlay_path": "VARCHAR(500)",
                    "efficientad_image_score": "FLOAT",
                    "patchcore_image_score": "FLOAT",
                    "stage2_map_score": "FLOAT",
                    "stage3_map_score": "FLOAT",
                    "classical_cv_score": "FLOAT",
                    "classical_cv_seconds": "FLOAT",
                    "classical_cv_defect_hint": "VARCHAR(255)",
                    "hybrid_mode": "VARCHAR(32)",
                    "hybrid_applied": "BOOLEAN NOT NULL DEFAULT 0",
                    "hybrid_map_score": "FLOAT",
                    "yolo_roi_state": "VARCHAR(64)",
                    "yolo_roi_confidence": "FLOAT",
                    "yolo_roi_class": "VARCHAR(128)",
                    "map_agreement": "FLOAT",
                    "defect_area_pixels": "INTEGER",
                    "defect_area_fraction": "FLOAT",
                    "defect_component_count": "INTEGER",
                    "defect_bbox_x": "INTEGER",
                    "defect_bbox_y": "INTEGER",
                    "defect_bbox_width": "INTEGER",
                    "defect_bbox_height": "INTEGER",
                },
            }
            for table, columns in additions.items():
                existing = {row[1] for row in (await conn.execute(text(f"PRAGMA table_info({table})"))).all()}
                for column, sql_type in columns.items():
                    if column not in existing:
                        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))

            # Explicit indexes for long-running installations. SQLite does not
            # automatically index foreign keys, and dashboard analytics filter
            # heavily by owner/time/category/validity.
            indexes = [
                "CREATE INDEX IF NOT EXISTS ix_detections_user_created ON detections(user_id, created_at)",
                "CREATE INDEX IF NOT EXISTS ix_detections_user_valid ON detections(user_id, result_valid)",
                "CREATE INDEX IF NOT EXISTS ix_detections_user_category ON detections(user_id, category)",
                "CREATE INDEX IF NOT EXISTS ix_reports_user_detection ON reports(user_id, detection_id)",
                "CREATE INDEX IF NOT EXISTS ix_detection_jobs_user_status ON detection_jobs(user_id, status)",
                "CREATE INDEX IF NOT EXISTS ix_logs_timestamp ON logs(timestamp)",
            ]
            for statement in indexes:
                await conn.execute(text(statement))

            # Normalize legacy valid detections from older builds. The portable
            # category validator previously marked low-margin disagreements as
            # review state, which produced false review states for correct
            # images. Keep hard rejections intact, but accept valid historical
            # detections and align their displayed category with the selected
            # inspection profile.
            await conn.execute(text("""
                UPDATE detections
                SET review_required = 0,
                    review_reason = NULL,
                    predicted_category = category,
                    category_validation_message = 'Category accepted using the selected inspection profile.'
                WHERE result_valid = 1
                  AND (
                    review_required = 1
                    OR review_reason IN ('category_uncertain', 'specialist_disagreement', 'image_quality_warning')
                  )
            """))
    logger.info("Database tables initialized, migrated, and production indexes verified.")
