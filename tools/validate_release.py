#!/usr/bin/env python3
"""Dependency-light production release guard for EVT-CLIP.

This intentionally checks architecture/safety invariants that should never be
silently removed by a future UI or deployment edit. It complements the real
frontend build in CI; it is not a substitute for model benchmark evaluation.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        FAILURES.append(message)


def text(path: str) -> str:
    target = ROOT / path
    require(target.is_file(), f"missing required file: {path}")
    return target.read_text(encoding="utf-8") if target.is_file() else ""


# Python syntax: dependency-free AST parse of every shipped Python file.
python_files = sorted(p for p in ROOT.rglob("*.py") if "node_modules" not in p.parts)
for path in python_files:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        FAILURES.append(f"python syntax error: {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")

modal = text("modal_deploy.py")
worker = text("backend/app/services/evtclip_worker.py")
detection_api = text("backend/app/api/detection.py")
main = text("backend/main.py")
reports = text("backend/app/api/reports.py")
admin = text("backend/app/api/admin.py")
detection_ui = text("frontend/src/pages/Detection/Detection.jsx")
dashboard = text("frontend/src/pages/Dashboard/Dashboard.jsx")
context = text("frontend/src/context/DetectionContext.jsx")

# Deployment invariants.
require(not re.search(r"\bgpu\s*=", modal), "Modal deployment must remain CPU-only (gpu= found)")
require('"CUDA_VISIBLE_DEVICES": ""' in modal, "CPU worker must explicitly hide CUDA devices")
require('"DEMO_MODE": "false"' in modal, "production Modal web must force DEMO_MODE=false")
require('"ALLOW_PUBLIC_REGISTRATION": "false"' in modal, "public registration must remain disabled by default")
require("enable_memory_snapshot=True" in modal, "CPU model worker must retain Memory Snapshot startup optimization")
require("class InferenceWorker" in modal and "@modal.enter(snap=True)" in modal, "snapshot-enabled reusable worker class missing")
require('name="InferenceWorker"' not in modal, "Modal App.cls does not accept name=; Cls name comes from the Python class")
require("max_containers=1" in modal, "single-container safety/SQLite writer invariant missing")
require("read_only=True" in modal, "model Volume must remain read-only")

# Inference safety/speed invariants.
require("_specialist_sessions" in worker and "_SpecialistSession" in worker, "warm specialist cache missing")
require(
    ("input_category_state\"] in {\"invalid_category\", \"unsupported_input\"}" in worker)
    or (
        'if category_validation["input_category_state"] in {"invalid_category", "category_uncertain", "unsupported_input"}:' in worker
        and 'route": "input_rejected_before_specialists"' in worker
    ),
    "hard-reject category gate before specialists missing",
)
require(
    ("strong_portable_mismatch" in worker and "review_required = False" in worker)
    or (
        'valid = state == "valid"' in worker
        and 'state = "category_uncertain"' in worker
        and 'state = "invalid_category"' in worker
    ),
    "accepted-category policy or hard-mismatch guard missing",
)
require("unsupported_input" in worker and "invalid_category" in worker, "wrong/unsupported category states missing")
require("poor_quality_input" in worker, "image-quality hard rejection state missing")
require("PRIMARY_SPECIALIST" in worker, "verified category-specific decision routing missing")
require("EVT_STAGE3_BLEND_ALPHA" in worker, "benchmark-gated optional fusion hook missing")

# API fail-closed evidence and async queue invariants.
require("await method.spawn.aio" in detection_api or "await worker.spawn.aio" in detection_api,
        "Modal queue submission must be asynchronous inside FastAPI")
require('asset_name != "original" and not detection.result_valid' in detection_api,
        "invalid-result derived asset block missing")
require("base64.b64decode(encoded, validate=True)" in detection_api, "worker asset base64 validation missing")
require("os.replace(temporary, target)" in detection_api, "atomic worker asset persistence missing")
require('@router.get("/detect/jobs", response_model=DetectionJobListResponse)' in detection_api, "persistent job listing endpoint missing")
require('@router.post("/detect/jobs/{job_id}/cancel"' in detection_api, "job cancellation endpoint missing")
require('@router.post("/detect/jobs/{job_id}/retry"' in detection_api, "job retry endpoint missing")
require("JOB_TIMEOUT_SECONDS" in detection_api and 'status = "timed_out"' in detection_api, "queue timeout safeguard missing")

# Production auth/runtime invariants.
require("Production requires a strong JWT_SECRET" in main, "production JWT startup guard missing")
require("DEMO_MODE is forbidden in production" in main, "production demo-mode startup guard missing")
require("Cache-Control" in main and "Content-Security-Policy" in main, "HTTP security/no-cache headers missing")

# UI safety and operational UX invariants.
require(
    "Incorrect Product Category" in detection_ui
    or ("Product Category Mismatch" in detection_ui and "precheckModalOpen" in detection_ui),
    "centered wrong-category UI warning missing",
)
require("Unsupported Image" in detection_ui and "Image Quality Too Poor" in detection_ui,
        "unsupported/quality safety popup states missing")
require("Run as {labelCategory(result.predictedCategory)}" in detection_ui,
        "correct-category rerun action missing")
require("InspectionRunAnimation" in detection_ui, "Run Inspection animation missing")
for label in ("Today", "7 Days", "30 Days", "1 Year", "All Time"):
    require(label in dashboard, f"dashboard time range missing: {label}")
require("analytics/export.csv" in dashboard or "exportAnalyticsCsv" in dashboard,
        "dashboard server CSV export missing")
require("loadAssetsForDetection" in context, "metadata-first/lazy history asset loader missing")


# Overview and public-entry invariants.
overview = text("frontend/src/pages/Overview/Overview.jsx")
about = text("frontend/src/pages/About/About.jsx")
report_service = text("backend/app/services/report_service.py")
require(all(phrase in overview for phrase in ("Detect the anomaly.", "Show where it is.", "Keep the evidence.")), "public overview hero missing")
require("Inspection flow" in overview and "Evidence from one inspection" in overview, "overview flow/evidence sections missing")
require("evt-overview-pipeline-tracer" in overview and "framer-motion" in overview, "animated overview pipeline missing")
require("break-all" in detection_ui and "Worker cache" in detection_ui and "Decision source" in detection_ui, "runtime evidence wrapping guard missing")
require("Inspection workflow" in about and "Records and export" in about, "About operational sections missing")
require("Complete Model Evidence" in detection_ui and "Defect Analysis" in detection_ui, "complete model evidence/defect analysis UI missing")
require("bbox_overlay_path" in detection_api and "bbox_overlay" in worker, "mask-derived defect location image missing")
require("Model-stage evidence" in report_service and "Defect location from final mask" in report_service, "technical PDF evidence pages missing")
require("Research benchmark context" in report_service and "Published EVT-CLIP paper benchmark" in report_service, "research benchmark appendix missing from PDF")
require((ROOT / "docs/CONTENT_STYLE.md").is_file(), "project copy-style policy missing")
input_component = text("frontend/src/components/common/Input.jsx")
require("flex w-11 items-center justify-center" in input_component and "pl-11 pr-4" in input_component, "login/input icon alignment guard missing")
login_ui = text("frontend/src/pages/Login/Login.jsx")
require("vision-text-login-loop.mp4" in login_ui and "autoPlay" in login_ui and "playsInline" in login_ui, "project login walkthrough video missing")
require((ROOT / "frontend/public/vision-text-login-loop.mp4").is_file(), "login walkthrough video asset missing")

# Export/recovery invariants.
require("HMAC-SHA256" in reports or "hmac.new" in reports, "signed evidence ZIP support missing")
require("manifest.sha256.json" in reports, "evidence manifest missing")
require("/backup/database" in admin and "source.backup" in admin, "consistent SQLite admin backup missing")

# Required core page structure from the supplied application.
for page in ("Dashboard", "Detection", "Reports", "History", "Settings", "Admin", "Login"):
    candidates = list((ROOT / "frontend/src/pages").glob(f"{page}/{page}.jsx")) + list((ROOT / "frontend/src/pages").glob(f"{page}.jsx"))
    require(bool(candidates), f"required original page missing: {page}")
require((ROOT / "frontend/src/components/detection/CameraCapture.jsx").is_file(), "camera capture component missing")
require("CameraCapture" in detection_ui, "camera capture must remain connected to Detection workflow")
category_guide = text("frontend/src/components/detection/CategoryExampleGuide.jsx")
routes_ui = text("frontend/src/routes/index.jsx")
sidebar_ui = text("frontend/src/components/layout/Sidebar.jsx")
for category in ("bottle", "cable", "capsule", "carpet", "grid", "hazelnut", "leather", "metal_nut", "pill", "screw", "tile", "toothbrush", "transistor", "wood", "zipper"):
    require(category in category_guide, f"missing upload-example guidance for category: {category}")
require("CategoryExampleGuide" in detection_ui and "supported_categories" in detection_ui, "dynamic category example/registry integration missing")
require("/datasets" not in routes_ui and "/research" not in routes_ui and "/medical-research" not in routes_ui, "removed research/data routes returned")
require("Research & Data" not in sidebar_ui and "Research Evidence" not in sidebar_ui and "Medical Research" not in sidebar_ui and "Datasets" not in sidebar_ui, "removed research/data navigation returned")


# Copy quality: keep public/project prose concrete and free of the canned
# patterns checked by the local no-ai-slop-derived gate.
quality_gate = subprocess.run(
    [sys.executable, str(ROOT / "tools/content_quality_gate.py")],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
require(quality_gate.returncode == 0, quality_gate.stdout.strip() or quality_gate.stderr.strip() or "content quality gate failed")

frontend_check = subprocess.run(
    [sys.executable, str(ROOT / "tools/frontend_source_check.py")],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
require(frontend_check.returncode == 0, frontend_check.stdout.strip() or frontend_check.stderr.strip() or "frontend source check failed")

# package.json/package-lock.json root dependency contract.
try:
    package = json.loads(text("frontend/package.json"))
    lock = json.loads(text("frontend/package-lock.json"))
    lock_root = lock.get("packages", {}).get("", {})
    require(package.get("dependencies", {}) == lock_root.get("dependencies", {}), "package-lock dependency mismatch")
    require(package.get("devDependencies", {}) == lock_root.get("devDependencies", {}), "package-lock devDependency mismatch")
except json.JSONDecodeError as exc:
    FAILURES.append(f"frontend package JSON invalid: {exc}")

if FAILURES:
    print("EVT-CLIP RELEASE GUARD: FAIL")
    for item in FAILURES:
        print(" -", item)
    sys.exit(1)

print("EVT-CLIP RELEASE GUARD: PASS")
print(f"Python files parsed: {len(python_files)}")
print("CPU-only deployment, fail-closed validation, exports, backup and core UI invariants verified.")
