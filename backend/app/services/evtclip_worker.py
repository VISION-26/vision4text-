"""High-reliability EVT-CLIP CPU production inference adapter.

Design goals:
- fail closed on unsupported or clearly mismatched product inputs;
- keep the verified category-specific decision policy unchanged;
- cache loaded specialist models inside a warm Modal container;
- avoid recreating Anomalib Engine/model objects on every inspection;
- expose timing/cache metadata for production diagnostics;
- keep browser-visible masks/heatmaps fully backend-generated.

The module is safe to import outside Modal. Heavy ML dependencies are imported
lazily so the web container does not need Torch/Anomalib.
"""
from __future__ import annotations

import base64
import gc
import io
import os
import tempfile
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

MODEL_ROOT = Path(os.environ.get("EVT_MODEL_ROOT", "/models/production"))
EXAMPLE_ROOT = Path(os.environ.get("EVT_EXAMPLE_ROOT", "/models/examples"))
FINAL_THRESHOLD = float(os.environ.get("EVT_FINAL_THRESHOLD", "0.267"))
MIN_COMPONENT_PIXELS = int(os.environ.get("EVT_MIN_COMPONENT_PIXELS", "16"))
CPU_THREADS = max(1, int(os.environ.get("EVT_CPU_THREADS", "8")))
SPECIALIST_CACHE_LIMIT = max(2, int(os.environ.get("EVT_SPECIALIST_CACHE_LIMIT", "4")))
CATEGORY_MISMATCH_MARGIN = float(os.environ.get("EVT_CATEGORY_MISMATCH_MARGIN", "0.04"))
OPEN_SET_MARGIN = float(os.environ.get("EVT_OPEN_SET_MARGIN", "0.08"))
HYBRID_CV_ENABLED = os.environ.get("EVT_HYBRID_CV_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
HYBRID_MODE = os.environ.get("EVT_HYBRID_MODE", "off").strip().lower()
if HYBRID_MODE not in {"off", "shadow", "localization"}:
    raise ValueError("EVT_HYBRID_MODE must be off, shadow, or localization")
HYBRID_CV_ALPHA = float(os.environ.get("EVT_HYBRID_CV_ALPHA", "0.15"))
if not 0.0 <= HYBRID_CV_ALPHA <= 0.5:
    raise ValueError("EVT_HYBRID_CV_ALPHA must be between 0 and 0.5")
PORTABLE_HARD_MISMATCH_MARGIN = float(os.environ.get("EVT_PORTABLE_HARD_MISMATCH_MARGIN", "0.25"))
PORTABLE_SELECTED_MIN_SCORE = float(os.environ.get("EVT_PORTABLE_SELECTED_MIN_SCORE", "0.15"))
PORTABLE_NEAR_NEIGHBOR_PAIRS = {frozenset(("capsule", "pill"))}
_stage3_blend_raw = os.environ.get("EVT_STAGE3_BLEND_ALPHA", "").strip()
STAGE3_BLEND_ALPHA = float(_stage3_blend_raw) if _stage3_blend_raw else None
if STAGE3_BLEND_ALPHA is not None and not 0.0 <= STAGE3_BLEND_ALPHA <= 1.0:
    raise ValueError("EVT_STAGE3_BLEND_ALPHA must be between 0 and 1 when configured")

CATEGORIES = ("bottle", "cable", "capsule", "metal_nut", "pill")
CATEGORY_NAMES = {
    "bottle": "Bottle",
    "cable": "Cable",
    "capsule": "Capsule",
    "metal_nut": "Metal Nut",
    "pill": "Pill",
}
PRIMARY_SPECIALIST = {
    "bottle": "efficientad",
    "cable": "patchcore",
    "capsule": "patchcore",
    "metal_nut": "patchcore",
    "pill": "efficientad",
}
CATEGORY_CENTROID_FILE = Path(
    os.environ.get("EVT_CATEGORY_CENTROIDS", str(MODEL_ROOT / "category_validation_centroids.npz"))
)

_runtime_lock = threading.RLock()
_specialist_lock = threading.RLock()
_pipeline = None
_category_text_features = None
_category_reference_features = None
_category_reference_available = None
_open_set_text_features = None
_category_centroids = None
_specialist_sessions: "OrderedDict[tuple[str, str], _SpecialistSession]" = OrderedDict()
_cpu_configured = False
_snapshot_manifest_fingerprint = None


def configure_cpu_runtime() -> None:
    """Configure a predictable CPU thread budget exactly once per container."""
    global _cpu_configured
    if _cpu_configured:
        return
    with _runtime_lock:
        if _cpu_configured:
            return
        # Avoid nested OpenMP/MKL thread pools fighting each other.
        os.environ.setdefault("OMP_NUM_THREADS", str(CPU_THREADS))
        os.environ.setdefault("MKL_NUM_THREADS", str(CPU_THREADS))
        os.environ.setdefault("OPENBLAS_NUM_THREADS", str(CPU_THREADS))
        os.environ.setdefault("NUMEXPR_NUM_THREADS", str(CPU_THREADS))
        os.environ.setdefault("OMP_DYNAMIC", "FALSE")
        os.environ.setdefault("KMP_BLOCKTIME", "0")
        import torch

        torch.set_grad_enabled(False)
        torch.set_num_threads(CPU_THREADS)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            # PyTorch allows this to be set only before inter-op work starts.
            pass
        _cpu_configured = True


def _load_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    with _runtime_lock:
        if _pipeline is not None:
            return _pipeline
        configure_cpu_runtime()
        if not MODEL_ROOT.is_dir():
            raise RuntimeError(f"Model root does not exist: {MODEL_ROOT}")
        import sys

        if str(MODEL_ROOT) not in sys.path:
            sys.path.insert(0, str(MODEL_ROOT))
        from evtclip_runtime.pipeline import EVTPipeline

        _pipeline = EVTPipeline(MODEL_ROOT)
        return _pipeline


def prepare_runtime() -> dict[str, Any]:
    """Warm the reusable core for Modal container startup/snapshotting.

    Specialist checkpoints remain lazy and are cached per category after their
    first use. Loading all ten specialists at boot would increase RAM and
    snapshot size unnecessarily.
    """
    started = time.perf_counter()
    current = _load_pipeline()
    current._load_refiner()
    _load_category_centroids()
    _ensure_category_text_features()
    # Pre-import lightweight post-processing/visualization modules into the
    # snapshot so the first real scan spends less time on Python import work.
    import matplotlib
    from scipy import ndimage as _ndimage  # noqa: F401
    _ = matplotlib.colormaps["turbo"]
    global _snapshot_manifest_fingerprint
    _snapshot_manifest_fingerprint = _manifest_fingerprint()
    if _snapshot_manifest_fingerprint is None:
        raise RuntimeError("Verified model deployment metadata is incomplete.")
    return {
        "status": "ready",
        "device": "cpu",
        "cpu_threads": CPU_THREADS,
        "centroid_validator": CATEGORY_CENTROID_FILE.is_file(),
        "startup_seconds": round(time.perf_counter() - started, 3),
    }



def _manifest_fingerprint() -> str | None:
    """Fingerprint lightweight deployment metadata, not multi-GB weight files."""
    import hashlib

    parts = []
    for name in ("model_manifest.json", "model_registry.json", "stage2_product_profiles.json"):
        path = MODEL_ROOT / name
        if not path.is_file():
            return None
        parts.append(name.encode("utf-8") + b"\0" + path.read_bytes())

    # The compact category-reference cache is also loaded into the snapshot.
    # Include its presence/content so adding or replacing the cache in the
    # Volume cannot silently leave an old in-memory validator active.
    if CATEGORY_CENTROID_FILE.is_file():
        parts.append(b"category_validation_centroids.npz\0" + CATEGORY_CENTROID_FILE.read_bytes())
    else:
        parts.append(b"category_validation_centroids.npz\0<absent>")

    digest = hashlib.sha256()
    for part in parts:
        digest.update(part)
    return digest.hexdigest()


def after_restore_runtime() -> dict[str, Any]:
    """Re-arm CPU threading and verify a restored snapshot matches its Volume.

    Modal Volume edits do not automatically invalidate Memory Snapshots. Failing
    closed here prevents a container restored from an old in-memory model state
    from silently serving after deployment metadata changed.
    """
    global _snapshot_manifest_fingerprint
    import torch

    torch.set_grad_enabled(False)
    torch.set_num_threads(CPU_THREADS)
    current = _manifest_fingerprint()
    if _snapshot_manifest_fingerprint and current != _snapshot_manifest_fingerprint:
        raise RuntimeError(
            "Model Volume metadata changed after the CPU Memory Snapshot was created. "
            "Redeploy EVT-CLIP so Modal creates a fresh snapshot."
        )
    if current is None:
        raise RuntimeError("Verified model deployment metadata is missing after snapshot restore.")
    return {"status": "ready", "manifest_fingerprint": current[:16], "cpu_threads": CPU_THREADS}

def _display_normalize(array: np.ndarray) -> np.ndarray:
    value = np.asarray(array, dtype=np.float32)
    finite = value[np.isfinite(value)]
    if finite.size == 0:
        return np.zeros(value.shape, dtype=np.float32)
    low = float(np.percentile(finite, 1.0))
    high = float(np.percentile(finite, 99.5))
    if high <= low:
        return np.zeros(value.shape, dtype=np.float32)
    return np.clip((value - low) / (high - low), 0.0, 1.0)


def _heatmap_image(array: np.ndarray) -> Image.Image:
    import matplotlib

    normalized = _display_normalize(array)
    rgba = matplotlib.colormaps["turbo"](normalized)
    return Image.fromarray((rgba[..., :3] * 255).astype(np.uint8), mode="RGB")


def _mask_image(mask: np.ndarray) -> Image.Image:
    return Image.fromarray((np.asarray(mask, dtype=np.uint8) * 255), mode="L")


def _overlay_image(original: Image.Image, anomaly_map: np.ndarray) -> Image.Image:
    normalized = _display_normalize(anomaly_map)
    heat = np.asarray(_heatmap_image(anomaly_map), dtype=np.float32)
    base = np.asarray(
        original.convert("RGB").resize((normalized.shape[1], normalized.shape[0])),
        dtype=np.float32,
    )
    alpha = (0.74 * normalized)[..., None]
    return Image.fromarray(
        np.clip(base * (1.0 - alpha) + heat * alpha, 0, 255).astype(np.uint8),
        mode="RGB",
    )


def _bbox_overlay_image(original: Image.Image, mask: np.ndarray, bbox: dict[str, int] | None) -> Image.Image:
    """Draw the accepted mask bounding box in the same coordinates as the final mask."""
    height, width = np.asarray(mask).shape[:2]
    canvas = original.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
    if not bbox:
        return canvas
    draw = ImageDraw.Draw(canvas)
    x0 = int(bbox["x"])
    y0 = int(bbox["y"])
    x1 = x0 + max(0, int(bbox["width"]) - 1)
    y1 = y0 + max(0, int(bbox["height"]) - 1)
    line_width = max(2, round(min(width, height) * 0.008))
    draw.rectangle((x0, y0, x1, y1), outline=(252, 76, 2), width=line_width)
    return canvas


def _encode_png(image: Image.Image | None) -> str | None:
    if image is None:
        return None
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=False)
    return base64.b64encode(stream.getvalue()).decode("ascii")


