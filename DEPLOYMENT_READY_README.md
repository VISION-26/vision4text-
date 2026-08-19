# EVT CLIP Deployment Ready Release

This archive contains the fixed source tree for the EVT CLIP inspection application. The frontend is designed to deploy on Vercel, while the CPU inference backend remains deployed on Modal.

## What this release fixes

The frontend no longer performs a separate `/detect/precheck` request when an image is selected. The Run Inspection action is not blocked by a precheck state. Category safety validation remains inside the authoritative Modal inspection worker and is returned as part of the normal inspection result.

The inspection polling loop has a hard client timeout and request timeouts. A completed job is marked terminal before optional evidence assets are downloaded. The completion animation remains visible until the operator changes or resets the input.

Both Vercel configuration files route `/api/*`, `/example-assets/*`, and `/health` to the existing Modal service. The obsolete examiner demo login path and examiner or defense focused interface labels have been removed.

## Deployment target

The expected production targets are:

| Component | Target |
|---|---|
| Website | `https://vision4text.in` |
| Modal backend | `https://akshaynhcm--evt-clip-v2-production-web.modal.run` |
| Vercel project | `vision4text` |
| Modal app | `evt-clip-v2-production` |

Do not delete or replace the Modal model volume. The trained checkpoints are not included in this archive because Modal loads them from its configured model volume.

## Vercel deployment

Import this repository into Vercel with the repository root as the Root Directory. The root `vercel.json` is already configured for this layout. If the Vercel project is configured with `frontend` as its Root Directory, the equivalent `frontend/vercel.json` is also included.

Use these build settings when Vercel asks for them:

```text
Build Command: npm --prefix frontend ci --no-audit --no-fund && npm --prefix frontend run build
Output Directory: frontend/dist
Install Command: leave empty
```

Do not add a separate frontend API URL unless you intentionally change the source. The frontend uses same origin paths such as `/api/v1`, and Vercel rewrites those paths to Modal.

After deployment, force a new deployment and perform a hard refresh or open a private browser window. The previous production site was serving an older JavaScript bundle with the precheck loop and examiner UI.

## Modal deployment

The Modal service is already responding in the existing production environment. Redeploy the backend only if you intentionally need to replace the current Modal source. Preserve the existing model volume, Modal environment, and production endpoint.

The backend can be deployed from Windows using the existing project scripts or the documented Modal deployment instructions in `DEPLOY_MODAL_CPU.md`. Do not redeploy the backend merely to fix the old frontend precheck loop.

## Live verification

Run these checks after the Vercel deployment:

```cmd
curl.exe -i https://vision4text.in/health
curl.exe -I https://vision4text.in/example-assets/bottle/good
curl.exe -i https://vision4text.in/api/v1/datasets
```

Expected behavior:

| Check | Expected result |
|---|---|
| `/health` | JSON response containing `"status":"ready"`, not `index.html` |
| `/example-assets/bottle/good` | `200` with an image content type such as `image/png` |
| `/api/v1/datasets` without login | A backend response such as `401 Not authenticated`, proving the rewrite reaches Modal |

Then perform a functional test. Upload a bottle image, select `bottle`, and run one inspection. Next, select a deliberately mismatched category such as `metal_nut` and run the inspection. The application should submit one normal inspection job and return the Modal category safety result. It should not display `Checking product...`, wait for a separate precheck, or disable Run Inspection indefinitely.

## Release contents

This archive intentionally excludes `.git`, `node_modules`, frontend `dist`, Python bytecode caches, local logs, and environment secrets. Vercel and Modal install or load their required runtime components during deployment.

The source release commit is `9e41c5b fix(deploy): remove precheck blocker and repair Vercel routing`, based on the earlier terminal inspection fix commit `78cb62b`.
