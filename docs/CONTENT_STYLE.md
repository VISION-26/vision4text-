# Project copy style

The application uses the public `petergyang/no-ai-slop` rules as a writing-quality gate for student-facing copy and report prose.

Project rules:

- lead with the specific point;
- keep model names, numbers, limits, and failure states intact;
- use direct verbs and short technical explanations;
- remove canned openings, faux-insight setups, inflated importance language, and vague attribution;
- do not invent benchmarks, prompts, attention maps, ground truth, medical claims, or speed claims;
- label published EVT-CLIP metrics as paper results;
- label the five-category evaluation as this project’s evaluation;
- keep the medical experiment separate from industrial inference;
- preserve uncertainty when the evidence is uncertain;
- prefer one concrete sentence over promotional filler.

The current application does not use a generative text model to write inspection conclusions. Reports use deterministic templates plus stored model metadata. If a text-generating model is added later, its output must pass the same rules before display or export.

Run `python tools/content_quality_gate.py` before release. `tools/validate_release.py` runs the gate automatically.

Upstream reference: https://github.com/petergyang/no-ai-slop
