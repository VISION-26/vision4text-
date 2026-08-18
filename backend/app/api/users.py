from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.services.history_service import HistoryService

router = APIRouter(prefix="/users", tags=["Users Management"])


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List all users",
    description="Retrieve list of registered users. Requires Admin or Researcher role.",
    dependencies=[Depends(require_role(["Admin", "Researcher"]))]
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    users = await UserService.get_all_users(db, skip=skip, limit=limit)
    return users


@router.get(
    "/{id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve detailed user profile by user ID. Requires Admin role.",
    dependencies=[Depends(require_role(["Admin"]))]
)
async def get_user(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    user = await UserService.get_by_id(db, id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {id} not found.")
    return user


@router.put(
    "/{id}",
    response_model=UserResponse,
    summary="Update user by ID",
    description="Update user account properties by ID. Requires Admin role.",
    dependencies=[Depends(require_role(["Admin"]))]
)
async def update_user(
    id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await UserService.update_user(db, id, user_in)
    await HistoryService.log_action(db, current_user.id, "ADMIN_UPDATE_USER", f"Admin updated user ID {id}")
    return user


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete user by ID",
    description="Delete user account by ID. Requires Admin role.",
    dependencies=[Depends(require_role(["Admin"]))]
)
async def delete_user(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot delete their own account.")
        
    await UserService.delete_user(db, id)
    await HistoryService.log_action(db, current_user.id, "ADMIN_DELETE_USER", f"Admin deleted user ID {id}")
    return {"success": True, "message": f"User ID {id} deleted successfully."}
