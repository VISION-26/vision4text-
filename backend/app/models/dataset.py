from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    sample_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}', category='{self.category}')>"
