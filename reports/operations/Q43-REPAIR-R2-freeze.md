# Q43 repair-r2 — R4 freeze

- branch: `repair-r2/q43-r2-escalation-semantics`
- annotated_tag: `archive/q43-repair-r2-frozen-head`
- base: Q43 repair-r1 head `5efbce81e96d90d5ebd246891e4762928365d6b8`
- direct predecessor: prior repair-r2 head `3283ef6e76788b30a467467083f0d5ad7086b5a0` (inherited via `--no-ff` merge of `repair-r2/q42-r2-counterfactual-semantics`)
- PR base: `repair-r2/q42-r2-counterfactual-semantics` (prior repair-r2 branch)

## Root blockers closed (this checkpoint)

1. **RB09-DIRECT-PREDECESSOR-BINDING** — `CONFIG['parent_head']` rebound from the stale
   prior-repair head `2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98` to the real predecessor repair-r2 head `3283ef6e76788b30a467467083f0d5ad7086b5a0`;
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

`python -m pytest tests/escalation/test_q43_repair_r2.py` → BUILDER_VALIDATION_PASS.

## Closure

closure_complete=true, residue=0, iteration_sync=PASS. Validation is internal
(BUILDER_VALIDATION_PASS), not INDEPENDENT_ACCEPTED.
