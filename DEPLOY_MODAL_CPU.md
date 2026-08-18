# EVT-CLIP V2 — High-speed CPU Modal deployment

The deployment contains two roles:

- `web`: React SPA + FastAPI + authentication + analytics + history + reports + SQLite/app-data.
- `InferenceWorker.infer`: CPU-only EVT-CLIP V2 inference.

## Existing prerequisites

- Modal CLI authenticated to the intended workspace/environment.
- Volume `evt-clip-v2-models` exists.
- Verified bundle exists at `/models/production` in that Volume.
- The package is extracted locally.

## 1. Modal Secret

Use a long random JWT secret, admin credentials, and preferably a separate evidence-signing secret:

```powershell
py -m modal secret create -e main evt-clip-v2-secrets `
  "JWT_SECRET=PASTE-A-LONG-RANDOM-SECRET" `
  "EVIDENCE_SIGNING_SECRET=PASTE-A-SECOND-LONG-RANDOM-SECRET" `
  "ADMIN_EMAIL=your-admin@email.com" `
  "ADMIN_PASSWORD=YOUR-STRONG-PASSWORD" `
  "ADMIN_NAME=EVT-CLIP Administrator"
```

If `evt-clip-v2-secrets` already exists, update/replace it only if you intentionally want to rotate credentials. If `EVIDENCE_SIGNING_SECRET` is omitted, the server domain-separates the JWT secret for evidence signatures; a dedicated secret is preferable.

## 2. Recommended category-reference cache

The worker automatically prefers:

```text
/models/production/category_validation_centroids.npz
```

If the file already exists, nothing is required. If it does not, the app still has a conservative OpenCLIP text fallback. For stronger Bottle/Cable/Capsule/Metal Nut/Pill mismatch detection, generate the compact cache with `evaluation/build_category_validation_centroids.py` on a machine/Kaggle session containing MVTec training images, then upload it to the model Volume and redeploy.

## 3. Deploy

From the extracted project directory:

```powershell
py -m modal deploy -e main .\modal_deploy.py
```

The first deployment creates a CPU Memory Snapshot after loading the reusable EVT/OpenCLIP core. Category specialists stay lazy and are cached as they are used.

## 4. Health test

```powershell
$URL = "PASTE-THE-MODAL-WEB-URL"
Invoke-RestMethod "$URL/health" | Format-List
```

Expected important fields:

```text
status            : ready
device            : cpu
inference_mode    : modal_cpu_queue
worker_configured : True
```

## 5. Production smoke-test order

1. Sign in.
2. Run a known-good supported sample with the correct category.
3. Run a known-defective supported sample with the correct category.
4. Select Bottle and upload a clearly different supported category such as Pill: the centered safety modal should reject/redirect the category and no invalid heatmap should be shown.
5. Upload a clearly unrelated image: it should be rejected when confidently out-of-scope. Category-unconfirmed inputs are also stopped before specialists and ask for a corrected input/category.
6. Try a blank/fully clipped image (hard reject) and a low-contrast/low-detail image (review warning when not blank).
7. Open Dashboard, test all time ranges and export CSV.
8. Open History and Reports; export both PDF and signed Evidence ZIP.
9. As Admin, download a consistent DB backup and run an integrity check locally if desired.
10. Reload the app and confirm persistence.
11. Run the same category again and compare timing: `worker_cache=warm_pair` should appear after the specialist pair is cached.

## Speed design

- 8 CPU cores, 32 GiB RAM.
- OpenCLIP/Stage-3 core loaded once per container lifecycle and snapshot-enabled.
- EfficientAD/PatchCore session objects are reused in an LRU cache.
- One heavy input per worker prevents memory/CPU oversubscription.
- Worker remains warm for up to 20 minutes after activity.
- Frontend uses queued jobs and 2-second polling, so inference is not constrained by a single long web request.

Do **not** enable `torch.compile` or change calibrated thresholds in production without a measured benchmark. Those changes can make one workload faster/better while regressing another.

## Important snapshot rule

Changing files in the model Volume does not itself mean the in-memory snapshot should be trusted. The worker records a lightweight model-manifest fingerprint and fails closed if restored deployment metadata differs. After updating checkpoints/manifests/category-centroid cache, redeploy so Modal creates a fresh snapshot.

## Production account/security defaults

Public self-registration is disabled by the Modal deployment. Production startup also fails if the default development JWT secret is still in use or if `JWT_SECRET` is shorter than 32 characters.

## Benchmark-gated experiments

The package includes post-processing and Stage-2/Stage-3 map-fusion gates under `evaluation/`. Do not set `EVT_STAGE3_BLEND_ALPHA`, `EVT_FINAL_THRESHOLD` or `EVT_MIN_COMPONENT_PIXELS` from guesswork; only apply an override produced by a passing real holdout gate.
