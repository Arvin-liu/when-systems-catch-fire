# F15-D1-I1 Architecture Decision — Latent-System Discovery & Identifiability Gate

Status: stacked Draft candidate. Direct parent is `Q41-I1` at the frozen exact head declared in the task receipt.

## Decision

Latent-system candidates and equivalent decompositions can remain candidate objects until distinguishing evidence passes an explicit identifiability gate.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `latent_system_candidate`
- `cross_system_ancestor_graph`
- `missing_system_search_plan`
- `identifiability_gate`
- `observational_signature`
- `equivalent_decompositions`
- `distinguishing_evidence_request`
- `candidate_status`
- `contradictions`
- `unsupported_elements`
- `claim_ceiling`

## Fail-closed rules

- `residual_not_entity`
- `pattern_not_common_cause`
- `equivalent_decompositions_preserved`
- `distinguishing_evidence_required`
- `non_identifiable_stays_unresolved`
- `contradictions_preserved`
- `unsupported_not_promoted`
- `claim_ceiling_preserved`

## Explicit non-claims

- residual is not a latent entity
- shared pattern is not a common cause
- non-identifiable decomposition remains unresolved
- no Q45+ numbering

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
