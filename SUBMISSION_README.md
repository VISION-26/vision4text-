# EVT-CLIP Submission Build

This is the consolidated source package prepared for the final submission build.

## Live production scope

Bottle, Cable, Capsule, Metal Nut and Pill. The runtime keeps the existing EfficientAD/PatchCore routing and the original Stage-2/Stage-3 production path.

## Recommended live demo

1. Select **Metal Nut**.
2. Run one known-good sample and show NORMAL / clean localization.
3. Run one known-defective sample and show the heatmap, mask and overlay.
4. Select the wrong category for a prepared input and show the precheck/category safety rejection.

Do not make the only submission demo depend on a random phone-camera image. Real-camera appearance can differ substantially from MVTec.

## Frontend

```bash
cd frontend
npm ci
npm run build
```

For development: `npm run dev`.

## Backend

Install the appropriate requirements file for the target environment, configure the `.env` values from `.env.example`, then run the FastAPI service according to the deployment notes. Model files are intentionally not bundled into ordinary Git/source archives.

## Modal

See `DEPLOY_MODAL_CPU.md`, `DEPLOYMENT_CHECKLIST.md`, and `modal_deploy.py`. The deployment expects the verified model artifacts to exist in the configured Modal Volume.

## Validation

See `FINAL_VALIDATION.json`, `CURRENT_RELEASE_STATUS.md`, and `PATCH_PROVENANCE.md`.

## Research extension

The additional ten MVTec categories and the EfficientAD/PatchCore/PaDiM/FastFlow training work remain research/benchmark extension work. They are not presented as fully production-integrated in this submission build.


### Final submission simplification
OpenCV/YOLO hybrid anomaly evidence is disabled in the production runtime and hidden from the primary UI. OpenCV remains installed only for basic image I/O/resizing utilities used by the backend. The production anomaly decision/localization path is EfficientAD + PatchCore + Stage-2/Stage-3 EVT-CLIP.
