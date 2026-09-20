# Complexity, retirement, and protocol freeze

## Protocol decision

- `R0.1`, `R0.2`, and `R0.3` remain historical protocol evidence.
- `R0.4` is the current experimental evaluation baseline.
- Task190 adds only a method-use experiment layer.
- No `R0.5` evaluation protocol is created.
- `EVALUATION_PROTOCOL_VERSION_CONSOLIDATION_CANDIDATE` is recorded as a future
  review candidate; it is not executed and does not delete historical evidence.

## Complexity decision

Task190 adds one task-local schema and one task-local validator. It adds zero
global schemas, global method registries, universal ontologies, parallel state
machines, second provenance services, or canonical claim IDs. Existing R0,
Cognitive IR, Transition, provenance, observation, failure, migration, and
self-correction surfaces remain unchanged.

The exact schema consumer is the future successor-visible reconstruction and
independent evaluator preparation surface. The validator consumes synthetic
fixtures and manifests only. The exact missing-slot argument and retirement
conditions are in `complexity-retirement.json`.

## Ceiling

A smaller representation is not adopted merely because the adapter serializes
cleanly. Retirement requires an authorized round-trip and missing-link control
that proves existing fields are sufficient for all twelve slots. No successor,
evaluator, R1, cross-model trial, Model-RSI, weight training, or canonical
promotion is performed in Task190.