def _image_quality_check(image: Image.Image) -> dict[str, Any]:
    """Conservative camera/input-quality diagnostics.

    Only near-blank or almost fully clipped images are hard rejected. Less
    certain conditions become a review warning so camera-domain heuristics do
    not silently replace a calibrated anomaly benchmark.
    """
    sample = np.asarray(image.convert("RGB").resize((256, 256)), dtype=np.float32) / 255.0
    gray = 0.2126 * sample[..., 0] + 0.7152 * sample[..., 1] + 0.0722 * sample[..., 2]
    contrast = float(gray.std())
    mean_luma = float(gray.mean())
    dark_fraction = float((gray <= 0.02).mean())
    bright_fraction = float((gray >= 0.98).mean())
    gx = np.abs(np.diff(gray, axis=1)).mean() if gray.shape[1] > 1 else 0.0
    gy = np.abs(np.diff(gray, axis=0)).mean() if gray.shape[0] > 1 else 0.0
    detail_score = float(gx + gy)

    hard_reasons = []
    warnings = []
    if contrast < 0.008:
        hard_reasons.append("near_blank_or_uniform")
    if dark_fraction >= 0.985:
        hard_reasons.append("almost_fully_black")
    if bright_fraction >= 0.985:
        hard_reasons.append("almost_fully_white")

    if not hard_reasons:
        if contrast < 0.035:
            warnings.append("low_contrast")
        if mean_luma < 0.08 or dark_fraction > 0.80:
            warnings.append("very_dark")
        if mean_luma > 0.92 or bright_fraction > 0.80:
            warnings.append("very_bright")
        # Low edge energy can indicate blur, but this is intentionally advisory
        # because focus thresholds vary strongly by product texture and camera.
        if detail_score < 0.010:
            warnings.append("low_detail_or_blur")

    if hard_reasons:
        state = "rejected"
        message = (
            "Image quality is insufficient for a reliable inspection ("
            + ", ".join(reason.replace("_", " ") for reason in hard_reasons)
            + "). Capture a clear, normally exposed product image and try again."
        )
    elif warnings:
        state = "warning"
        message = (
            "Image quality warning: "
            + ", ".join(reason.replace("_", " ") for reason in warnings)
            + ". The model result is available but should be manually reviewed."
        )
    else:
        state = "ok"
        message = "Image quality checks passed."

    return {
        "image_quality_state": state,
        "image_quality_message": message,
        "image_quality_warnings": warnings if not hard_reasons else hard_reasons,
        "image_quality_contrast": round(contrast, 5),
        "image_quality_mean_luma": round(mean_luma, 5),
        "image_quality_detail_score": round(detail_score, 5),
        "image_quality_dark_fraction": round(dark_fraction, 5),
        "image_quality_bright_fraction": round(bright_fraction, 5),
    }


