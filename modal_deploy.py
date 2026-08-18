"""Modal deployment for the hardened EVT-CLIP V2 CPU application.

Architecture
============
- `web`: React SPA + FastAPI + a single-writer SQLite/app-data Volume.
- `InferenceWorker`: one CPU-only model-serving container pool. The reusable
  EVT/OpenCLIP core is loaded during a Modal lifecycle hook and captured by a
  CPU Memory Snapshot; category specialist sessions are cached lazily in RAM.

The verified model bundle must already exist at /models/production inside the
Modal Volume `evt-clip-v2-models`.
"""
from pathlib import Path

import modal

APP_NAME = "evt-clip-v2-production"
MODEL_VOLUME_NAME = "evt-clip-v2-models"
DATA_VOLUME_NAME = "evt-clip-v2-app-data"
SECRET_NAME = "evt-clip-v2-secrets"
PROJECT_ROOT = Path(__file__).resolve().parent

app = modal.App(APP_NAME)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=False)
data_volume = modal.Volume.from_name(DATA_VOLUME_NAME, create_if_missing=True)
web_secret = modal.Secret.from_name(SECRET_NAME)

web_image = (
    modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12")
    .entrypoint([])
    .pip_install_from_requirements(PROJECT_ROOT / "backend" / "requirements-web.txt")
    .add_local_dir(
        PROJECT_ROOT / "frontend",
        remote_path="/build/frontend",
        copy=True,
        ignore=["node_modules/**", "dist/**"],
    )
    .run_commands(
        "cd /build/frontend && npm ci --no-audit --no-fund && npm run build",
        "mkdir -p /app/frontend && cp -a /build/frontend/dist /app/frontend/dist",
    )
    .add_local_dir(PROJECT_ROOT / "backend", remote_path="/app/backend", copy=True)
)

worker_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install(
        "torch==2.10.0",
        "torchvision==0.25.0",
        index_url="https://download.pytorch.org/whl/cpu",
    )
    .pip_install(
        "numpy==2.5.2",
        "scipy>=1.13,<2",
        "Pillow>=10,<13",
        "matplotlib>=3.9,<4",
        "anomalib==2.6.0",
        "open-clip-torch==3.3.0",
        "opencv-python-headless>=4.10,<5",
    )
    .add_local_dir(PROJECT_ROOT / "backend", remote_path="/app/backend", copy=True)
)


@app.cls(
    image=worker_image,
    volumes={"/models": model_volume.with_mount_options(read_only=True)},
    cpu=8.0,
    memory=32768,
    timeout=3600,
    startup_timeout=900,
    max_containers=1,
    scaledown_window=1200,
    retries=1,
    enable_memory_snapshot=True,
    env={
        "EVT_MODEL_ROOT": "/models/production",
        "EVT_FINAL_THRESHOLD": "0.267",
        "EVT_MIN_COMPONENT_PIXELS": "16",
        "EVT_CATEGORY_CENTROIDS": "/models/production/category_validation_centroids.npz",
        "EVT_CATEGORY_MISMATCH_MARGIN": "0.04",
        "EVT_OPEN_SET_MARGIN": "0.03",
        "EVT_SPECIALIST_CACHE_LIMIT": "4",
        "EVT_CPU_THREADS": "8",
        "EVT_HYBRID_CV_ENABLED": "false",
        "EVT_HYBRID_MODE": "off",
        "EVT_HYBRID_CV_ALPHA": "0.15",
        "EVT_YOLO_ENABLED": "false",
        "EVT_YOLO_MODEL_PATH": "/models/production/yolo/product_roi.pt",
        "EVT_YOLO_CONF": "0.25",
        "EVT_YOLO_DEVICE": "cpu",
        "OMP_NUM_THREADS": "8",
        "MKL_NUM_THREADS": "8",
        "OPENBLAS_NUM_THREADS": "8",
        "NUMEXPR_NUM_THREADS": "8",
        "OMP_DYNAMIC": "FALSE",
        "KMP_BLOCKTIME": "0",
        "PYTHONPATH": "/app/backend:/models/production",
        "CUDA_VISIBLE_DEVICES": "",
    },
)
class InferenceWorker:
    """Warm, snapshot-enabled CPU inference service."""

    @modal.enter(snap=True)
    def load_core(self):
        # Imports + OpenCLIP/Stage-3 initialization are expensive and reusable.
        from app.services.evtclip_worker import prepare_runtime

        info = prepare_runtime()
        print("EVT-CLIP CPU core ready for snapshot:", info)

    @modal.enter()
    def verify_after_restore(self):
        from app.services.evtclip_worker import after_restore_runtime

        info = after_restore_runtime()
        print("EVT-CLIP CPU snapshot restored and verified:", info)

    @modal.method()
    def infer(self, image_bytes: bytes, filename: str, category: str):
        from app.services.evtclip_worker import infer_image_bytes

        return infer_image_bytes(image_bytes, filename, category)

    @modal.method()
    def precheck(self, image_bytes: bytes, filename: str, category: str):
        from app.services.evtclip_worker import precheck_image_bytes

        return precheck_image_bytes(image_bytes, filename, category)


@app.function(
    image=web_image,
    secrets=[web_secret],
    volumes={
        "/app/backend/storage": data_volume,
        "/models": model_volume.with_mount_options(read_only=True),
    },
    cpu=2.0,
    memory=4096,
    timeout=300,
    startup_timeout=180,
    max_containers=1,
    scaledown_window=300,
    env={
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "DATABASE_URL": "sqlite+aiosqlite:////app/backend/storage/evtclip.sqlite3",
        "UPLOAD_DIR": "storage/uploads",
        "REPORT_DIR": "storage/reports",
        "MODEL_DIR": "/models/production",
        "EVT_EXAMPLE_ROOT": "/models/examples",
        "DEMO_MODE": "false",
        "MODAL_JOB_QUEUE": "true",
        "MODAL_APP_NAME": APP_NAME,
        "MODAL_WORKER_CLASS": "InferenceWorker",
        "MODAL_WORKER_METHOD": "infer",
        "FRONTEND_DIST_DIR": "/app/frontend/dist",
        "BACKEND_CORS_ORIGINS": "[]",
        "DOCS_ENABLED": "false",
        "ALLOW_PUBLIC_REGISTRATION": "false",
        "PYTHONPATH": "/app/backend",
    },
)
@modal.concurrent(max_inputs=10, target_inputs=4)
@modal.asgi_app()
def web():
    from main import app as fastapi_app

    return fastapi_app
