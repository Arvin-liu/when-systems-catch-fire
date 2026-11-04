# SCIENTIFIC-CONTEXT-PROTOCOL repair-r2 — R4 freeze

- branch: `repair-r2/scientific-context-protocol-r2-context-semantics`
- annotated_tag: `archive/scientific-context-protocol-repair-r2-frozen-head`
- base: SCIENTIFIC-CONTEXT-PROTOCOL repair-r1 head `50cdf4ca95337d5adbd900140c53dfc3aaf422f4`
- direct predecessor: prior repair-r2 head `7532b4b34cf841c09faab8c835c5fc7f896d30d8` (inherited via `--no-ff` merge of `repair-r2/q44-r2-consent-semantics`)
- PR base: `repair-r2/q44-r2-consent-semantics` (prior repair-r2 branch)

## Root blockers closed (this checkpoint)

1. **RB09-DIRECT-PREDECESSOR-BINDING** — `CONFIG['parent_head']` rebound from the stale
   prior-repair head `4d15ccaf2e574248c0e224c05716c3af46203a39` to the real predecessor repair-r2 head `7532b4b34cf841c09faab8c835c5fc7f896d30d8`;
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

`python -m pytest tests/context_protocol/test_scientific_context_protocol_repair_r2.py` → BUILDER_VALIDATION_PASS.

## Closure

closure_complete=true, residue=0, iteration_sync=PASS. Validation is internal
(BUILDER_VALIDATION_PASS), not INDEPENDENT_ACCEPTED.
