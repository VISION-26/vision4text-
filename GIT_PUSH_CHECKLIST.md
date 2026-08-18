# Git Push Checklist

## Include
- `backend/`
- `frontend/`
- `evaluation/`
- `tests/`
- `tools/`
- `modal_deploy.py`
- Docker / Caddy / deployment files
- documentation and `.env.example`
- model manifests / hashes when they contain no secrets and are reasonably small

## Do not commit
- multi-GB `.ckpt`, `.pt`, `.pth`, `.safetensors` model files
- generated reports, uploads, SQLite databases
- `.env` or secrets
- `node_modules`, `dist`, virtual environments, caches
- Kaggle temporary outputs

Large verified model bundles should stay in Kaggle/Modal storage or Git LFS/release storage if you intentionally choose that workflow.

## Before push
```bash
python tools/validate_release.py
python -m compileall backend
cd frontend && npm ci && npm run build && cd ..
git status
git add .
git commit -m "Integrate benchmark-gated YOLO/OpenCV hybrid inspection branch"
git push origin main
```
