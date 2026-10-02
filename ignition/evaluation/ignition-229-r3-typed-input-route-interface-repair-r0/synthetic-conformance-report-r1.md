# Synthetic Route Interface Conformance R1

Result: `25/25` synthetic fixtures produced their expected outcome: 10 valid route fixtures passed the interpreter and validator; 15 negative fixtures failed closed with the expected reason. Rebuilding every binding and interpreter result was byte-deterministic.

The fixture corpus is authored independently of the historical Task229 cases. It uses synthetic IDs and values only; the runner rejects the corpus if it contains target, evaluator, score, or sealed-result material. No live successor or evaluator ran.

## Coverage

- Selector match and all-present fallback.
- Missing selector input; a missing boolean does not become false; explicit false remains present and can select stop.
- Explicit null only under an explicitly nullable policy type; null remains distinct from absence.
- Stop match and missing stop input.
- Multiple selector matches and stop-selector conflict return `ROUTE_AMBIGUOUS` without a route trace.
- Unknown and duplicate mapping IDs, incomplete mapping, unresolved source pointer, type mismatch, and unit mismatch fail closed.
- Preserved-baseline mismatch, absent ID contamination of `evaluated_input_ids`, and duplicate trace IDs are rejected.
- A synthetic prose/binding conflict records `PROSE_BINDING_CONFLICT`; the bound boolean stays true and the interpreter emits no route trace.
- Unknown policy operator and unknown type fail closed.

Machine evidence is in `synthetic-conformance-report-r1.json`; the source fixture corpus is `fixtures/synthetic-route-conformance-r1.json`.

## Reproduction

Run from the repository root:

```text
python3 ignition/evaluation/ignition-229-r3-typed-input-route-interface-repair-r0/tools/run_synthetic_conformance.py --output ignition/evaluation/ignition-229-r3-typed-input-route-interface-repair-r0/synthetic-conformance-report-r1.json
```

This establishes synthetic interface conformance only. It does not establish live model behavior, target compatibility, transfer, policy effect, causality, revision generation, cross-model transfer, Model-RSI, or training benefit. Task230 remains unauthorized.
