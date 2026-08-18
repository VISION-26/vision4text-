import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(tags=["Example Assets"])

_ALLOWED_KINDS = {"good", "bad"}
_ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def _root() -> Path:
    return Path(os.environ.get("EVT_EXAMPLE_ROOT", "/models/examples"))


@router.get("/example-assets/{category}/{kind}", include_in_schema=False)
async def example_asset(category: str, kind: str):
    category = category.strip().lower()
    kind = kind.strip().lower()
    if category not in settings.SUPPORTED_CATEGORIES or kind not in _ALLOWED_KINDS:
        raise HTTPException(status_code=404, detail="Example not found.")

    folder = _root() / category
    for suffix in _ALLOWED_EXTENSIONS:
        candidate = folder / f"{kind}{suffix}"
        if candidate.is_file():
            media = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png" if suffix == ".png" else "image/webp" if suffix == ".webp" else "application/octet-stream"
            return FileResponse(candidate, media_type=media, headers={"Cache-Control": "public, max-age=3600"})

    raise HTTPException(status_code=404, detail=f"Real {kind} example is not installed for {category}.")
