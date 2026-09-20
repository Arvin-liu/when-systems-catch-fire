# Method-Use Trace R0 existing-schema sufficiency audit

## Scope

This audit precedes any Method Registry or new global ontology. It compares the twelve required method-use chain slots against the exact Task189-head schemas and adjacent existing observation/failure/provenance/self-correction contracts.

The audit uses the bounded rule:

`Existing schema + minimal adapter` is preferred over a new global ontology.

## Verdict

- `DIRECTLY_REPRESENTABLE`: 3 slots
- `REPRESENTABLE_WITH_ADAPTER`: 6 slots
- `MISSING`: 3 slots
- `AMBIGUOUS`: 0 slots
- Sufficiency verdict: `EXISTING_SCHEMAS_INSUFFICIENT_FOR_AUDITABLE_METHOD_USE_CHAIN_WITHOUT_A_NARROW_ADAPTER`
- Proposed response: one task-local, noncanonical adapter/schema only; no global cognitive registry, universal method ontology, second provenance service, or parallel state machine.

The missing slots are selection rationale, selection-scoped context/constraints/alternatives, and revision rationale. The adapter-needed slots are the explicit use event, source/fingerprint binding at segment grain, expected-vs-observed distinction, causal/confounder boundary, explicit no-revision branch, and ordered rollback/reconstruction references. Existing R0 fields remain the authority-bearing source records; the adapter only makes a trace reconstructable and testable.

## Existing field surfaces audited

- Cognitive IR: `ignition/agent_runtime/cognitive_inheritance_r0/schema/cognitive-ir-r0.schema.json`
  - `METHOD` objects; generic relations; required provenance, uncertainty, claim ceiling, lifecycle, and migration lineage.
- Cognitive Transition R0: `ignition/agent_runtime/cognitive_inheritance_r0/schema/cognitive-transition-r0.schema.json`
  - `new_method`, `observed_anomaly_or_failure`, `disposition`, `migration_lineage`, `unknowns`, and `independent_evaluation_status=NOT_RUN`.
- Provenance: `ignition/schemas/ignition-provenance-entry.schema.json`
  - source identity and digest fields, but not a trace-segment sequence.
- Observation/failure: `ignition/schemas/operations/live-observation-outcome-r1.schema.json`, `ignition/schemas/failure-case-evidence-gate.schema.json`, and `ignition/data/schemas/failure_typology.schema.json`.
  - typed observations/failures exist but do not say that a method was selected or used.
- Migration/self-correction: `ignition/agent_runtime/cognitive_inheritance_r0/schema/migration-record-r0.schema.json` and `ignition/data/governance/self-correction/`.
  - rollback and repair lineage exist as separate contracts; they do not provide a method-use event.

## Negative authority boundary

A valid Cognitive IR object, a `TRANSFERS_TO` relation, a failure record, a transition disposition, schema validity, or a green mechanical check cannot be read as method use, causation, inheritance, general cognitive capability, R1 authorization, or canonical truth.

Fixed statement:

`METHOD_USE_TRACE_IS_EVIDENCE_ARTIFACT_NOT_CAPABILITY_PROOF`.

The full slot-by-slot evidence and exact refs are in `method-use-schema-sufficiency.jsonl`.