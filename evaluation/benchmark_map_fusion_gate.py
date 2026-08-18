#!/usr/bin/env python3
"""Benchmark-gated Stage-2/Stage-3 map blending for EVT-CLIP V2.

This tool is intentionally research/offline only. It never edits production.
It searches a small family of convex Stage-2/Stage-3 blends plus threshold and
component cleanup using CALIBRATION samples only. The chosen configuration is
then evaluated once on an untouched HOLDOUT split. A production override is
recommended only when macro Pixel F1 improves by the configured margin and no
category regresses beyond the configured bound.

Each .npz file must contain:
  stage2_map: HxW float map
  stage3_map: HxW float map
  ground_truth: HxW binary/0-255 mask
  category: optional scalar string
  split: optional 'calibration' or 'holdout'

If split is absent, a deterministic filename hash creates the split per
category. This is a post-processing experiment: it does not retrain weights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage

BASELINE_THRESHOLD = 0.267
BASELINE_MIN_COMPONENT = 16


@dataclass
class Sample:
    path: Path
    category: str
    stage2: np.ndarray
    stage3: np.ndarray
    ground_truth: np.ndarray
    split: str


def _text(value, default="") -> str:
    if value is None:
        return default
    arr = np.asarray(value)
    if not arr.size:
        return default
    item = arr.reshape(-1)[0]
    return str(item.decode() if isinstance(item, bytes) else item)


def stable_split(path: Path, category: str, holdout_ratio: float) -> str:
    digest = hashlib.sha256(f"{category}:{path.name}".encode()).digest()
    unit = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
    return "holdout" if unit < holdout_ratio else "calibration"


def load_samples(root: Path, holdout_ratio: float) -> list[Sample]:
    samples = []
    for path in sorted(root.rglob("*.npz")):
        with np.load(path, allow_pickle=False) as data:
            required = {"stage2_map", "stage3_map", "ground_truth"}
            if not required.issubset(data.files):
                continue
            stage2 = np.asarray(data["stage2_map"], dtype=np.float32).squeeze()
            stage3 = np.asarray(data["stage3_map"], dtype=np.float32).squeeze()
            gt = np.asarray(data["ground_truth"]).squeeze() > 0
            if stage2.ndim != 2 or stage2.shape != stage3.shape or stage2.shape != gt.shape:
                raise ValueError(f"Shape mismatch in {path}: {stage2.shape}, {stage3.shape}, {gt.shape}")
            if not np.isfinite(stage2).all() or not np.isfinite(stage3).all():
                raise ValueError(f"Non-finite anomaly map in {path}")
            category = _text(data["category"] if "category" in data else None, path.stem.split("__")[0])
            split = _text(data["split"] if "split" in data else None).lower()
            if split not in {"calibration", "holdout"}:
                split = stable_split(path, category, holdout_ratio)
            samples.append(Sample(path, category, stage2, stage3, gt, split))
    if not samples:
        raise ValueError(f"No usable map-pair samples found under {root}")
    return samples


def blend(sample: Sample, alpha: float) -> np.ndarray:
    # alpha=1 -> current Stage-3 map; alpha=0 -> Stage-2 map.
    return (alpha * sample.stage3 + (1.0 - alpha) * sample.stage2).astype(np.float32)


def filter_components(mask: np.ndarray, minimum: int) -> np.ndarray:
    binary = np.asarray(mask, dtype=bool)
    if minimum <= 1:
        return binary
    labels, count = ndimage.label(binary)
    if count == 0:
        return np.zeros(binary.shape, dtype=bool)
    sizes = np.bincount(labels.ravel())
    keep = sizes >= minimum
    keep[0] = False
    return keep[labels]


def f1(counts) -> float:
    tp, fp, fn = counts
    denom = 2 * tp + fp + fn
    return (2.0 * tp / denom) if denom else 1.0


def evaluate(samples: list[Sample], alpha: float, threshold: float, minimum: int) -> dict:
    by_category: dict[str, list[int]] = {}
    total = [0, 0, 0]
    for sample in samples:
        pred = filter_components(blend(sample, alpha) >= threshold, minimum)
        gt = sample.ground_truth
        counts = [
            int(np.logical_and(pred, gt).sum()),
            int(np.logical_and(pred, ~gt).sum()),
            int(np.logical_and(~pred, gt).sum()),
        ]
        for i, value in enumerate(counts):
            total[i] += value
        bucket = by_category.setdefault(sample.category, [0, 0, 0])
        for i, value in enumerate(counts):
            bucket[i] += value
    per_category = {category: f1(values) for category, values in sorted(by_category.items())}
    return {
        "stage3_blend_alpha": float(alpha),
        "threshold": float(threshold),
        "minimum_component_pixels": int(minimum),
        "pixel_f1_micro": f1(total),
        "pixel_f1_macro_category": float(np.mean(list(per_category.values()))) if per_category else 0.0,
        "per_category_pixel_f1": per_category,
        "samples": len(samples),
    }


def threshold_candidates(samples: list[Sample], alpha: float, count: int) -> list[float]:
    values = np.concatenate([blend(sample, alpha).reshape(-1) for sample in samples])
    qs = np.linspace(0.70, 0.9995, count)
    candidates = {float(v) for v in np.quantile(values, qs)}
    candidates.add(BASELINE_THRESHOLD)
    return sorted({round(max(0.0, min(1.0, value)), 5) for value in candidates})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("map_fusion_gate_result.json"))
    parser.add_argument("--holdout-ratio", type=float, default=0.50)
    parser.add_argument("--alphas", default="0,0.25,0.5,0.75,1")
    parser.add_argument("--threshold-candidates", type=int, default=32)
    parser.add_argument("--component-sizes", default="0,4,8,16,24,32,48,64")
    parser.add_argument("--min-holdout-gain-pp", type=float, default=0.50)
    parser.add_argument("--max-category-regression-pp", type=float, default=2.00)
    args = parser.parse_args()

    if not 0.1 <= args.holdout_ratio <= 0.9:
        raise ValueError("--holdout-ratio must be between 0.1 and 0.9")
    alphas = sorted({float(x.strip()) for x in args.alphas.split(",") if x.strip()})
    if not alphas or any(alpha < 0 or alpha > 1 for alpha in alphas):
        raise ValueError("Every blend alpha must be between 0 and 1")
    components = sorted({max(0, int(x.strip())) for x in args.component_sizes.split(",") if x.strip()})

    samples = load_samples(args.input, args.holdout_ratio)
    calibration = [s for s in samples if s.split == "calibration"]
    holdout = [s for s in samples if s.split == "holdout"]
    categories = sorted({s.category for s in samples})
    if not calibration or not holdout:
        raise ValueError("Both calibration and holdout samples are required")
    missing = [c for c in categories if not any(s.category == c for s in calibration) or not any(s.category == c for s in holdout)]
    if missing:
        raise ValueError(f"Every category must occur in both splits; missing: {missing}")

    baseline_cal = evaluate(calibration, 1.0, BASELINE_THRESHOLD, BASELINE_MIN_COMPONENT)
    candidates = []
    for alpha in alphas:
        for threshold in threshold_candidates(calibration, alpha, args.threshold_candidates):
            for component in components:
                candidates.append(evaluate(calibration, alpha, threshold, component))
    candidates.sort(key=lambda row: (row["pixel_f1_macro_category"], row["pixel_f1_micro"]), reverse=True)
    winner_cal = candidates[0]

    # Exactly one holdout evaluation of the selected candidate plus the fixed baseline.
    baseline_holdout = evaluate(holdout, 1.0, BASELINE_THRESHOLD, BASELINE_MIN_COMPONENT)
    winner_holdout = evaluate(
        holdout,
        winner_cal["stage3_blend_alpha"],
        winner_cal["threshold"],
        winner_cal["minimum_component_pixels"],
    )
    gain_pp = 100.0 * (winner_holdout["pixel_f1_macro_category"] - baseline_holdout["pixel_f1_macro_category"])
    deltas = {
        c: 100.0 * (winner_holdout["per_category_pixel_f1"][c] - baseline_holdout["per_category_pixel_f1"][c])
        for c in categories
    }
    worst = min(deltas.values())
    promote = gain_pp >= args.min_holdout_gain_pp and worst >= -args.max_category_regression_pp
    recommendation = None
    if promote:
        recommendation = {
            "EVT_STAGE3_BLEND_ALPHA": winner_cal["stage3_blend_alpha"],
            "EVT_FINAL_THRESHOLD": winner_cal["threshold"],
            "EVT_MIN_COMPONENT_PIXELS": winner_cal["minimum_component_pixels"],
        }

    output = {
        "schema_version": "evtclip-map-fusion-benchmark-gate-v1",
        "policy": {
            "selection_split": "calibration only",
            "promotion_split": "untouched holdout",
            "production_is_not_modified_by_this_script": True,
            "min_holdout_gain_pp": args.min_holdout_gain_pp,
            "max_category_regression_pp": args.max_category_regression_pp,
        },
        "dataset": {"samples": len(samples), "calibration": len(calibration), "holdout": len(holdout), "categories": categories},
        "baseline": {"calibration": baseline_cal, "holdout": baseline_holdout},
        "candidate": {"calibration": winner_cal, "holdout": winner_holdout},
        "holdout_macro_gain_pp": round(gain_pp, 4),
        "holdout_category_delta_pp": {k: round(v, 4) for k, v in deltas.items()},
        "worst_category_regression_pp": round(worst, 4),
        "promotion_allowed": bool(promote),
        "recommended_production_override": recommendation,
    }
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0 if promote else 3


if __name__ == "__main__":
    raise SystemExit(main())
