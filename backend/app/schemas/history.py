from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class HistoryResponse(BaseModel):
    id: int
    user_id: int
    action: str
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    total: int
    items: List[HistoryResponse]
