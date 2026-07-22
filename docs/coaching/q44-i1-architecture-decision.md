# Q44-I1 Architecture Decision — Coaching / Commitment Subcapability

Status: stacked Draft candidate. Direct parent is `Q43-I1` at the frozen exact head declared in the task receipt.

## Decision

A coaching subcapability can support user-declared informed commitments while preserving autonomy, consent, multiple narratives, process/outcome separation and revise/pause/stop rights.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `user_declared_goal`
- `informed_commitment`
- `plan_checkpoints`
- `deviations`
- `support_options`
- `revise_pause_stop`
- `non_manipulation_constraint`
- `multi_perspective_narrative`
- `autonomy_consent`
- `outcome_process_separation`
- `escalation`
- `claim_ceiling`

## Fail-closed rules

- `goal_user_declared`
- `commitment_informed`
- `consent_reversible`
- `no_goal_substitution`
- `no_shame_pressure`
- `multiple_narratives_preserved`
- `process_outcome_separate`
- `support_not_control`
- `escalation_boundary_enforced`

## Explicit non-claims

- no manipulative persuasion
- no hidden goal substitution
- no shame-driven compliance
- outcome does not prove intervention legitimacy

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