def _filter_small_components(mask: np.ndarray) -> np.ndarray:
    from scipy import ndimage

    binary = np.asarray(mask, dtype=np.uint8) > 0
    labels, count = ndimage.label(binary)
    if count == 0:
        return np.zeros(binary.shape, dtype=np.uint8)
    sizes = np.bincount(labels.ravel())
    keep = sizes >= MIN_COMPONENT_PIXELS
    keep[0] = False
    return keep[labels].astype(np.uint8)


def _mask_geometry(mask: np.ndarray) -> dict[str, Any]:
    """Measure the accepted binary mask in image coordinates."""
    from scipy import ndimage

    binary = np.asarray(mask, dtype=np.uint8) > 0
    pixels = int(binary.sum())
    if pixels == 0:
        return {
            "defect_area_pixels": 0,
            "defect_area_fraction": 0.0,
            "defect_component_count": 0,
            "defect_bbox": None,
        }

    ys, xs = np.where(binary)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    _labels, count = ndimage.label(binary)
    return {
        "defect_area_pixels": pixels,
        "defect_area_fraction": float(binary.mean()),
        "defect_component_count": int(count),
        "defect_bbox": {
            "x": x0,
            "y": y0,
            "width": x1 - x0 + 1,
            "height": y1 - y0 + 1,
        },
    }


def _scalar(value):
    if value is None:
        return None
    try:
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()
        array = np.asarray(value)
        if array.size == 0:
            return None
        return float(array.reshape(-1)[0])
    except (TypeError, ValueError):
        return None


@dataclass
class _SpecialistSession:
    model_name: str
    category: str
    model: Any
    engine: Any
    checkpoint: Path
    initialized: bool = False
    uses: int = 0

    def predict(self, image_path: Path):
        from anomalib.data import PredictDataset

        dataset = PredictDataset(path=image_path, image_size=(256, 256))
        ckpt_path = None if self.initialized else str(self.checkpoint)
        predictions = self.engine.predict(
            model=self.model,
            dataset=dataset,
            ckpt_path=ckpt_path,
            return_predictions=True,
        )
        if not predictions:
            raise RuntimeError(f"{self.model_name} returned no prediction")
        self.initialized = True
        self.uses += 1
        try:
            self.model.eval()
        except Exception:
            pass
        item = predictions[0]
        anomaly_map = item.anomaly_map.detach().cpu().numpy().squeeze().astype(np.float32)
        image_score = _scalar(getattr(item, "pred_score", None))
        image_label_value = _scalar(getattr(item, "pred_label", None))
        image_label = None if image_label_value is None else bool(image_label_value >= 0.5)
        del predictions
        return anomaly_map, image_score, image_label


def _create_specialist_session(model_name: str, category: str) -> _SpecialistSession:
    from anomalib.engine import Engine
    from anomalib.models import EfficientAd, Patchcore

    current = _load_pipeline()
    checkpoint = current.root / "models" / model_name / category / "model.ckpt"
    if not checkpoint.is_file():
        raise RuntimeError(f"Missing {model_name}/{category} checkpoint")
    model = EfficientAd() if model_name == "efficientad" else Patchcore()
    engine = Engine(accelerator="cpu", devices=1, logger=False, enable_progress_bar=False)
    return _SpecialistSession(model_name, category, model, engine, checkpoint)


def _evict_specialist_if_needed() -> None:
    while len(_specialist_sessions) > SPECIALIST_CACHE_LIMIT:
        _key, session = _specialist_sessions.popitem(last=False)
        try:
            del session.model
            del session.engine
        except Exception:
            pass
        gc.collect()


def _specialist_prediction(model_name: str, category: str, image_path: Path):
    """Predict with a warm LRU session; reload safely if a cached session breaks."""
    key = (model_name, category)
    cache_hit = False
    load_started = time.perf_counter()
    with _specialist_lock:
        session = _specialist_sessions.get(key)
        if session is None:
            session = _create_specialist_session(model_name, category)
            _specialist_sessions[key] = session
            _evict_specialist_if_needed()
        else:
            cache_hit = session.initialized
            _specialist_sessions.move_to_end(key)

        try:
            result = session.predict(image_path)
        except Exception:
            # Fail-safe recovery: one fresh session retry handles stale Lightning
            # trainer state without requiring the whole Modal container to die.
            _specialist_sessions.pop(key, None)
            gc.collect()
            session = _create_specialist_session(model_name, category)
            _specialist_sessions[key] = session
            _evict_specialist_if_needed()
            cache_hit = False
            result = session.predict(image_path)

    return (*result, cache_hit, round(time.perf_counter() - load_started, 4))


