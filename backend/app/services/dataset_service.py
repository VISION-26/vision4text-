import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status

from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate


class DatasetService:
    @staticmethod
    async def create_dataset(db: AsyncSession, dataset_in: DatasetCreate) -> Dataset:
        stmt = select(Dataset).where(Dataset.name == dataset_in.name)
        res = await db.execute(stmt)
        if res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset with name '{dataset_in.name}' already exists."
            )
        
        dataset = Dataset(
            name=dataset_in.name,
            category=dataset_in.category,
            description=dataset_in.description,
            tags=json.dumps(dataset_in.tags),
            sample_count=dataset_in.sample_count or 0
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        return dataset

    @staticmethod
    async def get_datasets(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Dataset]:
        stmt = select(Dataset).offset(skip).limit(limit)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def get_categories(db: AsyncSession) -> List[str]:
        stmt = select(Dataset.category).distinct()
        res = await db.execute(stmt)
        categories = [r for r in res.scalars().all() if r]
        if not categories:
            categories = ["bottle", "cable", "capsule", "metal_nut", "pill"]
        return categories

    @staticmethod
    async def delete_dataset(db: AsyncSession, dataset_id: int) -> bool:
        stmt = select(Dataset).where(Dataset.id == dataset_id)
        res = await db.execute(stmt)
        dataset = res.scalars().first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found.")
            
        await db.delete(dataset)
        await db.commit()
        return True
