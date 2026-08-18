from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.detection import router as detection_router
from app.api.reports import router as reports_router
from app.api.history import router as history_router
from app.api.datasets import router as datasets_router
from app.api.settings import router as settings_router
from app.api.admin import router as admin_router

__all__ = [
    "auth_router",
    "users_router",
    "detection_router",
    "reports_router",
    "history_router",
    "datasets_router",
    "settings_router",
    "admin_router"
]