def _load_category_centroids() -> dict[str, np.ndarray] | None:
    global _category_centroids
    if _category_centroids is not None:
        return _category_centroids
    if not CATEGORY_CENTROID_FILE.is_file():
        return None
    cached = np.load(CATEGORY_CENTROID_FILE)
    if not all(category in cached.files for category in CATEGORIES):
        return None
    _category_centroids = {
        category: cached[category].astype(np.float32) for category in CATEGORIES
    }
    return _category_centroids


def _ensure_category_text_features():
    """Create portable zero-shot text references for all 15 supported products.

    Reference-image centroids remain authoritative for the original five when
    available. These text references are the fail-closed safety layer for the
    newly trained ten and for obvious non-product/OOD inputs.
    """
    global _category_text_features, _open_set_text_features
    if _category_text_features is not None and _open_set_text_features is not None:
        return

    current = _load_pipeline()
    import torch
    import torch.nn.functional as functional

    supported_prompt_groups = {
        "bottle": [
            "a photograph of a bottle",
            "an industrial inspection photo of one bottle",
            "a product photo of a bottle with a body and neck",
            "a factory quality-control image of a bottle",
        ],
        "cable": [
            "a photograph of an electrical cable",
            "an industrial inspection photo of one cable",
            "a product photo of an insulated wire or cable",
            "a factory quality-control image of a cable",
        ],
        "capsule": [
            "a photograph of a medicine capsule",
            "an industrial inspection photo of a two-piece capsule",
            "a product photo of a gelatin capsule shell",
            "a factory quality-control image of a capsule",
        ],
        "carpet": [
            "a close-up photograph of carpet texture",
            "an industrial inspection photo of carpet fabric",
            "a flat carpet surface with visible fibers",
            "a factory quality-control image of carpet material",
        ],
        "grid": [
            "a close-up photograph of a regular grid texture",
            "an industrial inspection photo of a repeating grid pattern",
            "a product surface with regular square grid lines",
            "a factory quality-control image of a grid material",
        ],
        "hazelnut": [
            "a photograph of a single hazelnut",
            "an industrial inspection photo of a hazelnut shell",
            "a product photo of one hazelnut",
            "a factory quality-control image of a hazelnut",
        ],
        "leather": [
            "a close-up photograph of leather texture",
            "an industrial inspection photo of a leather surface",
            "a flat leather material with visible texture",
            "a factory quality-control image of leather",
        ],
        "metal_nut": [
            "a photograph of a metal hex nut",
            "an industrial inspection photo of a threaded metal nut",
            "a product photo of a metallic fastening nut",
            "a factory quality-control image of a metal nut",
        ],
        "pill": [
            "a photograph of a solid pharmaceutical pill",
            "an industrial inspection photo of one medicine tablet",
            "a product photo of a round or oval tablet",
            "a factory quality-control image of a pill",
        ],
        "screw": [
            "a photograph of a metal screw",
            "an industrial inspection photo of one screw",
            "a product photo of a threaded screw with head and shaft",
            "a factory quality-control image of a screw",
        ],
        "tile": [
            "a close-up photograph of a tile surface",
            "an industrial inspection photo of a ceramic tile",
            "a flat tile face with visible surface texture",
            "a factory quality-control image of a tile",
        ],
        "toothbrush": [
            "a photograph of a toothbrush",
            "an industrial inspection photo of a toothbrush head and bristles",
            "a product photo of one toothbrush",
            "a factory quality-control image of a toothbrush",
        ],
        "transistor": [
            "a photograph of an electronic transistor component",
            "an industrial inspection photo of a transistor with metal leads",
            "a product photo of one transistor component",
            "a factory quality-control image of a transistor",
        ],
        "wood": [
            "a close-up photograph of a wood surface with grain",
            "an industrial inspection photo of flat wood texture",
            "a wooden material surface with visible grain",
            "a factory quality-control image of wood",
        ],
        "zipper": [
            "a close-up photograph of a zipper",
            "an industrial inspection photo of zipper teeth and fabric",
            "a product photo of a zipper with two rows of teeth",
            "a factory quality-control image of a zipper",
        ],
    }

    # Strong negative prompts make unrelated uploads fail closed before anomaly
    # specialists can generate meaningless full-frame masks.
    unsupported_prompts = [
        "a selfie or webcam photograph of a person",
        "a portrait photograph of a human face",
        "a photograph of a person standing or sitting in a room",
        "a photograph of an animal",
        "a bedroom, office, or indoor room scene",
        "a landscape or outdoor scene",
        "a document or page of text",
        "a computer screen or phone screen",
        "a vehicle",
        "food on a plate",
        "furniture in a room",
        "clothing worn by a person",
        "a plant or flower",
        "a building or street",
        "a random household scene",
    ]

    with torch.inference_mode():
        if _category_text_features is None:
            flattened = [
                prompt
                for category in CATEGORIES
                for prompt in supported_prompt_groups[category]
            ]
            tokens = current.tokenizer(flattened).to(current.device)
            encoded = functional.normalize(current.clip.encode_text(tokens).float(), dim=-1)
            group_size = len(supported_prompt_groups[CATEGORIES[0]])
            grouped = encoded.reshape(len(CATEGORIES), group_size, -1).mean(dim=1)
            _category_text_features = functional.normalize(grouped, dim=-1)

        if _open_set_text_features is None:
            tokens = current.tokenizer(unsupported_prompts).to(current.device)
            _open_set_text_features = functional.normalize(
                current.clip.encode_text(tokens).float(), dim=-1
            )


def _ensure_category_reference_features():
    """Encode real installed GOOD/BAD MVTec samples for all supported categories.

    These are not anomaly-training inputs and do not change the anomaly models.
    They are only a lightweight category-safety reference so a transistor photo
    is not silently accepted as wood (or similar cross-product mistakes).
    """
    global _category_reference_features, _category_reference_available
    if _category_reference_features is not None:
        return

    current = _load_pipeline()
    import torch
    import torch.nn.functional as functional

    # Text features are also the fallback when a reference asset is missing.
    _ensure_category_text_features()

    refs = []
    available = {}
    extensions = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")

    with torch.inference_mode():
        for index, category in enumerate(CATEGORIES):
            encoded_images = []
            category_dir = EXAMPLE_ROOT / category
            for kind in ("good", "bad"):
                candidate = None
                for ext in extensions:
                    path = category_dir / f"{kind}{ext}"
                    if path.is_file():
                        candidate = path
                        break
                if candidate is None:
                    continue
                try:
                    image = Image.open(candidate).convert("RGB")
                    tensor = current.preprocess(image).unsqueeze(0).to(current.device)
                    feature = functional.normalize(current.clip.encode_image(tensor).float(), dim=-1)[0]
                    encoded_images.append(feature)
                except Exception:
                    continue

            if encoded_images:
                stacked = torch.stack(encoded_images, dim=0).mean(dim=0, keepdim=True)
                refs.append(functional.normalize(stacked, dim=-1)[0])
                available[category] = len(encoded_images)
            else:
                # Fail-soft reference fallback: use the already-created text
                # prototype for this category, but record that no image ref exists.
                refs.append(_category_text_features[index])
                available[category] = 0

        _category_reference_features = functional.normalize(torch.stack(refs, dim=0), dim=-1)
        _category_reference_available = available


