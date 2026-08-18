from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SettingsUpdate(BaseModel):
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_name: Optional[str] = None
    device: Optional[str] = Field(None, description="Production deployment is locked to cpu")
    batch_size: Optional[int] = Field(None, ge=1, le=128)
    auto_report: Optional[bool] = None


class SettingsResponse(BaseModel):
    id: int
    threshold: float
    model_name: str
    device: str
    batch_size: int
    auto_report: bool
    updated_at: datetime

    class Config:
        from_attributes = True
