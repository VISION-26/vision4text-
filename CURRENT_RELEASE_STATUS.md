# EVT-CLIP Submission Release Status

## Production scope for submission

The live submission build exposes five production-integrated categories:

- Bottle
- Cable
- Capsule
- Metal Nut
- Pill

These categories use the verified EfficientAD/PatchCore specialist routing already present in the production runtime. Stage-2 fusion and Stage-3 refinement remain available for this original production scope.

## Additional ten categories

The additional MVTec categories and four-specialist training work are retained as research/benchmark extension work. They are not advertised as production-integrated in this submission build. Completing that expansion still requires runtime registry integration, category-specific routing/calibration, Stage-2 profiles, Stage-3 strategy, deployment-volume placement, and final end-to-end validation.

## Safety changes included in this consolidated build

- Real example images replace fake SVG product examples.
- Expired authentication sessions refresh or fail closed to login.
- Category/OOD precheck runs before a full anomaly job.
- Wrong-category, unsupported, and poor-quality inputs are blocked before accepted anomaly evidence is produced.
- Missing Stage-2/Stage-3/YOLO artifacts are hidden rather than represented by empty cards.
- Domain-shift safety logic is retained for future specialist-only categories.
- YOLO remains optional/disabled unless valid weights and policy are supplied.

## Submission demo recommendation

Use the original production scope for the live demonstration. Metal Nut is the preferred localization demo category. Prepare one known-good image, one known-defective image, and one mismatched-category input. Do not make the only live demo depend on an arbitrary phone-camera image.

## Known limitation

Real-camera images can differ from MVTec in lighting, background, scale, viewpoint, reflections, and product appearance. The build therefore treats uncertain inputs conservatively rather than claiming factory-grade arbitrary-camera generalization.


### Final submission simplification
OpenCV/YOLO hybrid anomaly evidence is disabled in the production runtime and hidden from the primary UI. OpenCV remains installed only for basic image I/O/resizing utilities used by the backend. The production anomaly decision/localization path is EfficientAD + PatchCore + Stage-2/Stage-3 EVT-CLIP.
