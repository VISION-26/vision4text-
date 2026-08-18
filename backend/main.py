from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, text

from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
from app.api.examples import router as examples_router
from app.api.detection import router as detection_router
from app.api.history import router as history_router
from app.api.reports import router as reports_router
from app.api.settings import router as settings_router
from app.api.users import router as users_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.middleware.error_middleware import ErrorMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.models.user import User


async def _ensure_admin() -> None:
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        return
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))).scalars().first()
        if existing:
            return
        db.add(User(
            email=settings.ADMIN_EMAIL,
            full_name=settings.ADMIN_NAME,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            role="Admin",
            is_active=True,
        ))
        await db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.ENVIRONMENT.lower() == "production":
        if settings.DEMO_MODE:
            raise RuntimeError("DEMO_MODE is forbidden in production. Configure the verified CPU inference runtime.")
        if settings.JWT_SECRET.startswith("development-only-") or len(settings.JWT_SECRET) < 32:
            raise RuntimeError("Production requires a strong JWT_SECRET of at least 32 characters.")
    settings.abs_upload_dir
    settings.abs_report_dir
    await init_db()
    await _ensure_admin()
    if not settings.DEMO_MODE and not settings.trained_models_ready:
        # The web container in queued Modal mode intentionally does not mount the model volume.
        # The CPU worker owns /models/production instead.
        if not settings.MODAL_JOB_QUEUE:
            raise RuntimeError(f"Verified EVT-CLIP model bundle is missing at {settings.abs_model_dir}.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
    lifespan=lifespan,
)
app.add_middleware(ErrorMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(), geolocation=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self'; media-src 'self' blob:; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'",
    )
    if request.url.path.startswith(settings.API_V1_STR) or request.url.path == "/health":
        response.headers["Cache-Control"] = "no-store"
    if settings.ENVIRONMENT.lower() == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})


@app.get("/health", tags=["Health"])
async def health():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "database": False, "inference_mode": "modal_cpu_queue" if settings.MODAL_JOB_QUEUE else "local_cpu"})
    return {
        "status": "ready",
        "version": settings.APP_VERSION,
        "database": True,
        "device": "cpu",
        "inference_mode": "modal_cpu_queue" if settings.MODAL_JOB_QUEUE else ("demo" if settings.DEMO_MODE else "local_cpu"),
        "trained_models_ready": settings.trained_models_ready if not settings.MODAL_JOB_QUEUE else None,
        "worker_configured": bool(settings.MODAL_JOB_QUEUE),
        "supported_categories": sorted(settings.SUPPORTED_CATEGORIES),
    }


app.include_router(examples_router)


for router in (auth_router, users_router, detection_router, reports_router, history_router, datasets_router, settings_router, analytics_router, admin_router):
    app.include_router(router, prefix=settings.API_V1_STR)


# Modal builds the complete Vite dist directory into the web image. API routes
# above take precedence; every other browser route falls back to index.html for React Router.
FRONTEND_DIST = settings.frontend_dist_path


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    if not FRONTEND_DIST.is_dir():
        return JSONResponse(status_code=404, content={"detail": "Frontend build is not installed."})
    requested = (FRONTEND_DIST / full_path).resolve()
    try:
        requested.relative_to(FRONTEND_DIST.resolve())
    except ValueError:
        return JSONResponse(status_code=404, content={"detail": "Not found."})
    if full_path and requested.is_file():
        return FileResponse(requested)
    return FileResponse(FRONTEND_DIST / "index.html")
