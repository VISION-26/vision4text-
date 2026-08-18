# EVT-CLIP Project Scope

## Live inspection scope

The deployed system supports five industrial categories: Bottle, Cable, Capsule, Metal Nut, and Pill.

A completed inspection can show:

- uploaded or camera-captured input
- preprocessing preview
- category/input safety state
- EfficientAD specialist output
- PatchCore specialist output
- Stage-2 fused anomaly map
- Stage-3 EVT-CLIP refined map
- final heatmap, binary mask, bounding-box view, and overlay
- Normal / Anomalous / Rejected Input decision
- model scores, map agreement, defect pixels, mask coverage, bounding box, connected regions, and CPU timing
- persistent history and dashboard analytics
- PDF report and signed evidence export

## Separated areas

### Industrial inspection

This is the live five-category CPU inference system.

### Research evidence

This section explains CLIP, DAEP, CMI, the EVT-CLIP architecture, implementation evaluation, and published EVT-CLIP benchmark results. Published paper metrics remain labelled as research results and are not presented as measurements from a random live upload.

### Medical research

The medical page records the brain-MRI zero-shot experiment separately from industrial inference. ViT-B/32 and ViT-B/16 were not promoted because the tested class separation did not hold up. ViT-L/14-336 remains the recorded research direction.

Live MRI inference is not enabled in this deployment package because the exact earlier MRI source, prompt set, and crop-grid implementation are not present here. No medical result is fabricated. The page remains a research record, not a diagnostic feature.

## Authentication

The current deployment uses one controlled login flow. Public self-registration is disabled. Additional roles can be added later if required.

## Interface principles

Each major screen should answer a clear question:

1. What problem does EVT-CLIP solve?
2. What happens to an image inside the system?
3. What evidence did each model stage produce?
4. Where is the detected region and how large is it in image-mask terms?
5. Was the selected input/category accepted or rejected?
6. Which results come from the live implementation and which belong to research evidence?

## Reliability features

- persistent inspection jobs while CPU inference is queued or running
- queued, starting, running, completed, failed, cancelled, and timed-out job states
- queue age, scan identifier, cancel, retry, and terminal timeout behavior
- separate API availability and inference queue/worker status
- uploaded image metadata: filename, file size, dimensions, and selected time
- accepted/rejected category safety policy with hard mismatch blocking
- human-readable runtime/routing labels with raw identifiers kept under technical details
- active and failed jobs surfaced on Dashboard, Reports, History, and Administration
- PDF/evidence-export completion feedback
- Research and Experimental Medical Research separated from the normal inspection path

## Deployment

The project remains CPU-only on Modal and expects the existing persistent model volume and production secret. The large model bundle is intentionally not duplicated inside this ZIP.
