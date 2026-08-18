# EVT-CLIP V2 benchmark-safety utilities

These utilities are deliberately **not connected to production automatically**. Benchmark numbers must come from measured data, not from code changes alone.

## 1. Improve wrong-category rejection with exact references

`build_category_validation_centroids.py` creates the same five-category OpenCLIP centroid cache used by the verified Kaggle safety fix. Run it where MVTec AD `train/good` images are available, then copy `category_validation_centroids.npz` into the production model volume at `/models/production/category_validation_centroids.npz` and redeploy. The CPU worker detects this file automatically. If it is absent, production uses a conservative OpenCLIP text fallback.

## 2. Try to improve unknown/LOCO Pixel F1 without benchmark leakage

`benchmark_postprocess_gate.py` searches only threshold + tiny connected-component cleanup settings on a **calibration split** and evaluates the winner once on an **untouched holdout split**. It refuses promotion unless the mean category Pixel F1 improves by the configured margin and no single category regresses beyond the guardrail.

The current production values remain `threshold=0.267` and `minimum_component_pixels=16` unless a measured gate result explicitly passes. This avoids making the controlled benchmark look better by tuning directly on the test set.

Expected per-image NPZ fields:

- `score_map`: final anomaly/localization map
- `ground_truth`: binary ground-truth mask
- `category`: optional category string
- `split`: optional `calibration` or `holdout`

Example:

```bash
python evaluation/benchmark_postprocess_gate.py ./benchmark_maps --output benchmark_gate_result.json
```

A passing result includes `promotion_allowed: true` and a recommended environment override. A failing result changes nothing in production.

## 3. Stronger experiment: benchmark-gated Stage-2 / Stage-3 map fusion

`benchmark_map_fusion_gate.py` is the more powerful, still leakage-resistant experiment. It evaluates convex blends of the existing Stage-2 fused map and Stage-3 EVT-CLIP map, together with threshold and small-component cleanup. Candidate selection happens on calibration data only; the winner is compared with the fixed Stage-3 production baseline on untouched holdout data.

Expected NPZ fields:

- `stage2_map`
- `stage3_map`
- `ground_truth`
- optional `category`
- optional `split=calibration|holdout`

```bash
python evaluation/benchmark_map_fusion_gate.py ./loco_map_pairs --output loco_map_fusion_gate.json
```

If and only if `promotion_allowed` is true, the output provides a candidate `EVT_STAGE3_BLEND_ALPHA`, `EVT_FINAL_THRESHOLD`, and `EVT_MIN_COMPONENT_PIXELS`. The production worker already understands the optional blend variable, but it is **disabled by default**. Apply an override only after checking the full benchmark report and then redeploying. This keeps the current verified production behavior unchanged until measurement proves the candidate is better.
