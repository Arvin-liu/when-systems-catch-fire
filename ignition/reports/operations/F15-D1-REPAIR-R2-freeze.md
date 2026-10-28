# F15-D1 repair-r2 — R4 freeze

- branch: `repair-r2/f15-d1-r2-identifiability-semantics`
- annotated_tag: `archive/f15-d1-repair-r2-frozen-head`
- base: F15-D1 repair-r1 head `f0f7d7ff9dda620d59ad1dd1b504bcd503fe5c09`
- direct predecessor: prior repair-r2 head `e92e7d3eadbb67da288077052f635e3c052bd3a1` (inherited via `--no-ff` merge of `repair-r2/q41-r2-anomaly-semantics`)
- PR base: `repair-r2/q41-r2-anomaly-semantics` (prior repair-r2 branch)

## Root blockers closed (this checkpoint)

1. **RB09-DIRECT-PREDECESSOR-BINDING** — `CONFIG['parent_head']` rebound from the stale
   prior-repair head `da9c4e2a6b8c0f757aa676814fda7c86d4ac2558` to the real predecessor repair-r2 head `e92e7d3eadbb67da288077052f635e3c052bd3a1`;
   the pilot bundle's `parent_binding.exact_head` is rebound to match. A bundle bound to the
   wrong predecessor is now rejected with `PARENT_BINDING_INVALID` (exit 3).
2. **Pilot evidence schema upgrade** — each evidence entry gained the now-mandatory
   `record_type` and `declared_role` fields so the fail-closed engine's
   `MANDATORY_EVIDENCE_FIELDS` check passes (closes the evidence-binding surface for this
   capability consistently with the CP1/CP2/CP3 pilots).

The other four root blockers (ENGINE-PATH-CONTAINMENT, MANDATORY-GIT-OBJECT-BINDING,
EXACT-HEAD-NONRESOLUTION, CALLER-ASSERTED-SEMANTICS) are closed transitively by the
inherited fail-closed shared engine.

## Final local regression

`python -m pytest tests/latent/test_f15_d1_repair_r2.py` → BUILDER_VALIDATION_PASS.

## Closure

closure_complete=true, residue=0, iteration_sync=PASS. Validation is internal
(BUILDER_VALIDATION_PASS), not INDEPENDENT_ACCEPTED.
