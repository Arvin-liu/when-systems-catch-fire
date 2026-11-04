# Q44 repair-r2 — R4 freeze

- branch: `repair-r2/q44-r2-consent-semantics`
- annotated_tag: `archive/q44-repair-r2-frozen-head`
- base: Q44 repair-r1 head `4d15ccaf2e574248c0e224c05716c3af46203a39`
- direct predecessor: prior repair-r2 head `e5181c83efba68f847b55e13c7b5a1ee1fd6888e` (inherited via `--no-ff` merge of `repair-r2/q43-r2-escalation-semantics`)
- PR base: `repair-r2/q43-r2-escalation-semantics` (prior repair-r2 branch)

## Root blockers closed (this checkpoint)

1. **RB09-DIRECT-PREDECESSOR-BINDING** — `CONFIG['parent_head']` rebound from the stale
   prior-repair head `5efbce81e96d90d5ebd246891e4762928365d6b8` to the real predecessor repair-r2 head `e5181c83efba68f847b55e13c7b5a1ee1fd6888e`;
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

`python -m pytest tests/coaching/test_q44_repair_r2.py` → BUILDER_VALIDATION_PASS.

## Closure

closure_complete=true, residue=0, iteration_sync=PASS. Validation is internal
(BUILDER_VALIDATION_PASS), not INDEPENDENT_ACCEPTED.
