# Consolidated Patch Provenance

Base source:
- EVT_CLIP_HYBRID_YOLO_OPENCV_GIT_READY(1)(1).zip

Applied in chronological order:
1. EVT_CLIP_REAL_EXAMPLES_AUTH_FIX_TOOLS.zip
2. EVT_CLIP_OOD_DYNAMIC_EVIDENCE_FIX.zip
3. EVT_CLIP_FINAL_PREDEPLOY_SAFETY_FIX.zip
4. EVT_CLIP_PRECHECK_DOMAIN_SHIFT_GUARD.zip

Submission-specific reconciliation:
- Public UI wording was restored to the actual five-category production scope because the runtime registry still exposes five integrated categories.
- Experimental new-ten categories remain research/benchmark work and are not advertised as live production support.
- tools/validate_release.py was updated only to recognize the newer precheck/category-safety implementation; production logic was not weakened.
