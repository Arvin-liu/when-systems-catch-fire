# Q39-I1 Interfaces

## Inputs

Q39 accepts typed candidates from Q36 observation/intervention failure surfaces, Q37 audit mismatches and retractions, and Q38 `q39_failure_exports`. Each candidate must bind `originating_task`, `originating_artifact`, a 40-hex exact head, negative evidence and affected claims/actions.

## Lineage

`failure_event -> repair_proposal -> repair_event -> propagation_targets -> downstream_plan_effects -> closure_or_unresolved_residue`.

Events are append-only and hash chained. A repair appends a new event; it never overwrites the failure. Supersession preserves both event ids. Closure requires verified propagation to every declared affected object and retains the prior negative record.

## Outputs

- downstream plan effects: `SEARCH`, `PREDICT`, `ANALOGY_AUDIT`, `INTERVENE`, `ESCALATE`, `DEFER`, or `CLAIM_CEILING_CHANGE`;
- recurrence signatures for deterministic repeat detection;
- unresolved residue for Scientific Metacognition;
- environment/theory distinction for Q41 anomaly aggregation;
- claim-ceiling impacts limited to `HOLD`, `DOWNGRADE`, or `RETRACT`.

No output authorizes a real-world retry or external action.
