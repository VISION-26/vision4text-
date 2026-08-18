# Production hardening summary — v2.1.0

## High-speed CPU inference

- Heavy worker is a reusable Modal `InferenceWorker` class.
- Snapshot lifecycle preloads the reusable EVT/OpenCLIP core and re-verifies lightweight model metadata after restore.
- EfficientAD/PatchCore model + Engine sessions are cached per category with a bounded LRU and one fresh-session retry on stale state.
- CPU/OpenMP thread budgets are controlled to avoid nested thread-pool oversubscription.
- Per-stage timings (`validation`, `EfficientAD`, `PatchCore`, `refiner`) and worker-cache state are persisted per inspection.
- One heavy input at a time protects RAM/CPU stability; requests queue instead of loading multiple model stacks concurrently.

## Input/category safety

- Image-quality gate hard-rejects only essentially blank/fully clipped inputs; softer lighting/contrast/detail issues become manual-review warnings.
- Exact OpenCLIP image-reference centroids are preferred when `/models/production/category_validation_centroids.npz` exists.
- Portable fallback uses an OpenCLIP prompt ensemble plus a conservative unsupported-image guard.
- Any category result other than `valid` is stopped before category-specific specialists.
- Centered UI popup explains incorrect category, unsupported input, quality rejection or category uncertainty.
- Rejected/invalid localization evidence is withheld at frontend, API, PDF and ZIP layers.

## Long-term dashboard/history

- Full-database server-side analytics: Today / 7 Days / 30 Days / 1 Year / All Time.
- Server-generated CSV export for the selected analytics window.
- History/Reports are metadata-first, lazy-load visual blobs and page older records in 100-item batches.
- SQLite query indexes cover user+date, validity, category, report lookup, job status and audit timestamp.
- Logout immediately revokes blob URLs and clears client history/dataset caches.

## Export/recovery

- Server-generated PDF with validity/routing/quality/timing metadata.
- Signed evidence ZIP with per-file SHA-256 and HMAC-SHA256 manifest signature.
- Offline evidence verifier rejects hash/signature/schema/extra-file tampering.
- Admin-only database backup uses SQLite's online backup API, runs off the async event loop, performs `PRAGMA integrity_check`, then deletes its temporary server copy after download.
- Existing same-remarks PDF reports are reused when the stored file is still valid.

## Security

- Production forbids demo inference.
- Production refuses the default/short JWT secret.
- Public registration is disabled by default in Modal.
- Security/no-cache headers and production HSTS are applied.
- Worker and utility package `__init__` files no longer eagerly import web/database/OpenCV dependencies.

## Unknown/LOCO benchmark

No new LOCO number is claimed in this build. Two evaluation gates are included:

1. `benchmark_postprocess_gate.py` — threshold + component cleanup.
2. `benchmark_map_fusion_gate.py` — Stage-2/Stage-3 blend + threshold + component cleanup.

Both select only on calibration data and require untouched holdout improvement with bounded per-category regression before producing a production recommendation. The live blend override is unset by default.


## Capsule/Pill portable-validator hotfix
- The text-only OpenCLIP fallback is now advisory for semantically adjacent Capsule/Pill cases.
- Only strong, well-separated fallback mismatches can hard-block before specialists.
- `category_uncertain` proceeds with the selected trained category and is always marked REVIEW REQUIRED.
- Exact image-reference centroid validation, when `category_validation_centroids.npz` is present, remains the preferred validator.
