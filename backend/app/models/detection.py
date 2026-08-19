from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_image_path = Column(String(500), nullable=False)
    heatmap_path = Column(String(500), nullable=True)
    mask_path = Column(String(500), nullable=True)
    overlay_path = Column(String(500), nullable=True)
    preprocessed_path = Column(String(500), nullable=True)
    efficientad_heatmap_path = Column(String(500), nullable=True)
    patchcore_heatmap_path = Column(String(500), nullable=True)
    stage2_heatmap_path = Column(String(500), nullable=True)
    stage3_heatmap_path = Column(String(500), nullable=True)
    classical_cv_heatmap_path = Column(String(500), nullable=True)
    yolo_roi_mask_path = Column(String(500), nullable=True)
    hybrid_heatmap_path = Column(String(500), nullable=True)
    bbox_overlay_path = Column(String(500), nullable=True)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.0)
    prediction = Column(String(100), nullable=False, default="Normal")
    inference_time = Column(Float, nullable=False, default=0.0)
    dataset_name = Column(String(255), nullable=True, default="MVTec AD Industrial Inspection")
    category = Column(String(255), nullable=True)
    threshold = Column(Float, nullable=True)
    result_valid = Column(Boolean, nullable=False, default=True)
    review_required = Column(Boolean, nullable=False, default=False)
    review_reason = Column(String(255), nullable=True)
    decision_source = Column(String(255), nullable=True)
    route = Column(String(128), nullable=True)
    localization_source = Column(String(255), nullable=True)
    primary_specialist = Column(String(64), nullable=True)
    predicted_category = Column(String(64), nullable=True)
    category_validation_message = Column(String(512), nullable=True)
    category_validator = Column(String(255), nullable=True)
    rejection_code = Column(String(128), nullable=True)
    worker_cache = Column(String(64), nullable=True)
    validation_seconds = Column(Float, nullable=True)
    efficientad_seconds = Column(Float, nullable=True)
    patchcore_seconds = Column(Float, nullable=True)
    refiner_seconds = Column(Float, nullable=True)
    image_quality_state = Column(String(64), nullable=True)
    image_quality_message = Column(String(512), nullable=True)
    efficientad_image_score = Column(Float, nullable=True)
    patchcore_image_score = Column(Float, nullable=True)
    stage2_map_score = Column(Float, nullable=True)
    stage3_map_score = Column(Float, nullable=True)
    classical_cv_score = Column(Float, nullable=True)
    classical_cv_seconds = Column(Float, nullable=True)
    classical_cv_defect_hint = Column(String(255), nullable=True)
    hybrid_mode = Column(String(32), nullable=True)
    hybrid_applied = Column(Boolean, nullable=False, default=False)
    hybrid_map_score = Column(Float, nullable=True)
    yolo_roi_state = Column(String(64), nullable=True)
    yolo_roi_confidence = Column(Float, nullable=True)
    yolo_roi_class = Column(String(128), nullable=True)
    map_agreement = Column(Float, nullable=True)
    defect_area_pixels = Column(Integer, nullable=True)
    defect_area_fraction = Column(Float, nullable=True)
    defect_component_count = Column(Integer, nullable=True)
    defect_bbox_x = Column(Integer, nullable=True)
    defect_bbox_y = Column(Integer, nullable=True)
    defect_bbox_width = Column(Integer, nullable=True)
    defect_bbox_height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="detections")
    reports = relationship("Report", back_populates="detection", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Detection(id={self.id}, prediction='{self.prediction}', anomaly_score={self.anomaly_score})>"
