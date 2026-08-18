from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.history import HistoryResponse, HistoryListResponse
from app.services.history_service import HistoryService
from app.core.auth import require_role

router = APIRouter(prefix="", tags=["System History"])


@router.get(
    "/history",
    response_model=HistoryListResponse,
    summary="Get user system activity history",
    description="Retrieve activity logs for the current user or system audit history."
)
async def list_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    owner_id = current_user.id if current_user.role != "Admin" else None
    items = await HistoryService.get_history(db, user_id=owner_id, skip=skip, limit=limit)
    total = await HistoryService.count_history(db, user_id=owner_id)
    return HistoryListResponse(total=total, items=items)


@router.get(
    "/history/{id}",
    response_model=HistoryResponse,
    summary="Get history entry by ID",
    description="Retrieve specific history log entry details."
)
async def get_history_by_id(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    entry = await HistoryService.get_by_id(db, id)
    if not entry or (current_user.role != "Admin" and entry.user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"History entry {id} not found.")
    return entry


@router.delete(
    "/history/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete history entry by ID",
    description="Delete history log record."
)
async def delete_history(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    entry = await HistoryService.get_by_id(db, id)
    if not entry or (current_user.role != "Admin" and entry.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="History entry not found.")
    await HistoryService.delete_history(db, id)
    return {"success": True, "message": f"History log entry {id} deleted successfully."}
