# IGNITION-130 Step 11 — residual reclassification

Task 129’s terminal receipt remains the source record. The following items are retained as historical or environmental residuals; none is a new Task 130 Current Surface regression.

| Residual | Classification | Evidence boundary | Task 130 disposition |
| --- | --- | --- | --- |
| `d127`, `d182`, `d190`, `d260`, `t2`, `y1`, five `nfc-*` entries (11 total) | `PRE_EXISTING_SOURCE_HASH_DRIFT` | Human Surface validator reproduces the same 11 source-hash drifts recorded by Task 129. | Retain; do not rewrite source text or hashes. |
| Task 127 projection manifest `missing=96` | `HISTORICAL_PROJECTION_RESIDUAL` | Historical projection-hygiene manifest and Task 129 receipt. | Preserve historical provenance. |
| `test_production_execution_authority` short-window interruption | `ENVIRONMENTAL_TIMEOUT` | Existing validator subprocess exceeded the bounded window; no new Steering assertion failure. | Do not call PASS; retain classification. |
| Knowledge Experience two-pass first-generator interruption | `ENVIRONMENTAL_TIMEOUT` | Existing heavy generator exceeded the bounded window; no deterministic PASS claimed. | Do not call PASS; retain classification. |
| Foundation / Phase-E full discovery long-running boundary | `ENVIRONMENTAL_LONG_RUNNING_BASELINE` | Task 129 Step 20/21 discovery record. | Retain baseline boundary; do not weaken gates. |

The current compiler, typed semantic gate, lifecycle checks, Current Facts, snapshot and Current-State sync are separate Task 130 evidence and pass independently. `CURRENT_WITH_OPEN_OBLIGATIONS` and `EPISTEMICALLY_ACCEPTED=0` remain unchanged.

Claim ceiling: repository-local residual bookkeeping only; no production, Owner, external-truth or epistemic claim follows.
