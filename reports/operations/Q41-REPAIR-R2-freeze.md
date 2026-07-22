# Q41 repair-r2 — R4 freeze

- branch: `repair-r2/q41-r2-anomaly-semantics`
- annotated_tag: `archive/q41-repair-r2-frozen-head`
- base: Q41 repair-r1 head `da9c4e2a6b8c0f757aa676814fda7c86d4ac2558`
- direct predecessor: prior repair-r2 head `25f937ea8d53b4b14f31fc9c8779995f3c516bac` (inherited via `--no-ff` merge of `repair-r2/scientific-metacognition-r2-parent-and-semantics`)
- PR base: `repair-r2/scientific-metacognition-r2-parent-and-semantics` (prior repair-r2 branch)

## Root blockers closed (this checkpoint)

1. **RB09-DIRECT-PREDECESSOR-BINDING** — `CONFIG['parent_head']` rebound from the stale
   prior-repair head `183f4343a036d0dbb20ae7df9dd96be97bcd3fc3` to the real predecessor repair-r2 head `25f937ea8d53b4b14f31fc9c8779995f3c516bac`;
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

`python -m pytest tests/anomaly/test_q41_repair_r2.py` → BUILDER_VALIDATION_PASS.

## Closure

closure_complete=true, residue=0, iteration_sync=PASS. Validation is internal
(BUILDER_VALIDATION_PASS), not INDEPENDENT_ACCEPTED.
