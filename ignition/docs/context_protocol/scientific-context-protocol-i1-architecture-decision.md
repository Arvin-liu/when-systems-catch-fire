# SCIENTIFIC-CONTEXT-PROTOCOL-I1 Architecture Decision — Open Scientific Context Protocol

Status: stacked Draft candidate. Direct parent is `Q44-I1` at the frozen exact head declared in the task receipt.

## Decision

A minimal versioned local protocol can negotiate capabilities and exchange identity-, authority-, artifact-, failure-, retry- and boundary-bound scientific context without copying a platform or executing hardware actions.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `protocol_version`
- `source_rights_context`
- `model_tool_executor_identity`
- `authority_capability`
- `observation_prediction`
- `analogy_search_case`
- `intervention_failure`
- `symbolic_perspectives`
- `decision_integrity`
- `epistemic_state`
- `latent_multi_history_counterfactual`
- `experiment_hardware_request_result`
- `exact_head_provenance_digest`
- `stop_rollback`
- `sensitive_data_network_local_first`
- `capability_negotiation`
- `request_response_envelope`
- `identity_authorization`
- `artifact_binding`
- `failure_retry_semantics`
- `compatibility_policy`
- `local_mock_adapter`
- `claim_ceiling`

## Fail-closed rules

- `version_negotiated`
- `identity_authorized`
- `capability_not_authority`
- `artifact_exact_head_bound`
- `rights_preserved`
- `failure_retry_typed`
- `compatibility_fail_closed`
- `sensitive_local_first`
- `hardware_request_only`
- `no_ecosystem_overclaim`
- `stop_rollback_present`

## Explicit non-claims

- no deployed ecosystem
- no hardware execution
- no platform model copying
- no sensitive-data/network boundary bypass

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
