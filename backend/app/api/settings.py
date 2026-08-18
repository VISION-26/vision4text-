from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.user import User
from app.models.settings import Settings
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.history_service import HistoryService

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get(
    "",
    response_model=SettingsResponse,
    summary="Get application system settings",
    description="Retrieve the locked EVT-CLIP production calibration, CPU device, and report preference."
)
async def get_settings(
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Settings).where(Settings.id == 1)
    res = await db.execute(stmt)
    settings_obj = res.scalars().first()

    if not settings_obj:
        # Initialize default settings if absent
        settings_obj = Settings(id=1, threshold=0.267, model_name="EVT-CLIP-V2", device="cpu", batch_size=1, auto_report=True)
        db.add(settings_obj)
        await db.commit()
        await db.refresh(settings_obj)

    return settings_obj


@router.put(
    "",
    response_model=SettingsResponse,
    summary="Update system settings",
    description="Update permitted application preferences. Production model calibration remains locked."
)
async def update_settings(
    settings_in: SettingsUpdate,
    current_user: User = Depends(require_role(["Admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Settings).where(Settings.id == 1)
    res = await db.execute(stmt)
    settings_obj = res.scalars().first()

    if not settings_obj:
        settings_obj = Settings(id=1)
        db.add(settings_obj)

    requested = settings_in.model_dump(exclude_unset=True)
    # The deployed EVT-CLIP model is calibrated as one immutable production
    # profile. Only the report preference is mutable through this legacy route.
    update_data = {
        "threshold": 0.267,
        "model_name": "EVT-CLIP-V2",
        "device": "cpu",
        "batch_size": 1,
    }
    if "auto_report" in requested:
        update_data["auto_report"] = requested["auto_report"]
    for k, v in update_data.items():
        setattr(settings_obj, k, v)

    await db.commit()
    await db.refresh(settings_obj)

    await HistoryService.log_action(
        db, current_user.id, "UPDATE_SETTINGS", f"Updated system settings: {update_data}"
    )

    return settings_obj
