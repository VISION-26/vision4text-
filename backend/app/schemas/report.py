from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    detection_id: int
    remarks: Optional[str] = Field(None, description="Custom notes or comments to include in the PDF report")


class ReportResponse(BaseModel):
    id: int
    detection_id: int
    user_id: int
    pdf_path: str
    remarks: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    total: int
    items: List[ReportResponse]
