# Q36-INT Typed Contract — Intervention–Failure Dynamics & Rollback

> Schema: `schemas/intervention/intervention-failure-dynamics-contract.schema.json`
> Validator: `tools/intervention/validate_intervention_failure_gate.py` (P1)
> Style: follows Q34 (`commitment-claim.schema.json`), Q35 (`responsibility-contract.schema.json`) and Q36-OBS (`observation-prediction-contract.schema.json`) — draft 2020-12, `additionalProperties: false`, stable id patterns, fail-closed enums.

## Objects

### 1. `intervention_request`

Records the *intent* to intervene, bound to prior governance artifacts. Key invariants:
`external_action` must be `false` (or equivalent boundary); the bound Q34 claim must be
`committed_current`; the bound Q35 grant must be resolvable, unexpired and scope-matching;
the bound Q36-OBS observation/residual must be validated and must respect `do_not_infer_cause`.

Required: stable id, initiator/proposer, Q34 claim ref, Q35 actor/grant/action/trajectory refs,
Q36-OBS observation/residual refs, target resource/system, normalized intervention type,
intended change, `mechanism_hypothesis` (must be marked hypothesis unless lawful causal evidence),
applicability scope, uncertainty, expected effect + evaluation window, claim ceiling,
exact-head / artifact digest, `proposed_at` / `authorized_at`, `external_action=false`.

### 2. `safety_envelope`

Freezes the guardrails before any execution. Missing/unverifiable fields fail closed.

Required: allowed target scope, max change magnitude, allowed side effects, forbidden surfaces,
prerequisites, stop conditions, abort conditions, observation cadence, authority escalation threshold,
rollback readiness, expiry.

### 3. `intervention_plan` / `execution_event`

Distinct lifecycle states (append-only; never mutated in place to a "success" after failure):
`proposed`, `authorized`, `dry_run`, `executing`, `observed`, `succeeded_within_scope`, `failed`,
`degraded`, `stopped`, `rolled_back`, `abandoned`, `unresolved`.

Execution event records: pre-state digest, exact command/normalized operation, executor,
start/end time, affected surfaces, actual change magnitude, output artifact digests, side effects,
stop-condition status, trajectory event hash, `no_silent_mutation` (append-only correction only).

### 4. `outcome_evaluation`

Binds the execution event to a Q36-OBS observation. Records expected vs observed effect,
evaluation method, baseline/comparator, uncertainty, residual change, unintended effects, scope validity,
evaluator/verifier, `causal_interpretation_status` ∈ {`NOT_IDENTIFIED`, `BOUNDED_MECHANISM_EVIDENCE`,
`ALTERNATIVE_EXPLANATIONS_REMAIN`}, and a hard `do_not_overclaim_causality` marker.

### 5. `failure_mode_record`

Preserves failures honestly. Required: failure id, intervention/action refs, failure type, trigger,
detected_at, affected surfaces, severity, reversibility, residual impact, responsibility state,
known/unknown cause, competing explanations, escalation target, Q39 failure-memory interface ref,
claim ceiling. `UNRESOLVED_MANY_HANDS` must be preserved honestly; a single fake owner is forbidden.

### 6. `stop_rollback_record`

Expresses stop/abort/rollback as NEW append-only events. Required: triggering stop condition,
stop authority, rollback plan ref, rollback action/trajectory, pre/post digests,
restored/not-restored surfaces, irreversible residue, verification result, follow-up restrictions,
history preservation. Rollback must not silently overwrite the original trajectory.

## Invariants enforced by the validator (P1)

1. Schema + required fields (fail closed).
2. Q34 bound claim is `committed_current` and its claim ceiling covers the intervention.
3. Q35 authority/grant/trajectory resolvable, unexpired, scope-matching; separation-of-duty satisfied for high-risk.
4. Q36-OBS observation/residual validated and `do_not_infer_cause=true` respected (residual ≠ cause).
5. Q33 rights/publication gate not bypassed for any source used by the intervention/result.
6. Target/scope/effect window match the bound observation.
7. Safety envelope, stop conditions, rollback plan complete (fail closed if missing).
8. `external_action=true` (real-world) fails closed — repository governance only.
9. Actual change does not exceed magnitude/surface envelope.
10. After a stop/abort condition triggers, no further execution may occur.
11. Failure / negative-effect / residual-impact records must not be deleted or rewritten to success.
12. `expected_effect` must not be modified after the outcome is recorded.
13. Outcome must include baseline/comparator and uncertainty.
14. Residual/correlation must not be upgraded to a unique causal mechanism.
15. Bounded pilot must not be externalized into universal real-world intervention capability.
16. Rollback must append a trajectory event and verify the restored scope.
17. `UNRESOLVED_MANY_HANDS` / `INSUFFICIENT_EVIDENCE` must not be forged into a single owner.
18. `unresolved` failures remain `unresolved` and enterable into the Q39 interface.
