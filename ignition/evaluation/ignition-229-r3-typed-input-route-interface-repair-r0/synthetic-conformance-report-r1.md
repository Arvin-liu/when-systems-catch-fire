# Synthetic Route Interface Conformance R1

Result: `48/48` synthetic fixtures produced their expected outcomes: 18 valid route fixtures passed the interpreter and validator; 30 negative fixtures were rejected at the expected boundary. Rebuilding bindings and interpreter results was byte-deterministic.

The fixture corpus uses synthetic IDs and values only. The runner rejects result-material terms in the corpus. No live successor or evaluator ran.

## Coverage

- Missing values stay distinct from explicit `null`, `false`, `0`, and the empty string. Boolean values do not pass integer declarations; number tests cover negative zero, integer input under a number declaration, the largest finite double, overflow to infinity, and non-finite rejection. Unit mismatches fail closed.
- Unknown and duplicate mapping IDs, unresolved and malformed JSON Pointers, and incomplete mappings fail closed.
- Multiple selector matches and stop-selector conflicts emit no route trace. Fallback remains valid with missing inputs; a no-match condition dominates a missing condition.
- Missing-ID contamination is rejected both in an input binding and in candidate trace IDs.
- Candidate traces with a wrong policy hash, binding hash, baseline action ID, selected rule ID, or selected action ID fail validation. Missing or extra trace fields and duplicate trace IDs are rejected.
- Binding policy-hash mismatch and malformed source-case or builder provenance fail closed.
- Contradictory synthetic prose produces `PROSE_BINDING_CONFLICT`; vague prose leaves the typed route unchanged.
- The JSON loader rejects a non-finite constant, and the binding builder rejects an overflowed numeric value.

Machine evidence is in `synthetic-conformance-report-r1.json`; the source fixture corpus is `fixtures/synthetic-route-conformance-r1.json`.

## Reproduction

Run from the repository root:

```text
python3 ignition/evaluation/ignition-229-r3-typed-input-route-interface-repair-r0/tools/run_synthetic_conformance.py --output ignition/evaluation/ignition-229-r3-typed-input-route-interface-repair-r0/synthetic-conformance-report-r1.json
```

The runner also rebuilds each valid binding and interpreter result twice and compares canonical bytes. Re-running the command produces a byte-identical machine report.

This establishes synthetic interface conformance only. It does not establish live model behavior, target compatibility, transfer, policy effect, causality, revision generation, cross-model transfer, Model-RSI, or training benefit. Task230 remains unauthorized.
