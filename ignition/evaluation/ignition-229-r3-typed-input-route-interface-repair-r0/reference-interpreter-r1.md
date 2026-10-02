# Deterministic Reference Interpreter R1

The Python standard-library implementation in `tools/route_reference_interpreter.py` accepts a frozen policy JSON and a typed binding JSON. It reads no natural-language case prose, target criteria, evaluator material, scores, or labels.

For valid inputs it returns the expected `route_trace`, every stop/selector condition result, each route-condition-set result, and an explicit missing-input report. It hashes the policy's exact file bytes and the canonical typed-binding object. Canonical JSON is UTF-8, recursively sorted object keys, compact separators, `ensure_ascii=false`, and finite JSON numbers only.

`tools/validate_route_trace_r1.py` uses the same frozen inputs to generate the reference result and compares the candidate trace field-for-field. It rejects missing or extra fields, duplicate IDs, wrong route IDs/actions, wrong hashes, absent IDs in `evaluated_input_ids`, and any other semantic difference. It never repairs or normalizes a candidate trace.

## Fail-closed behavior

Unknown operators, undeclared IDs, ambiguous type declarations, type/unit mismatches, malformed provenance, and invalid missingness produce a coded failure. Multiple fully matching routes or a stop-selector conflict produce `ROUTE_AMBIGUOUS` with the condition evaluations and missing-input report preserved and no route trace. `PROSE_BINDING_CONFLICT` produces `INTERFACE_CONFLICT` and no route trace.

## R1 deterministic check

A synthetic all-present boolean fixture selected `READY_RULE` as `selector` in two interpreter runs. Both canonical expected trace byte strings had SHA-256 `74c733c45c7563d6579c309c45c7ed29178344bb519ed7fa59342aab1c171235`; byte comparison passed. The semantic validator accepted the reference trace. The fixture is synthetic and target-blind; this check makes no claim about live successor behavior.

Run from the R3 subtree's repository root after creating explicit policy, binding, and trace JSON files:

```text
python3 ignition/evaluation/ignition-229-r3-typed-input-route-interface-repair-r0/tools/route_reference_interpreter.py --policy POLICY.json --binding BINDING.json
python3 ignition/evaluation/ignition-229-r3-typed-input-route-interface-repair-r0/tools/validate_route_trace_r1.py --policy POLICY.json --binding BINDING.json --trace ROUTE-TRACE.json
```
