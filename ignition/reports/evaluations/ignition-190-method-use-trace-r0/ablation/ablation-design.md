# Method vs facts/skill/template ablation design R0

## Status

This is a synthetic/offline design only. It has not run a model, Successor,
Evaluator, provider comparison, cross-model trial, or score aggregation.

All conditions use the same bounded synthetic facts. The only deliberate change
is the supplied artifact surface.

| Condition | Supplied | Withheld | Purpose |
| --- | --- | --- | --- |
| `FACTS_ONLY` | facts, task prompt, source fingerprint | method-use chain and skill artifact | establish what can be reconstructed from facts alone |
| `METHOD_TRACE` | same facts plus a complete source-bound trace | evaluator criteria and future transfer answer | test chain recovery and bounded use of a recorded method slot |
| `BROKEN_METHOD_TRACE_CONTROL` | same facts plus candidate/outcome excerpt with missing links | complete trace and evaluator criteria | detect false-positive completion and preserve missing links |
| `SKILL_ONLY` | none | skill artifact | `NOT_APPLICABLE`: no safe existing skill artifact in scope |

## Observable comparisons

The future evaluator may compare exact link recovery, missing-link detection,
false-positive completion, source/provenance fidelity, uncertainty preservation,
and whether the method-trace condition supplies an observable structural aid
beyond facts-only. No total score is defined. A valid method trace is not proof
of capability, causation, transfer, or inheritance.

Fixed boundaries:

- `CROSS_MODEL_TRANSFER_NOT_RUN`
- `SUCCESSOR_NOT_RUN`
- `EVALUATOR_NOT_RUN`
- `NO_CANONICAL_PROMOTION`
