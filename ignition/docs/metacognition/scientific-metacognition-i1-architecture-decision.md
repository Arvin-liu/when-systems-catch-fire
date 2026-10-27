# SCIENTIFIC-METACOGNITION-I1 Architecture Decision — Scientific Metacognition & Epistemic-State Control Plane

Status: stacked Draft candidate. Direct parent is `DECISION-INTEGRITY-I1` at the frozen exact head declared in the task receipt.

## Decision

Epistemic states and unknowns can be ranked and transitioned through authorized evidence acquisition with deterministic replay, bounded cost/risk/time and explicit replanning.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `epistemic_state_ledger`
- `committed_knowledge`
- `candidate_hypotheses`
- `conflicts`
- `retracted_states`
- `insufficient_evidence`
- `not_searched`
- `temporarily_unobservable`
- `structurally_unobservable`
- `non_identifiable`
- `known_unknowns`
- `unknown_acquisition_paths`
- `visibility_bias`
- `decision_integrity_risk`
- `unresolved_failures`
- `cost_risk_time_priority`
- `stop_condition`
- `evidence_requirement`
- `next_action_type`
- `voi_like_ranking`
- `authorized_acquisition_plan`
- `feedback_transition`
- `replanning`
- `claim_ceiling`

## Fail-closed rules

- `self_rating_not_evidence`
- `unknown_needs_evidence_transition`
- `non_identifiable_not_solved`
- `dominant_view_not_fact`
- `good_outcome_not_bad_process_erasure`
- `failure_changes_plan`
- `retracted_not_active`
- `plan_authorized_and_stopped`
- `exploration_bounded`
- `cost_risk_present`
- `ceiling_noninflation`
- `no_circular_evidence`

## Explicit non-claims

- model self-rating is not evidence
- non-identifiable is not solved
- dominant discourse is not fact
- planning is not external execution

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
