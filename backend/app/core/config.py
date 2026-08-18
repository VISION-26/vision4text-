import json
import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EVT-CLIP"
    APP_VERSION: str = "2.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite+aiosqlite:///./evtclip.db"
    JWT_SECRET: str = "development-only-change-me-please-000000000000000000"
    EVIDENCE_SIGNING_SECRET: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "reports"
    MAX_UPLOAD_SIZE_MB: int = Field(default=20, ge=1, le=50)
    MAX_IMAGE_PIXELS: int = Field(default=40_000_000, ge=1_000_000, le=100_000_000)
    MIN_IMAGE_SIDE: int = Field(default=64, ge=16, le=512)
    ALLOWED_EXTENSIONS: set[str] = {"png", "jpg", "jpeg"}
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8000"]
    DEMO_MODE: bool = False
    MODEL_DIR: str = "/models/production"
    PRIMARY_MODEL: str = "evtclip_v2"
    SUPPORTED_CATEGORIES: set[str] = {"bottle", "cable", "capsule", "carpet", "grid", "hazelnut", "leather", "metal_nut", "pill", "screw", "tile", "toothbrush", "transistor", "wood", "zipper"}
    ML_CONFIDENCE_THRESHOLD: float = Field(default=0.267, ge=0, le=1)
    DOCS_ENABLED: bool = False
    ALLOW_PUBLIC_REGISTRATION: bool = True
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None
    ADMIN_NAME: str = "EVT-CLIP Administrator"
    MODAL_APP_NAME: str = "evt-clip-v2-production"
    MODAL_WORKER_FUNCTION: str = "infer_cpu"
    MODAL_WORKER_CLASS: str | None = None
    MODAL_WORKER_METHOD: str = "infer"
    MODAL_JOB_QUEUE: bool = False
    FRONTEND_DIST_DIR: str = "../frontend/dist"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, value):
        if isinstance(value, str):
            return json.loads(value) if value.startswith("[") else [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("SUPPORTED_CATEGORIES", mode="before")
    @classmethod
    def parse_categories(cls, value):
        if isinstance(value, str):
            return set(json.loads(value)) if value.startswith("[") else {item.strip() for item in value.split(",") if item.strip()}
        return value

    @property
    def BASE_DIR(self) -> str:
        return str(Path(__file__).resolve().parents[2])

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def _storage_path(self, configured: str) -> Path:
        candidate = Path(configured)
        return candidate if candidate.is_absolute() else Path(self.BASE_DIR, candidate)

    @property
    def abs_upload_dir(self) -> str:
        path = self._storage_path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @property
    def abs_report_dir(self) -> str:
        path = self._storage_path(self.REPORT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @property
    def abs_model_dir(self) -> str:
        return str(self._storage_path(self.MODEL_DIR))

    @property
    def frontend_dist_path(self) -> Path:
        path = Path(self.FRONTEND_DIST_DIR)
        return path if path.is_absolute() else Path(self.BASE_DIR, path).resolve()

    @property
    def trained_models_ready(self) -> bool:
        base = Path(self.abs_model_dir)
        required = [
            base / "deployment.ckpt",
            base / "model_registry.json",
            base / "stage2_product_profiles.json",
            base / "evtclip_runtime",
            base / "models",
        ]
        return all(path.exists() for path in required)


settings = Settings()
