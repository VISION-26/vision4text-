from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime

from app.core.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True, default=1)
    threshold = Column(Float, nullable=False, default=0.267)
    model_name = Column(String(255), nullable=False, default="EVT-CLIP-V2")
    device = Column(String(50), nullable=False, default="cpu")
    batch_size = Column(Integer, nullable=False, default=1)
    auto_report = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Settings(threshold={self.threshold}, model_name='{self.model_name}', device='{self.device}')>"
