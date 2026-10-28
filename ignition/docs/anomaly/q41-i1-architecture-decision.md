# Q41-I1 Architecture Decision — World-Feedback Anomaly Trigger & Governance

Status: stacked Draft candidate. Direct parent is `SCIENTIFIC-METACOGNITION-I1` at the frozen exact head declared in the task receipt.

## Decision

Recurring evidence-bound expected/observed divergence can trigger a bounded continue/repair/downgrade/rebuild/search decision without automatically inventing a hidden system.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `world_feedback_anomaly`
- `recurrence_window`
- `residual_failure_aggregation`
- `expected_observed_divergence`
- `model_repair_budget`
- `governance_decision`
- `escalation_authority`
- `stop_rollback`
- `q39_update`
- `metacognition_update`
- `claim_ceiling`

## Fail-closed rules

- `anomaly_not_hidden_system`
- `recurrence_required`
- `threshold_declared`
- `single_deviation_no_rebuild`
- `repair_budget_bounded`
- `authority_required`
- `stop_rollback_present`
- `failure_sampling_balanced`
- `q39_updated`
- `metacognition_updated`

## Explicit non-claims

- single residual is not a hidden system
- anomaly is not causal proof
- no threshold-free escalation
- no selective failure sampling

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
