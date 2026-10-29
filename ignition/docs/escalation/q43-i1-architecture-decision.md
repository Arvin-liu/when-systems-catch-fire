# Q43-I1 Architecture Decision — Graded Intervention & Professional Escalation

Status: stacked Draft candidate. Direct parent is `Q42-I1` at the frozen exact head declared in the task receipt.

## Decision

Actions can be classified by risk, reversibility, evidence, authority and expertise so only repository-local reversible actions are automatic and high-risk external actions become request-only escalations.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `action_risk_class`
- `reversibility`
- `evidence_grade`
- `authority`
- `expertise_requirement`
- `automatic_repository_local_action`
- `user_confirmation_required`
- `expert_escalation`
- `institutional_approval`
- `prohibited_action`
- `request_only_external_action`
- `stop_rollback_result_return`
- `claim_ceiling`

## Fail-closed rules

- `risk_class_required`
- `reversibility_required`
- `evidence_grade_required`
- `authority_required`
- `expertise_boundary_enforced`
- `automatic_only_repository_local`
- `confirmation_for_external`
- `high_risk_request_only`
- `prohibited_never_executed`
- `stop_rollback_return_present`

## Explicit non-claims

- no legal action
- no medical action
- no financial action
- no safety-critical external action

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
