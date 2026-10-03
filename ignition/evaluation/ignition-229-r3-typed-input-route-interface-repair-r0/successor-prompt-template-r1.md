# Candidate Successor Prompt Template R1

Status: candidate-only prompt package. This template is frozen for review and has not been sent to a successor.

## Inputs supplied to a future run

- `policy_json`: the exact frozen policy object.
- `typed_binding_json`: a builder-produced R1 binding with present values and explicit missing IDs.
- `case_prose`: visible explanatory prose for the same synthetic or otherwise separately authorized case.
- `reference_execution_json`: the deterministic reference interpreter result for the exact policy and binding. A prompt run is in scope only when the result is `ROUTE_TRACE_READY` or `ROUTE_AMBIGUOUS`.
- `successor_response_schema`: `successor-response-schema-r1.json`.

## Instructions

Write only a concise explanatory response based on the supplied inputs and return one JSON object that validates against `successor-response-schema-r1.json`.

The typed binding is the sole authority for route inputs. Do not use prose to change a bound value, add a value, select a route, or override the reference interpreter. Do not coerce values or blur JSON types or units.

An input is present only when it has a record in `bindings` and its ID is in `present_input_ids`. An input is missing only when its ID is in `missing_input_ids` and it has no record in `bindings`. Never invent or infer a missing value. Missing is not `null`, `false`, an empty string, or zero. `null` is present only when the policy explicitly permits the null type.

If a required input is missing and the reference trace is `fallback`, treat that fallback as valid. Keep the exact reference trace, report the missing input ID in plain language, and do not choose another route or claim the missing input's value.

Before returning a routed response, check whether the visible prose makes a direct, unambiguous assertion that contradicts a specific bound input. Do not infer a contradiction from vague or unrelated prose. If such a contradiction exists, return `INTERFACE_CONFLICT` with `PROSE_BINDING_CONFLICT`, a null response text, and a null route trace. Do not emit, copy, or repair a route trace in this case.

If the reference interpreter reports `ROUTE_AMBIGUOUS`, return `ROUTE_AMBIGUOUS` with a null response text, a null route trace, and the matching interface error. Do not choose between routes.

Otherwise return `ROUTED`; copy the reference interpreter's complete `route_trace` object verbatim. Do not omit fields, add fields, change IDs or hashes, or normalize it. A routed fallback may include missing required inputs. Explain the chosen route only from the reference trace and typed binding.

Do not discuss target criteria, evaluator outcomes, scores, labels, or policy effectiveness. Do not tune any behavior from such results. This prompt defines an interface shape only; it makes no claim about live successor behavior or transfer.
