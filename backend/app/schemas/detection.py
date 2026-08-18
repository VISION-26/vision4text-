from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DetectionRequest(BaseModel):
    image_path: str = Field(..., description="Path to an image previously uploaded through /upload")
    dataset_name: Optional[str] = "MVTec AD Industrial Inspection"
    category: str = "bottle"
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Legacy display field; production calibration is model-controlled.")


class UploadResponse(BaseModel):
    image_path: str
    filename: str
    size_bytes: int
    content_type: str
    message: str


class DetectionResponse(BaseModel):
    id: int
    user_id: int
    original_image_path: str
    heatmap_path: Optional[str] = None
    mask_path: Optional[str] = None
    overlay_path: Optional[str] = None
    preprocessed_path: Optional[str] = None
    efficientad_heatmap_path: Optional[str] = None
    patchcore_heatmap_path: Optional[str] = None
    stage2_heatmap_path: Optional[str] = None
    stage3_heatmap_path: Optional[str] = None
    classical_cv_heatmap_path: Optional[str] = None
    yolo_roi_mask_path: Optional[str] = None
    hybrid_heatmap_path: Optional[str] = None
    bbox_overlay_path: Optional[str] = None
    anomaly_score: float
    confidence: float
    prediction: str
    inference_time: float
    dataset_name: Optional[str] = None
    category: Optional[str] = None
    threshold: Optional[float] = None
    result_valid: bool = True
    review_required: bool = False
    review_reason: Optional[str] = None
    decision_source: Optional[str] = None
    route: Optional[str] = None
    localization_source: Optional[str] = None
    primary_specialist: Optional[str] = None
    predicted_category: Optional[str] = None
    category_validation_message: Optional[str] = None
    category_validator: Optional[str] = None
    rejection_code: Optional[str] = None
    worker_cache: Optional[str] = None
    validation_seconds: Optional[float] = None
    efficientad_seconds: Optional[float] = None
    patchcore_seconds: Optional[float] = None
    refiner_seconds: Optional[float] = None
    image_quality_state: Optional[str] = None
    image_quality_message: Optional[str] = None
    efficientad_image_score: Optional[float] = None
    patchcore_image_score: Optional[float] = None
    stage2_map_score: Optional[float] = None
    stage3_map_score: Optional[float] = None
    classical_cv_score: Optional[float] = None
    classical_cv_seconds: Optional[float] = None
    classical_cv_defect_hint: Optional[str] = None
    hybrid_mode: Optional[str] = None
    hybrid_applied: bool = False
    hybrid_map_score: Optional[float] = None
    yolo_roi_state: Optional[str] = None
    yolo_roi_confidence: Optional[float] = None
    yolo_roi_class: Optional[str] = None
    map_agreement: Optional[float] = None
    defect_area_pixels: Optional[int] = None
    defect_area_fraction: Optional[float] = None
    defect_component_count: Optional[int] = None
    defect_bbox_x: Optional[int] = None
    defect_bbox_y: Optional[int] = None
    defect_bbox_width: Optional[int] = None
    defect_bbox_height: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DetectionListResponse(BaseModel):
    total: int
    items: List[DetectionResponse]


class DetectionJobResponse(BaseModel):
    job_id: int
    call_id: str
    status: str
    detection: Optional[DetectionResponse] = None
    error: Optional[str] = None


class DetectionJobListItem(BaseModel):
    job_id: int
    call_id: str
    status: str
    category: str
    dataset_name: Optional[str] = None
    detection_id: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DetectionJobListResponse(BaseModel):
    total: int
    items: List[DetectionJobListItem]
