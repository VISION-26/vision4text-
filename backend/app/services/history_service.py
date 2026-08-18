from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.history import History


class HistoryService:
    @staticmethod
    async def log_action(db: AsyncSession, user_id: int, action: str, details: Optional[str] = None) -> History:
        entry = History(
            user_id=user_id,
            action=action,
            details=details
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def get_history(db: AsyncSession, user_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[History]:
        stmt = select(History)
        if user_id:
            stmt = stmt.where(History.user_id == user_id)
        stmt = stmt.order_by(History.timestamp.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        return res.scalars().all()


    @staticmethod
    async def count_history(db: AsyncSession, user_id: Optional[int] = None) -> int:
        stmt = select(func.count(History.id))
        if user_id:
            stmt = stmt.where(History.user_id == user_id)
        res = await db.execute(stmt)
        return int(res.scalar_one() or 0)

    @staticmethod
    async def get_by_id(db: AsyncSession, history_id: int) -> Optional[History]:
        stmt = select(History).where(History.id == history_id)
        res = await db.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def delete_history(db: AsyncSession, history_id: int) -> bool:
        stmt = select(History).where(History.id == history_id)
        res = await db.execute(stmt)
        entry = res.scalars().first()
        if not entry:
            raise HTTPException(status_code=404, detail="History log entry not found.")
        await db.delete(entry)
        await db.commit()
        return True
