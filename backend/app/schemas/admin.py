from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class LogResponse(BaseModel):
    id: int
    level: str
    message: str
    module: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class LogListResponse(BaseModel):
    total: int
    items: List[LogResponse]


class SystemStatsResponse(BaseModel):
    total_users: int
    total_detections: int
    total_reports: int
    total_datasets: int
    normal_detections: int
    anomalous_detections: int
    average_inference_time_sec: float
    system_status: str


class SystemHealthResponse(BaseModel):
    status: str
    database_connected: bool
    upload_dir_writable: bool
    report_dir_writable: bool
    ml_model_loaded: bool
    pytorch_device: str
    memory_usage_mb: Optional[float] = None
    uptime_seconds: float
