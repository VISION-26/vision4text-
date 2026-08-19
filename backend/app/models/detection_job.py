from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class DetectionJob(Base):
    __tablename__ = "detection_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    call_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = Column(String(1024), nullable=False)
    dataset_name = Column(String(255), nullable=True)
    category = Column(String(64), nullable=False)
    threshold = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="queued")
    error = Column(Text, nullable=True)
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
    detection = relationship("Detection")
