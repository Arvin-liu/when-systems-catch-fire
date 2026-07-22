# Q42 repair-r2 — R4 freeze

- branch: `repair-r2/q42-r2-counterfactual-semantics`
- annotated_tag: `archive/q42-repair-r2-frozen-head`
- base: Q42 repair-r1 head `2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98`
- direct predecessor: prior repair-r2 head `ea447ed7f6331f8ed5e58526f4c2341d3a41d6a6` (inherited via `--no-ff` merge of `repair-r2/d2-r2-multihistory-semantics`)
- PR base: `repair-r2/d2-r2-multihistory-semantics` (prior repair-r2 branch)

## Root blockers closed (this checkpoint)

1. **RB09-DIRECT-PREDECESSOR-BINDING** — `CONFIG['parent_head']` rebound from the stale
   prior-repair head `1904628103d8c23133107d501a22e3f17d08221d` to the real predecessor repair-r2 head `ea447ed7f6331f8ed5e58526f4c2341d3a41d6a6`;
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

`python -m pytest tests/counterfactual/test_q42_repair_r2.py` → BUILDER_VALIDATION_PASS.

## Closure

closure_complete=true, residue=0, iteration_sync=PASS. Validation is internal
(BUILDER_VALIDATION_PASS), not INDEPENDENT_ACCEPTED.
