# EVT-CLIP: Vision-Language Anomaly Detection System (Vision4Text)

> **Live Application**: [https://vision4text.in](https://vision4text.in)

EVT-CLIP is an industrial vision-language anomaly detection and localization system deployed for production visual inspection across five core industrial categories (Bottle, Cable, Capsule, Metal Nut, Pill).

## High-Level Architecture

```
Browser (React SPA)
  └──> Vercel Frontend (vision4text.in)
        └──> Modal Backend / API (FastAPI Container)
              └──> EVT-CLIP Anomaly Inspection Pipeline (EfficientAD + PatchCore + Stage-2/Stage-3 Multi-Modal Refinement)
```

## Production Overview

- **Frontend**: High-performance React Single Page Application deployed on Vercel with responsive dark UI, live camera capture, animated pipeline telemetry, and role-based workflows.
- **Backend & Inference**: FastAPI containerized backend hosted on Modal CPU infrastructure with automated memory snapshotting, warm LRU model session cache, and streaming upload protection.
- **Fail-Closed Inspection**: Multi-stage validation ensuring out-of-distribution (OOD) and low-quality inputs are rejected before resource-intensive specialist inference.
- **Audit & Evidence Export**: Server-side PDF report generation and HMAC-SHA256 cryptographically signed evidence bundles.


## Fail-closed input safety

- Production supports only Bottle, Cable, Capsule, Metal Nut and Pill.
- Blank/clipped images are rejected by a conservative image-quality gate. Lower-confidence quality issues are review warnings, not fabricated defects.
- Wrong-category, unsupported and category-unconfirmed inputs are stopped **before category-specific specialists run**.
- Rejected inputs show a centered safety popup and return **no heatmap, mask or overlay**.
- The same invalid-evidence rule is enforced by the browser, asset API, PDF and signed evidence ZIP.
- Production threshold remains `0.267` unless a real benchmark gate explicitly passes; it is not user-editable.
- Browser graphics never invent defect circles, masks or scores.

## Long-term operations

- Server-side Dashboard analytics support Today / 7 Days / 30 Days / 1 Year / All Time.
- Selected analytics windows can be exported as server-generated CSV.
- Detection History and Reports are metadata-first and can progressively load older batches of 100 records.
- Visual assets are lazy-loaded only when needed.
- SQLite uses WAL, foreign keys, busy timeout and indexes aligned to long-running history/analytics queries.
- Admin can download a **consistent, integrity-checked SQLite backup** created with SQLite's backup API without stopping the app.
- Re-generating the same report/remarks reuses an existing valid PDF rather than endlessly duplicating files.

## Export reliability

- PDF is generated server-side.
- Evidence ZIP contains metadata JSON, PDF, allowed evidence, SHA-256 per-file hashes and an HMAC-SHA256 signature.
- Invalid/rejected inspections preserve the original input + rejection metadata but withhold derived AI visualizations.
- `tools/verify_evidence_bundle.py` verifies a downloaded evidence ZIP offline when supplied with the deployment evidence-signing secret.

## Security defaults

- Modal production disables public self-registration by default.
- Production refuses the built-in development JWT secret or a JWT secret shorter than 32 characters.
- API/health responses are no-store and security headers/CSP/HSTS are applied in production.
- Uploads are streaming-size-limited, decode-verified, pixel-limited and atomically persisted.
- Client scan/blob caches are immediately cleared on logout.

## Benchmark honesty and improvement path

The recorded unseen/LOCO benchmark is **not changed simply because code changed**.

- `evaluation/benchmark_postprocess_gate.py` searches threshold/component cleanup on calibration data only and promotes only after an untouched holdout passes the guard.
- `evaluation/benchmark_map_fusion_gate.py` can test Stage-2/Stage-3 map blends + post-processing on calibration data, then touch holdout once. The production blend path is dormant unless a passing gate explicitly recommends it.
- `evaluation/build_category_validation_centroids.py` builds the preferred exact five-category OpenCLIP reference cache when MVTec `train/good` images are available.

Until a real holdout rerun passes, the deployed model stays on the verified production behavior.

## Deployment

Read `DEPLOY_MODAL_CPU.md` and `DEPLOYMENT_CHECKLIST.md`.

The Modal image build compiles the included React source with Node 22, so Node/npm is not required on the Windows deployment laptop.


### Final submission simplification
OpenCV/YOLO hybrid anomaly evidence is disabled in the production runtime and hidden from the primary UI. OpenCV remains installed only for basic image I/O/resizing utilities used by the backend. The production anomaly decision/localization path is EfficientAD + PatchCore + Stage-2/Stage-3 EVT-CLIP.
