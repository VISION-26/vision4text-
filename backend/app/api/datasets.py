from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.dataset import (
    DatasetCreate, DatasetResponse, CategoryListResponse
)
from app.services.dataset_service import DatasetService
from app.services.history_service import HistoryService

router = APIRouter(prefix="", tags=["Datasets"])


@router.get(
    "/datasets",
    response_model=List[DatasetResponse],
    summary="List all datasets",
    description="Retrieve registered dataset metadata used to organize EVT-CLIP inspections."
)
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await DatasetService.get_datasets(db, skip=skip, limit=limit)


@router.post(
    "/datasets",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new dataset entry",
    description="Register dataset metadata for inspection organization; this does not retrain the production model."
)
async def create_dataset(
    dataset_in: DatasetCreate,
    current_user: User = Depends(require_role(["Admin", "Researcher"])),
    db: AsyncSession = Depends(get_db)
):
    dataset = await DatasetService.create_dataset(db, dataset_in)
    await HistoryService.log_action(
        db, current_user.id, "CREATE_DATASET", f"Registered new dataset '{dataset.name}'"
    )
    return dataset


@router.delete(
    "/datasets/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete dataset by ID",
    description="Remove dataset entry by ID."
)
async def delete_dataset(
    id: int,
    current_user: User = Depends(require_role(["Admin", "Researcher"])),
    db: AsyncSession = Depends(get_db)
):
    await DatasetService.delete_dataset(db, id)
    await HistoryService.log_action(db, current_user.id, "DELETE_DATASET", f"Deleted dataset ID {id}")
    return {"success": True, "message": f"Dataset ID {id} deleted successfully."}


@router.get(
    "/dataset/categories",
    response_model=CategoryListResponse,
    summary="Get dataset categories",
    description="Retrieve available vision anomaly categories."
)
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    categories = await DatasetService.get_categories(db)
    return CategoryListResponse(categories=categories)
