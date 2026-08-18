import asyncio
import os

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import User


async def main():
    try:
        import app.models
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
            async with AsyncSessionLocal() as db:
                existing = (await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))).scalars().first()
                if not existing:
                    db.add(User(email=settings.ADMIN_EMAIL, full_name=settings.ADMIN_NAME, hashed_password=get_password_hash(settings.ADMIN_PASSWORD), role="Admin", is_active=True))
                    await db.commit()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