def _category_validation(image_path: Path, selected_category: str) -> dict[str, Any]:
    """Hybrid category/OOD gate for the configured production categories.

    Priority:
      1) reject obvious non-product/OOD uploads,
      2) compare the upload against real per-category MVTec reference images,
      3) blend that with 15-way OpenCLIP text semantics,
      4) use legacy centroids as an extra tie-breaker for the original five.

    Strong mismatches fail closed before anomaly specialists run. This restores
    the previous safety behavior where a wrong selected product does not produce
    an accepted anomaly heatmap.
    """
    current = _load_pipeline()
    import torch
    import torch.nn.functional as functional

    current._load_refiner()
    _ensure_category_text_features()
    _ensure_category_reference_features()

    image = current.preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(current.device)
    with torch.inference_mode():
        feature = functional.normalize(current.clip.encode_image(image).float(), dim=-1)
        text_raw = (feature @ _category_text_features.T)[0]
        ref_raw = (feature @ _category_reference_features.T)[0]
        unsupported_raw = (feature @ _open_set_text_features.T)[0]

        text_prob = torch.softmax(18.0 * text_raw, dim=-1)
        ref_prob = torch.softmax(30.0 * ref_raw, dim=-1)
        combined = 0.72 * ref_prob + 0.28 * text_prob

    combined_scores = {
        category: float(combined[index])
        for index, category in enumerate(CATEGORIES)
    }
    ranking = sorted(combined_scores, key=combined_scores.get, reverse=True)
    predicted = ranking[0]
    top_score = combined_scores[ranking[0]]
    second_score = combined_scores[ranking[1]] if len(ranking) > 1 else 0.0
    margin = top_score - second_score
    selected_score = combined_scores[selected_category]

    supported_best = float(torch.maximum(text_raw.max(), ref_raw.max()))
    unsupported_best = float(unsupported_raw.max())
    open_set_margin = unsupported_best - supported_best
    unsupported_index = int(unsupported_raw.argmax().item())
    unsupported_labels = [
        "person_or_webcam", "human_face", "person_in_room", "animal", "indoor_room",
        "outdoor_scene", "document", "screen", "vehicle", "food", "furniture",
        "clothing_person", "plant", "building_street", "household_scene",
    ]
    top_unsupported = unsupported_labels[unsupported_index]

    critical_negative = (
        top_unsupported in {
            "person_or_webcam", "human_face", "person_in_room", "animal",
            "indoor_room", "document", "screen",
        }
        and unsupported_best >= supported_best - 0.02
    )
    unsupported = open_set_margin >= OPEN_SET_MARGIN or critical_negative

    # Extra legacy-centroid cross-check when available. It is a tie-breaker,
    # not the only 15-way classifier.
    centroid_predicted = None
    centroid_margin = None
    centroids = _load_category_centroids()
    legacy_categories = tuple(VALIDATION_CATEGORIES) if 'VALIDATION_CATEGORIES' in globals() else tuple(LEGACY_EVT_CATEGORIES) if 'LEGACY_EVT_CATEGORIES' in globals() else tuple()
    if selected_category in legacy_categories and centroids is not None:
        feature_np = feature[0].cpu().numpy().astype(np.float32)
        similarities = {
            category: float(np.dot(feature_np, centroids[category]))
            for category in legacy_categories
            if category in centroids
        }
        if len(similarities) >= 2:
            legacy_rank = sorted(similarities, key=similarities.get, reverse=True)
            centroid_predicted = legacy_rank[0]
            centroid_margin = similarities[legacy_rank[0]] - similarities[legacy_rank[1]]

    near_neighbor = frozenset((predicted, selected_category)) in PORTABLE_NEAR_NEIGHBOR_PAIRS

    # A real-reference mismatch is intentionally easier to trigger than the old
    # text-only gate because the installed samples provide direct category cues.
    strong_mismatch = (
        predicted != selected_category
        and not near_neighbor
        and (
            margin >= 0.075
            or selected_score <= 0.12
            or (
                centroid_predicted is not None
                and centroid_predicted != selected_category
                and centroid_margin is not None
                and centroid_margin >= CATEGORY_MISMATCH_MARGIN
            )
        )
    )

    weak_mismatch = (
        predicted != selected_category
        and not near_neighbor
        and margin >= 0.025
    )

    if unsupported:
        state = "unsupported_input"
        message = (
            "This upload appears outside the supported industrial product set "
            f"(strongest non-product cue: {top_unsupported.replace('_', ' ')}). "
            "Inspection was stopped before anomaly specialists ran."
        )
    elif strong_mismatch:
        state = "invalid_category"
        message = (
            f"The selected profile is {CATEGORY_NAMES[selected_category]}, but the image is most "
            f"consistent with {CATEGORY_NAMES[predicted]}. Choose the matching category and retry."
        )
    elif weak_mismatch:
        state = "category_uncertain"
        message = (
            f"The selected profile is {CATEGORY_NAMES[selected_category]}, while the closest reference "
            f"is {CATEGORY_NAMES[predicted]}. The category match is uncertain; do not accept the result "
            "without operator review."
        )
    else:
        state = "valid"
        predicted = selected_category
        message = f"Category accepted as {CATEGORY_NAMES[selected_category]}."

    # Strong invalid/OOD fail closed. Weak uncertainty is also blocked so the
    # UI can show the safety modal rather than silently running a wrong model.
    valid = state == "valid"

    return {
        "input_category_state": state,
        "input_category_valid": valid,
        "selected_category": selected_category,
        "predicted_category": predicted,
        "category_probability": combined_scores.get(predicted),
        "selected_category_probability": selected_score,
        "category_margin": float(margin),
        "category_probabilities": combined_scores,
        "category_supported_score": supported_best,
        "category_unsupported_score": unsupported_best,
        "category_open_set_margin": open_set_margin,
        "category_top_unsupported": top_unsupported,
        "category_reference_counts": dict(_category_reference_available or {}),
        "category_validation_message": message,
        "category_validator": "real_mvtec_reference+openclip_15category+open_set_guard",
    }

