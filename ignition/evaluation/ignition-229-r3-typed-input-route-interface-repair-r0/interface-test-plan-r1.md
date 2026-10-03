# Candidate Interface Test Plan R1

Status: frozen candidate plan only. No successor prompt, successor, or evaluator was run for this package.

## Test boundary

Use synthetic inputs only unless a later command separately authorizes another scope. The deterministic builder, reference interpreter, and route-trace validator are the oracles for binding and route bytes. A future successor prompt can be assessed only for adherence to the response schema and interface invariants listed here. This plan defines no target labels, evaluator scores, or tuning loop.

## Candidate cases

| Case | Synthetic setup | Required observation |
| --- | --- | --- |
| Present selector inputs | All typed inputs are present and one selector matches | `ROUTED`; response trace equals the reference trace field-for-field. |
| Missing selector input | A required selector input is absent and no other route matches | A reference `fallback` remains valid; the absent ID is in `missing_input_ids`, absent from `evaluated_input_ids`, and is never invented. |
| Direct prose contradiction | Prose explicitly asserts the opposite of one bound value | `INTERFACE_CONFLICT`; error code `PROSE_BINDING_CONFLICT`; response text and route trace are null. |
| Non-conflicting prose | Prose is consistent or says nothing about a bound input | Prose does not alter the typed route or the copied reference trace. |
| Missing boolean vs false | One case omits a required boolean; a separate case binds explicit `false` | Missing remains `MISSING_INPUT`; explicit false remains present and is evaluated as false. |
| Nullable value | Policy explicitly allows `null`; compare a present null with an absent ID | Present null and missing remain distinct; no null is synthesized for absence. |
| Ambiguous route | Synthetic policy produces multiple matching routes | `ROUTE_AMBIGUOUS`; response text and route trace are null; no route is chosen. |
| Trace tampering | Change a trace ID, hash, field, or evaluated/missing list | The deterministic validator rejects it; the candidate does not repair the trace. |
| Invalid mapping or types | Duplicate/unknown IDs, incomplete mapping, coercion, or unit mismatch | The builder fails closed before a successor prompt is eligible to run. |

## Acceptance checks

- The response object validates against `successor-response-schema-r1.json`.
- For `ROUTED`, the copied trace passes `validate_route_trace_r1.py` against the exact policy and binding.
- `evaluated_input_ids` and `missing_input_ids` are sorted, unique, disjoint, and match the reference result.
- Missing IDs have no records in `bindings`; no absent value is replaced with null, false, zero, an empty string, or prose-derived content.
- `ROUTE_AMBIGUOUS` and `INTERFACE_CONFLICT` responses carry no route trace.
- A prose/binding contradiction yields the exact `PROSE_BINDING_CONFLICT` marker without changing the bound value.
- A fallback trace may carry missing required IDs and remains valid when the reference interpreter selects fallback.

## Freeze and claim ceiling

This package is a candidate interface for a separately authorized future test. Do not run it as part of R3. Any future run must preserve the target-blind boundary and may not use target/evaluator results for tuning. Schema or prompt conformance would not establish live compatibility, policy effect, transfer, causal effect, revision generation, Cognitive Evolution, cross-model transfer, Model-RSI, or training benefit. Task230 is outside this package and remains unauthorized.
