# DECISION-INTEGRITY-I1 Architecture Decision — Principle Lock, Process Quality & Outcome-Bias Governance

Status: stacked Draft candidate. Direct parent is `SYMBOLIC-SPHERE-I1` at the frozen exact head declared in the task receipt.

## Decision

Principles, assumptions, decision order, risks and stop conditions can be frozen ex ante so process quality and outcome quality remain separately auditable after results appear.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `principle_registry`
- `principle_version`
- `revision_authority`
- `ex_ante_decision_record`
- `known_unknown_assumptions`
- `decision_hierarchy`
- `competence_boundary`
- `risk_reversibility_stop`
- `process_quality`
- `outcome_quality`
- `process_outcome_quadrant`
- `result_bias_audit`
- `post_hoc_narrative_diff`
- `principle_capture`
- `legitimate_revision`
- `usefulness_necessity_gate`
- `bargain_fomo_signal`
- `information_intake`
- `integration_evidence`
- `learning_update`
- `claim_ceiling`

## Fail-closed rules

- `success_not_process_proof`
- `failure_not_process_disproof`
- `ex_ante_record_immutable`
- `principle_relabel_blocked`
- `competence_required`
- `utility_before_bargain`
- `fomo_not_need`
- `intake_not_integration`
- `integration_requires_output`
- `revision_versioned_authorized`
- `original_record_preserved`
- `claim_ceiling_preserved`

## Explicit non-claims

- success does not prove process quality
- failure does not disprove a good process
- no investment advice
- information intake is not integration

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