def _rejected_payload(
    category_validation: dict[str, Any],
    started: float,
    validation_seconds: float,
) -> dict[str, Any]:
    """Return a fail-closed result before wrong specialists generate a heatmap."""
    state = category_validation["input_category_state"]
    metadata = {
        **category_validation,
        "status": "rejected",
        "rejection_code": state,
        "result_valid": False,
        "review_required": False,
        "review_reason": state,
        "decision": "invalid_input",
        "raw_anomaly_decision": "invalid",
        "anomalous": False,
        "score": 0.0,
        "decision_source": "image_quality_gate" if state == "poor_quality_input" else "category_safety_gate",
        "primary_specialist": None,
        "route": "input_rejected_before_specialists",
        "confidence": 0.0,
        "map_agreement": None,
        "fallback_reason": None,
        "localization_source": None,
        "defect_area_pixels": 0,
        "defect_area_fraction": 0.0,
        "efficientad_image_score": None,
        "efficientad_image_label": None,
        "patchcore_image_score": None,
        "patchcore_image_label": None,
        "stage2_map_score": None,
        "stage3_map_score": None,
        "classical_cv_score": None,
        "classical_cv_seconds": 0.0,
        "classical_cv_defect_hint": None,
        "hybrid_mode": HYBRID_MODE,
        "hybrid_applied": False,
        "hybrid_map_score": None,
        "yolo_roi_state": "not_run",
        "yolo_roi_confidence": None,
        "yolo_roi_class": None,
        "defect_component_count": 0,
        "defect_bbox": None,
        "final_threshold": FINAL_THRESHOLD,
        "minimum_component_pixels": MIN_COMPONENT_PIXELS,
        "device": "cpu",
        "validation_seconds": round(validation_seconds, 4),
        "efficientad_seconds": 0.0,
        "patchcore_seconds": 0.0,
        "refiner_seconds": 0.0,
        "worker_cache": "core_warm",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    return {
        "metadata": metadata,
        "images_base64_png": {
            "preprocessed": None,
            "efficientad_heatmap": None,
            "patchcore_heatmap": None,
            "stage2_heatmap": None,
            "stage3_heatmap": None,
            "classical_cv_heatmap": None,
            "yolo_roi_mask": None,
            "hybrid_heatmap": None,
            "bbox_overlay": None,
            "heatmap": None,
            "mask": None,
            "overlay": None,
        },
    }


def precheck_image_bytes(image_bytes: bytes, filename: str, category: str) -> dict[str, Any]:
    """Run only image-quality + category/OOD validation. No anomaly specialist is executed.

    This is intentionally cheap compared with full inspection and is used by the UI
    immediately after upload/category selection so obvious mismatches are caught before
    a CPU inspection job is created.
    """
    configure_cpu_runtime()
    if category not in CATEGORIES:
        return {
            "state": "unsupported_category",
            "can_run": False,
            "selected_category": category,
            "predicted_category": None,
            "message": f"Unsupported category: {category}",
        }
    if not image_bytes:
        return {
            "state": "empty_input",
            "can_run": False,
            "selected_category": category,
            "predicted_category": None,
            "message": "Image payload is empty.",
        }

    suffix = Path(filename or "image.png").suffix.lower() or ".png"
    started = time.perf_counter()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as stream:
        stream.write(image_bytes)
        image_path = Path(stream.name)
    try:
        original = Image.open(image_path).convert("RGB")
        quality = _image_quality_check(original)
        if quality.get("image_quality_state") == "rejected":
            return {
                "state": "poor_quality_input",
                "can_run": False,
                "selected_category": category,
                "predicted_category": None,
                "message": quality.get("image_quality_message") or "Image quality is too poor for inspection.",
                "precheck_seconds": round(time.perf_counter() - started, 4),
            }

        validation = _category_validation(image_path, category)
        state = validation.get("input_category_state") or "unknown"
        can_run = state == "valid"
        return {
            "state": state,
            "can_run": can_run,
            "selected_category": category,
            "predicted_category": validation.get("predicted_category"),
            "message": validation.get("category_validation_message") or "Input precheck complete.",
            "validator": validation.get("category_validator"),
            "category_probability": validation.get("category_probability"),
            "selected_category_probability": validation.get("selected_category_probability"),
            "category_margin": validation.get("category_margin"),
            "precheck_seconds": round(time.perf_counter() - started, 4),
        }
    except Exception as exc:
        return {
            "state": "precheck_error",
            "can_run": False,
            "selected_category": category,
            "predicted_category": None,
            "message": f"Could not validate the input safely: {type(exc).__name__}",
            "precheck_seconds": round(time.perf_counter() - started, 4),
        }
    finally:
        image_path.unlink(missing_ok=True)


def infer_image_bytes(image_bytes: bytes, filename: str, category: str) -> dict[str, Any]:
    configure_cpu_runtime()
    if category not in CATEGORIES:
        raise ValueError(f"Unsupported category: {category}")
    if not image_bytes:
        raise ValueError("Image payload is empty")

    suffix = Path(filename or "image.png").suffix.lower() or ".png"
    started = time.perf_counter()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as stream:
        stream.write(image_bytes)
        image_path = Path(stream.name)
    try:
        original = Image.open(image_path).convert("RGB")
        current = _load_pipeline()
        from evtclip_runtime.refinement import mask_agreement, normalize, stage2_map, stage2_mask
        from evtclip_runtime.routing import RouteDecision, RuntimeHealth, choose_route

        profile = current.profiles[category]
        validation_started = time.perf_counter()
        image_quality = _image_quality_check(original)
        if image_quality["image_quality_state"] == "rejected":
            quality_rejection = {
                **image_quality,
                "input_category_state": "poor_quality_input",
                "input_category_valid": False,
                "selected_category": category,
                "predicted_category": None,
                "category_similarity": None,
                "category_margin": 0.0,
                "category_similarities": {},
                "category_supported_score": None,
                "category_unsupported_score": None,
                "category_open_set_margin": 0.0,
                "category_validation_message": image_quality["image_quality_message"],
                "category_validator": "image_quality_gate",
            }
            validation_seconds = time.perf_counter() - validation_started
            return _rejected_payload(quality_rejection, started, validation_seconds)

        category_validation = _category_validation(image_path, category)
        category_validation.update(image_quality)
        validation_seconds = time.perf_counter() - validation_started

        # Hard reject only a calibrated/strong mismatch or unsupported input.
        # Low-margin category disagreements are advisory and do not block or
        # downgrade an otherwise valid inspection.
        if category_validation["input_category_state"] in {"invalid_category", "category_uncertain", "unsupported_input"}:
            return _rejected_payload(category_validation, started, validation_seconds)

        # Hybrid CV is intentionally benchmark-gated. In the default shadow
        # mode it computes and records evidence without changing the calibrated
        # EVT-CLIP decision or accepted mask.
        classical_cv = None
        yolo_roi = {"state": "not_run", "mask": None, "confidence": None, "bbox": None, "class_name": None}
        classical_cv_seconds = 0.0
        if HYBRID_CV_ENABLED and HYBRID_MODE != "off":
            cv_started = time.perf_counter()
            from app.services.yolo_roi import get_roi_mask
            from app.services.hybrid_cv import compute_classical_cv_evidence
            yolo_roi = get_roi_mask(original)
            # Compute at the same geometry later used by the anomaly maps.
            # 256x256 is a safe temporary target and is resized again after
            # specialist/refiner inference if necessary.
            classical_cv = compute_classical_cv_evidence(
                original, (256, 256), roi_mask=yolo_roi.get("mask")
            )
            classical_cv_seconds = time.perf_counter() - cv_started

        efficient_raw, efficient_score, efficient_label, efficient_cache_hit, efficient_seconds = _specialist_prediction(
            "efficientad", category, image_path
        )
        patchcore_raw, patchcore_score, patchcore_label, patchcore_cache_hit, patchcore_seconds = _specialist_prediction(
            "patchcore", category, image_path
        )
        efficient = normalize(efficient_raw, **profile["normalization"]["efficientad"])
        patchcore = normalize(patchcore_raw, **profile["normalization"]["patchcore"])
        fused_map = stage2_map(efficient_raw, patchcore_raw, profile)
        fused_mask = _filter_small_components(stage2_mask(fused_map, profile))

        refined_map = refined_mask = None
        agreement = confidence = None
        fallback_reason = None
        refiner_started = time.perf_counter()
        try:
            refined_map = current._refined_map(category, image_path, efficient_raw, patchcore_raw)
            refined_mask = _filter_small_components((refined_map >= FINAL_THRESHOLD).astype(np.uint8))
            agreement = mask_agreement(fused_mask, refined_mask)
            confidence = float(refined_map.max())
            route = choose_route(
                category,
                RuntimeHealth(True, True, True),
                confidence=confidence,
                map_agreement=agreement,
            )
        except Exception as error:
            route = RouteDecision.STAGE2_FALLBACK
            fallback_reason = type(error).__name__
        refiner_seconds = time.perf_counter() - refiner_started

        if route == RouteDecision.STAGE3_STABLE and refined_map is not None:
            if STAGE3_BLEND_ALPHA is None:
                localization_map, localization_mask = refined_map, refined_mask
                localization_source = "stage3_evt_clip"
            else:
                # Experimental path is dormant by default. It is intended only
                # for an override produced by evaluation/benchmark_map_fusion_gate.py
                # after calibration-only selection and untouched-holdout promotion.
                alpha = float(STAGE3_BLEND_ALPHA)
                localization_map = (alpha * refined_map + (1.0 - alpha) * fused_map).astype(np.float32)
                localization_mask = _filter_small_components((localization_map >= FINAL_THRESHOLD).astype(np.uint8))
                localization_source = f"benchmark_gated_stage2_stage3_blend_{alpha:.2f}"
            if not localization_mask.any() and fused_mask.any():
                localization_map, localization_mask = fused_map, fused_mask
                localization_source = "stage2_fallback_empty_stage3_mask"
        else:
            localization_map, localization_mask = fused_map, fused_mask
            localization_source = "stage2_fallback"
            fallback_reason = fallback_reason or "invalid_refiner_output"

        classical_map = None
        hybrid_map = localization_map
        hybrid_applied = False
        if classical_cv is not None:
            import cv2
            classical_map = cv2.resize(
                classical_cv.evidence_map.astype(np.float32),
                (localization_map.shape[1], localization_map.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )
            if HYBRID_MODE == "localization":
                # Benchmark-gated residual fusion: CV can strengthen suspicious
                # pixels but does not replace the learned map.
                hybrid_map = np.clip(
                    localization_map + HYBRID_CV_ALPHA * classical_map * (1.0 - localization_map),
                    0.0, 1.0
                ).astype(np.float32)
                localization_map = hybrid_map
                localization_mask = _filter_small_components((localization_map >= FINAL_THRESHOLD).astype(np.uint8))
                localization_source = f"hybrid_evt_clip_opencv_alpha_{HYBRID_CV_ALPHA:.2f}"
                hybrid_applied = True

        labels = {"efficientad": efficient_label, "patchcore": patchcore_label}
        scores = {"efficientad": efficient_score, "patchcore": patchcore_score}
        primary = PRIMARY_SPECIALIST[category]
        secondary = "patchcore" if primary == "efficientad" else "efficientad"
        primary_label = labels[primary]
        if primary_label is None:
            primary_label = bool(localization_mask.any())
            decision_source = "localization_area_fallback"
        else:
            decision_source = f"{primary}_checkpoint_image_label"
        anomalous = bool(primary_label)
        disagreement = labels[secondary] is not None and bool(labels[secondary]) != anomalous
        final_mask = localization_mask if anomalous else np.zeros_like(localization_mask)
        final_map = localization_map
        result_valid = bool(category_validation["input_category_valid"])
        quality_warning = category_validation.get("image_quality_state") == "warning"
        # Valid inspections are accepted as Normal/Anomalous. Specialist
        # disagreement and soft quality cautions remain visible as technical
        # evidence, but they no longer force every scan into review state.
        review_required = False
        raw_decision = "anomaly" if anomalous else "normal"
        accepted_decision = raw_decision if result_valid else "diagnostic_only"
        review_reason = None
        decision_score = scores[primary]
        if decision_score is None:
            decision_score = float(localization_map.max())
        display_map = (
            np.where(final_mask > 0, final_map, 0.0).astype(np.float32)
            if anomalous and final_mask.any()
            else np.zeros_like(final_map)
        )

        cache_state = (
            "warm_pair" if efficient_cache_hit and patchcore_cache_hit
            else "partial_warm" if efficient_cache_hit or patchcore_cache_hit
            else "cold_pair"
        )
        geometry = _mask_geometry(final_mask)

        # Same semantic category does not guarantee the image belongs to the
        # MVTec appearance distribution used to fit that specialist. For the
        # newly added ten categories, two saturated specialist scores together
        # with an almost-full-frame mask is treated as domain shift, not as a
        # trustworthy defect result. This specifically prevents arbitrary wood
        # photos (or similarly shifted same-category photos) from being reported
        # as a confident 100% defect.
        _new_category = (
            'NEW_SPECIALIST_CATEGORIES' in globals()
            and category in NEW_SPECIALIST_CATEGORIES
        )
        _efficient_saturated = efficient_score is not None and float(efficient_score) >= 0.985
        _patchcore_saturated = patchcore_score is not None and float(patchcore_score) >= 0.985
        _mask_fraction = float(geometry.get("defect_area_fraction") or 0.0)
        if (
            _new_category
            and anomalous
            and _efficient_saturated
            and _patchcore_saturated
            and _mask_fraction >= 0.85
        ):
            result_valid = False
            review_required = True
            review_reason = "out_of_calibrated_domain_saturation"
            raw_decision = "invalid"
            accepted_decision = "diagnostic_only"
            decision_source = "domain_shift_safety_gate"
            confidence = 0.0
            fallback_reason = "same_category_domain_shift"
            category_validation["category_validation_message"] = (
                f"The image is semantically consistent with {CATEGORY_NAMES[category]}, "
                "but both trained specialists saturated and the predicted mask covers most "
                "of the frame. This is outside the calibrated MVTec appearance domain, so "
                "the defect result was withheld instead of being reported as a valid anomaly."
            )
            # Clear production geometry. Raw specialist maps remain inside the
            # worker payload only; the web layer intentionally does not persist
            # AI evidence for invalid results.
            final_mask = np.zeros_like(final_mask)
            display_map = np.zeros_like(final_map)
            geometry = _mask_geometry(final_mask)
        if (
            'NEW_SPECIALIST_CATEGORIES' in globals()
            and category in NEW_SPECIALIST_CATEGORIES
            and result_valid
            and anomalous
            and float(geometry.get("defect_area_fraction") or 0.0) >= 0.90
        ):
            review_required = True
            review_reason = "implausible_full_frame_localization"
        stage3_score = float(refined_map.max()) if refined_map is not None else None
        metadata = {
            **category_validation,
            "status": "complete",
            "rejection_code": (
                "domain_shift" if review_reason == "out_of_calibrated_domain_saturation" else None
            ),
            "result_valid": result_valid,
            "review_required": review_required,
            "review_reason": review_reason,
            "decision": accepted_decision,
            "raw_anomaly_decision": raw_decision,
            "anomalous": anomalous,
            "score": float(decision_score),
            "decision_source": decision_source,
            "primary_specialist": primary,
            "route": route.value,
            "confidence": confidence,
            "map_agreement": agreement,
            "fallback_reason": fallback_reason,
            "localization_source": localization_source,
            **geometry,
            "efficientad_image_score": efficient_score,
            "efficientad_image_label": efficient_label,
            "patchcore_image_score": patchcore_score,
            "patchcore_image_label": patchcore_label,
            "stage2_map_score": float(fused_map.max()),
            "stage3_map_score": stage3_score,
            "classical_cv_score": float(classical_cv.score) if classical_cv is not None else None,
            "classical_cv_seconds": round(classical_cv_seconds, 4),
            "classical_cv_defect_hint": classical_cv.defect_hint if classical_cv is not None else None,
            "classical_cv_metrics": classical_cv.metrics if classical_cv is not None else {},
            "hybrid_mode": HYBRID_MODE,
            "hybrid_applied": hybrid_applied,
            "hybrid_map_score": float(hybrid_map.max()) if hybrid_map is not None else None,
            "yolo_roi_state": yolo_roi.get("state"),
            "yolo_roi_confidence": yolo_roi.get("confidence"),
            "yolo_roi_class": yolo_roi.get("class_name"),
            "final_threshold": FINAL_THRESHOLD,
            "minimum_component_pixels": MIN_COMPONENT_PIXELS,
            "stage3_blend_alpha": STAGE3_BLEND_ALPHA,
            "device": "cpu",
            "validation_seconds": round(validation_seconds, 4),
            "efficientad_seconds": efficient_seconds,
            "patchcore_seconds": patchcore_seconds,
            "refiner_seconds": round(refiner_seconds, 4),
            "worker_cache": cache_state,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        model_input = original.resize((256, 256), Image.Resampling.LANCZOS)
        images = {
            "preprocessed": model_input,
            "efficientad_heatmap": _heatmap_image(efficient),
            "patchcore_heatmap": _heatmap_image(patchcore),
            "stage2_heatmap": _heatmap_image(fused_map),
            "stage3_heatmap": _heatmap_image(refined_map) if refined_map is not None else None,
            "classical_cv_heatmap": _heatmap_image(classical_map) if classical_map is not None else None,
            "yolo_roi_mask": _mask_image(yolo_roi["mask"]) if isinstance(yolo_roi.get("mask"), np.ndarray) else None,
            "hybrid_heatmap": _heatmap_image(hybrid_map) if hybrid_map is not None else None,
            "bbox_overlay": _bbox_overlay_image(original, final_mask, geometry.get("defect_bbox")),
            "heatmap": _heatmap_image(display_map if display_map.any() else final_map),
            "mask": _mask_image(final_mask),
            "overlay": _overlay_image(original, display_map) if display_map.any() else original,
        }
        return {
            "metadata": metadata,
            "images_base64_png": {name: _encode_png(image) for name, image in images.items()},
        }
    finally:
        image_path.unlink(missing_ok=True)
