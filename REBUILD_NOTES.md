# EVT-CLIP V2 rebuild notes

This is the full original React/FastAPI application with the Together-style visual system, CPU-only Modal serving, inspection animation, persistent storage and production hardening. See `PRODUCTION_HARDENING_NOTES.md` for the final changes.

## Preserved pages

Dashboard, Detection, Camera, Reports, History, Datasets, Settings, Admin, Login and NotFound.

## Runtime boundary

Training notebooks remain reproducibility artifacts only; production uses the verified `/models/production` bundle. The web container does not need the model Volume. The CPU `InferenceWorker` owns model loading and returns real backend evidence through a queued job contract.

## Validation boundary

Static compilation/parsing/import/integrity checks can be completed in this build environment. Full model inference and Modal deployment require the user's existing 4.3+ GiB model Volume and must be smoke-tested after deployment. No benchmark is claimed to improve until its evaluation is actually rerun.
