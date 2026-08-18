# Dynamic Product Examples + Focused UI Handoff

## Product example behavior

The New Inspection page does not render a 30-image gallery.

It reads `supported_categories` from the backend `/health` response and displays only those categories in the Product Model selector.

For the currently selected product, `CategoryExampleGuide.jsx` renders:
- one compact Good example,
- one compact Defect example,
- category-specific defect guidance,
- a recommended framing note.

Built-in guidance exists for all 15 MVTec AD category names:
bottle, cable, capsule, carpet, grid, hazelnut, leather, metal_nut, pill, screw, tile, toothbrush, transistor, wood, zipper.

The illustrations are upload/framing guidance only. They are deliberately labelled as examples and are not model predictions or fabricated benchmark evidence.

## Backend-safe behavior

The UI intentionally does not expose a future category merely because its illustration exists.

If the backend returns five supported categories, the selector displays five.
When the trained/runtime registry is expanded and `/health` returns all 15, the same frontend displays all 15 automatically.

This prevents unsupported category selections before the corresponding runtime models, calibration and routing are integrated.

## Removed signed-in UI areas

The following frontend sections/routes were removed:
- Datasets
- Research Evidence
- Medical Research
- the complete Research & Data navigation group

About was retained, rewritten as an operational system page, and moved under Workspace.

Dashboard/Admin/Reports/Overview user-facing dataset/research/medical wording was also removed.

Backend dataset mechanics were not deleted because the existing detection API still uses an internal inspection-profile record. They are no longer presented as a user-facing research/data feature.

## Future integration

After expanded training:
1. integrate verified model artifacts;
2. calibrate Stage-2 for newly supported categories;
3. update/replace the Stage-3 runtime as required;
4. update backend `SUPPORTED_CATEGORIES` / runtime registry;
5. verify `/health` returns the intended category list;
6. deploy this frontend together with that backend;
7. smoke-test one Good and one defective image per enabled category.
