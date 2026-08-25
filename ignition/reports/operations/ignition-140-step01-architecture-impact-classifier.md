# IGNITION-20260826-140 Step 01 — Architecture-impact classification R1

The new machine-readable classifier separates `ARCHITECTURE_CHANGING`,
`BEHAVIORAL_CONTROL_PLANE_CHANGE`, `PRESENTATION_ONLY`, `RELEASE_ONLY` and
`DATA_REFRESH_ONLY` (with `NONE` for an unchanged task). It derives the class
from semantic markers rather than from whether a map node or documentation
file changed. The existing three-value `identity_impact` field remains as a
compatibility projection.

The negative gate rejects a change that touches process transport or the
canonical state source while declaring `PRESENTATION_ONLY`. Six focused tests
pass with zero failures, errors or skips.

Machine evidence: `ignition/data/operations/iterations/140/step01-architecture-impact-classifier.json`.

Claim ceiling: repository-local semantic classification only; no external
truth, Owner authority or epistemic upgrade is inferred.
