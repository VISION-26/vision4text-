#!/usr/bin/env python3
"""Leakage-resistant post-processing benchmark gate for EVT-CLIP V2.

This tool does NOT change production automatically. It evaluates whether a
candidate mask threshold/minimum-component setting improves held-out Pixel F1.

Input directory: one .npz per inspected image with:
  score_map: HxW float anomaly map (required)
  ground_truth: HxW binary/0-255 mask (required)
  category: optional scalar string; falls back to filename prefix before '__'
  split: optional scalar string: 'calibration' or 'holdout'

If split is absent, a stable SHA-256 filename split is created per category.
Only calibration data chooses the candidate. Holdout data is touched once for
promotion. This prevents tuning directly on the reported benchmark set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import ndimage

BASELINE_THRESHOLD = 0.267
BASELINE_MIN_COMPONENT = 16


@dataclass
class Sample:
    path: Path
    category: str
    score_map: np.ndarray
    ground_truth: np.ndarray
    split: str


def _scalar_text(value, default="") -> str:
    if value is None:
        return default
    arr = np.asarray(value)
    if arr.size == 0:
        return default
    item = arr.reshape(-1)[0]
    return str(item.decode() if isinstance(item, bytes) else item)


def stable_split(path: Path, category: str, holdout_ratio: float) -> str:
    digest = hashlib.sha256(f"{category}:{path.name}".encode()).digest()
    unit = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
    return "holdout" if unit < holdout_ratio else "calibration"


def load_samples(root: Path, holdout_ratio: float) -> list[Sample]:
    samples: list[Sample] = []
    for path in sorted(root.rglob("*.npz")):
        with np.load(path, allow_pickle=False) as data:
            if "score_map" not in data or "ground_truth" not in data:
                continue
            score = np.asarray(data["score_map"], dtype=np.float32).squeeze()
            gt = np.asarray(data["ground_truth"]).squeeze() > 0
            if score.ndim != 2 or gt.ndim != 2 or score.shape != gt.shape:
                raise ValueError(f"Invalid shapes in {path}: score={score.shape}, gt={gt.shape}")
            if not np.isfinite(score).all():
                raise ValueError(f"Non-finite score map in {path}")
            category = _scalar_text(data["category"] if "category" in data else None, path.stem.split("__")[0])
            split = _scalar_text(data["split"] if "split" in data else None).lower()
            if split not in {"calibration", "holdout"}:
                split = stable_split(path, category, holdout_ratio)
            samples.append(Sample(path, category, score, gt, split))
    if not samples:
        raise ValueError(f"No usable .npz samples found under {root}")
    return samples


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


def confusion(samples: Iterable[Sample], threshold: float, minimum: int):
    tp = fp = fn = 0
    by_category: dict[str, list[int]] = {}
    for sample in samples:
        pred = filter_components(sample.score_map >= threshold, minimum)
        gt = sample.ground_truth
        values = [int(np.logical_and(pred, gt).sum()), int(np.logical_and(pred, ~gt).sum()), int(np.logical_and(~pred, gt).sum())]
        tp += values[0]; fp += values[1]; fn += values[2]
        bucket = by_category.setdefault(sample.category, [0, 0, 0])
        for i, value in enumerate(values): bucket[i] += value
    return (tp, fp, fn), by_category


def f1_from_counts(counts) -> float:
    tp, fp, fn = counts
    denom = 2 * tp + fp + fn
    return (2.0 * tp / denom) if denom else 1.0


def evaluate(samples: list[Sample], threshold: float, minimum: int) -> dict:
    counts, per_category_counts = confusion(samples, threshold, minimum)
    per_category = {category: f1_from_counts(values) for category, values in sorted(per_category_counts.items())}
    macro = float(np.mean(list(per_category.values()))) if per_category else 0.0
    return {
        "threshold": float(threshold),
        "minimum_component_pixels": int(minimum),
        "pixel_f1_micro": f1_from_counts(counts),
        "pixel_f1_macro_category": macro,
        "per_category_pixel_f1": per_category,
        "samples": len(samples),
    }


def threshold_candidates(samples: list[Sample], count: int) -> list[float]:
    # Include current production threshold and data-derived calibration quantiles.
    values = np.concatenate([s.score_map.reshape(-1) for s in samples])
    quantiles = np.linspace(0.70, 0.9995, count)
    candidates = set(float(x) for x in np.quantile(values, quantiles))
    candidates.add(BASELINE_THRESHOLD)
    # Stable rounded candidates prevent meaningless floating-point differences.
    return sorted({round(max(0.0, min(1.0, value)), 5) for value in candidates})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Directory containing per-image .npz score maps and ground-truth masks")
    parser.add_argument("--output", type=Path, default=Path("benchmark_gate_result.json"))
    parser.add_argument("--holdout-ratio", type=float, default=0.50)
    parser.add_argument("--threshold-candidates", type=int, default=48)
    parser.add_argument("--component-sizes", default="0,4,8,16,24,32,48,64")
    parser.add_argument("--min-holdout-gain-pp", type=float, default=0.50, help="Required macro Pixel F1 gain in percentage points")
    parser.add_argument("--max-category-regression-pp", type=float, default=2.00)
    args = parser.parse_args()

    if not 0.1 <= args.holdout_ratio <= 0.9:
        raise ValueError("--holdout-ratio must be between 0.1 and 0.9")
    samples = load_samples(args.input, args.holdout_ratio)
    calibration = [s for s in samples if s.split == "calibration"]
    holdout = [s for s in samples if s.split == "holdout"]
    categories = sorted({s.category for s in samples})
    if not calibration or not holdout:
        raise ValueError("Both calibration and holdout samples are required")
    missing_split_categories = [category for category in categories if not any(s.category == category for s in calibration) or not any(s.category == category for s in holdout)]
    if missing_split_categories:
        raise ValueError(f"Every category must occur in both splits; missing: {missing_split_categories}")

    components = sorted({max(0, int(value.strip())) for value in args.component_sizes.split(",") if value.strip()})
    thresholds = threshold_candidates(calibration, args.threshold_candidates)

    baseline_cal = evaluate(calibration, BASELINE_THRESHOLD, BASELINE_MIN_COMPONENT)
    candidates = []
    for threshold in thresholds:
        for component in components:
            result = evaluate(calibration, threshold, component)
            candidates.append(result)
    candidates.sort(key=lambda row: (row["pixel_f1_macro_category"], row["pixel_f1_micro"]), reverse=True)
    winner_cal = candidates[0]

    # Holdout is evaluated only after candidate selection.
    baseline_holdout = evaluate(holdout, BASELINE_THRESHOLD, BASELINE_MIN_COMPONENT)
    winner_holdout = evaluate(holdout, winner_cal["threshold"], winner_cal["minimum_component_pixels"])

    mean_gain_pp = 100.0 * (winner_holdout["pixel_f1_macro_category"] - baseline_holdout["pixel_f1_macro_category"])
    category_deltas_pp = {
        category: 100.0 * (winner_holdout["per_category_pixel_f1"][category] - baseline_holdout["per_category_pixel_f1"][category])
        for category in categories
    }
    worst_regression_pp = min(category_deltas_pp.values())
    promotion_allowed = mean_gain_pp >= args.min_holdout_gain_pp and worst_regression_pp >= -args.max_category_regression_pp

    output = {
        "schema_version": "evtclip-postprocess-benchmark-gate-v1",
        "policy": {
            "selection_split": "calibration only",
            "promotion_split": "untouched holdout",
            "min_holdout_gain_pp": args.min_holdout_gain_pp,
            "max_category_regression_pp": args.max_category_regression_pp,
            "production_is_not_modified_by_this_script": True,
        },
        "dataset": {"samples": len(samples), "calibration": len(calibration), "holdout": len(holdout), "categories": categories},
        "baseline": {"calibration": baseline_cal, "holdout": baseline_holdout},
        "candidate": {"calibration": winner_cal, "holdout": winner_holdout},
        "holdout_macro_gain_pp": round(mean_gain_pp, 4),
        "holdout_category_delta_pp": {k: round(v, 4) for k, v in category_deltas_pp.items()},
        "worst_category_regression_pp": round(worst_regression_pp, 4),
        "promotion_allowed": bool(promotion_allowed),
        "recommended_production_override": ({
            "EVT_FINAL_THRESHOLD": winner_cal["threshold"],
            "EVT_MIN_COMPONENT_PIXELS": winner_cal["minimum_component_pixels"],
        } if promotion_allowed else None),
    }
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0 if promotion_allowed else 3


if __name__ == "__main__":
    raise SystemExit(main())
