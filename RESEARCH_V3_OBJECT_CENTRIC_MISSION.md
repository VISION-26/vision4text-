# EVT-CLIP Research V3 — Object-Centric Self-Calibrating Inspection

This branch is research-only. It must not replace the stable five-category production route until real-camera evidence justifies it.

## Working hypothesis

A rapidly enrolled object-coordinate normality passport, combined with nuisance-invariant residual evidence and a dual-coordinate temporal attachment test, can reduce false alarms from background, illumination, pose and camera shifts while preserving physical defect localization without category-specific retraining.

## Visual Normality Passport (VNP)

Enrollment does not train a category-specific network. It creates a compact object-specific normality representation from several good observations:

1. isolate or mark the product,
2. align good observations into canonical object coordinates,
3. model normal appearance, edge and frequency variation,
4. optionally add frozen foundation-feature local normality,
5. calibrate using normal-only data,
6. inspect future frames in canonical object coordinates,
7. for video, compare anomaly persistence in image coordinates with persistence after object-motion compensation.

A physical defect should generally become more spatially persistent after object compensation. Background/scene artifacts should often become less persistent.

## V3 prototype work started

The local research package now contains:

- object-biased ORB + RANSAC alignment with ECC fallback,
- object-coordinate normal median/MAD passport,
- robust photometric normalization,
- gradient and high-frequency residual witnesses,
- evidence-agreement fusion,
- deterministic nuisance-counterfactual persistence,
- object-coordinate vs image-coordinate temporal attachment scoring,
- a bridge for running NCRQ on canonicalized object-only inputs,
- a MVTec-like real-folder benchmark runner,
- controlled synthetic camera-shift regression tests.

Initial software verification: 10 research tests pass. A 40-sample controlled synthetic nuisance test separates defects from nuisance perfectly in this synthetic setup while naive full-frame difference performs substantially worse. This is only a development sanity check and must not be reported as real-camera evidence.

## Required real evidence

The next scientific gate is evaluation on AutoVI, RobustAD, AeBAD, Real-IAD/Real-IAD D3, MVTec AD 2, plus an own phone/webcam camera-shift holdout. The primary success criterion is lower normal false-positive rate and smaller performance drop under real background/illumination/pose/camera shifts, not another saturated MVTec score.

## Novelty discipline

Do not claim generic reference matching, image registration, background removal, PCA/subspace residuals, DINO/CLIP patch matching, lighting normalization, multi-frame inspection or object-coordinate defect mapping as new. All have substantial paper/patent prior art. Any eventual paper or patent must be based on a specific experimentally demonstrated mechanism and must survive a professional prior-art review.
