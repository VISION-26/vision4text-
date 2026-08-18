#!/usr/bin/env python3
"""Build the exact five-class OpenCLIP category-centroid cache.

Run where the verified production model bundle AND MVTec AD training images are
available (Kaggle is ideal). Copy the resulting NPZ to:
  /models/production/category_validation_centroids.npz

The production worker automatically prefers this reference validator over the
portable text-only fallback.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

CATEGORIES = ("bottle", "cable", "capsule", "metal_nut", "pill")


def evenly_spaced(paths: list[Path], count: int) -> list[Path]:
    if len(paths) <= count:
        return paths
    indices = np.linspace(0, len(paths) - 1, num=count, dtype=int)
    return [paths[int(i)] for i in indices]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--mvtec-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("category_validation_centroids.npz"))
    parser.add_argument("--images-per-category", type=int, default=12)
    args = parser.parse_args()

    if str(args.model_root) not in sys.path:
        sys.path.insert(0, str(args.model_root))
    import torch
    import torch.nn.functional as F
    from evtclip_runtime.pipeline import EVTPipeline

    pipeline = EVTPipeline(args.model_root)
    pipeline.device = "cpu" if not torch.cuda.is_available() else pipeline.device
    pipeline._load_refiner()
    centroids = {}
    counts = {}
    extensions = {".png", ".jpg", ".jpeg", ".bmp"}
    for category in CATEGORIES:
        root = args.mvtec_root / category / "train" / "good"
        candidates = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in extensions)
        selected = evenly_spaced(candidates, args.images_per_category)
        if not selected:
            raise RuntimeError(f"No training-good images found for {category}: {root}")
        features = []
        for start in range(0, len(selected), 4):
            batch_paths = selected[start:start + 4]
            batch = torch.stack([pipeline.preprocess(Image.open(path).convert("RGB")) for path in batch_paths]).to(pipeline.device)
            with torch.inference_mode():
                feature = F.normalize(pipeline.clip.encode_image(batch).float(), dim=-1)
            features.append(feature.cpu().numpy().astype(np.float32))
        values = np.concatenate(features, axis=0)
        centroid = values.mean(axis=0)
        centroid /= max(float(np.linalg.norm(centroid)), 1e-12)
        centroids[category] = centroid.astype(np.float32)
        counts[category] = len(selected)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output, **centroids)
    print(json.dumps({"status": "complete", "output": str(args.output), "categories": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
