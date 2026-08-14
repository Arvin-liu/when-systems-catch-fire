# REOS vNext minimal kernel R1 — frozen contract

Status: `CONTRACT_FROZEN_BEFORE_IMPLEMENTATION`

This contract is scoped to one bounded `REOS_LIGHT` research case. It is a research-execution control surface, not a source, claim, evidence, proof, ceiling, normative, publication or epistemic authority.

## Identifiers and serialization

- schema version: `reos.vnext.minimal-kernel.r1`;
- serialization: UTF-8 canonical JSON, `sort_keys=true`, compact separators, `ensure_ascii=false`, one trailing newline;
- case document is the only persisted REOS document in R1;
- nested typed rows are append-only by identifier; no separate canonical activation, claim, evidence, review or handoff store;
- implementation namespace: `reos_vnext/`;
- command entry point: `python3 -m reos_vnext`.

## Case document shape

The document contains:

```text
schema_version
case.case_id
case.activation                  # embedded ActivationDecision
case.question_contract           # preregistration ref/digest + compact frozen/current validation summaries
case.owner_boundary
case.budget_contract
case.stop_conditions
case.case_state                  # case state only
case.obligations[]               # one append-only ResearchObligation ledger
case.artifact_refs[]             # thin references only
case.evidence_requests[]         # retrieval state only
case.claim_candidates[]          # noncanonical annotations only
case.reviews[]                   # one append-only review stream
```

`HandoffBundle` is a deterministic projection returned by the API/CLI from the validated case; it is not a case-owned acceptance or publication state.

QuestionContract is intentionally compact. It persists:
- `preregistration_ref` and an external `preregistration_digest` that binds that reference to the compact frozen validation summary;
- immutable `frozen_validation_summary` and `current_validation_summary`, each with exactly `question`, `scope`, `estimand`, `measurement_boundaries`, `claim_ceiling` and `stop_conditions`;
- the current and initial summary digests plus an append-only amendment chain. The current summary may differ from the frozen summary only through a versioned amendment; replacing the frozen summary and its local digests without changing the external preregistration binding is invalid.

The full preregistration, source ledger and claim registry remain outside the REOS case. The summary is a validation boundary, not a second canonical research record.

For deterministic R1 validation, the binding digest is the SHA-256 of canonical JSON containing exactly `preregistration_ref` and `frozen_validation_summary`; the full preregistration bytes remain external and are not copied into the case.

## Typed state sets

Activation modes: `DIRECT_RESEARCH`, `REOS_LIGHT`, `REOS_FULL`.

R1 activation permits `DIRECT_RESEARCH` and `REOS_LIGHT`. `REOS_FULL` is rejected as `DEFERRED_UNAVAILABLE_IN_R1`; it is not a maturity rank.

Case states: `OPEN`, `OPEN_WITH_REPAIR_OBLIGATIONS`, `HANDOFF_READY_WITH_BOUNDED_RESULTS`, `HANDOFF_READY_WITH_EXPLICIT_RESIDUALS`, `BLOCKED_BY_EVIDENCE_ACCESS`, `NOT_IDENTIFIABLE_WITH_AVAILABLE_EVIDENCE`, `STOPPED_BY_BUDGET_OR_SCOPE`, `REQUIRES_QUESTION_REFORMULATION`, `NO_INCREMENTAL_VALUE_OBSERVED`, `ABSTAINED`.

Obligation states: `OPEN`, `READY`, `WAITING_DEPENDENCY`, `WAITING_REVIEW`, `BLOCKED_TOOL_OR_ACCESS`, `SATISFIED_WITH_SCOPE`, `SATISFIED_WITH_RESIDUALS`, `ABSTAINED`, `CLOSED_NO_RESULT`.

Evidence retrieval states: `REQUESTED`, `CANDIDATE_FOUND`, `FULLTEXT_RECOVERED`, `PARTIAL_ACCESS`, `METADATA_ONLY`, `SOURCE_NOT_RECOVERED`, `SOURCE_IDENTITY_AMBIGUOUS`, `BLOCKED`, `NOT_APPLICABLE`.

Review verdicts: `PASS_WITHIN_QUESTION_SCOPE`, `PASS_WITH_EXPLICIT_RESIDUALS`, `MATERIAL_REPAIR_REQUIRED`, `BLOCKED_MISSING_INPUT`, `ABSTAIN`, `DISAGREEMENT_REQUIRES_ADJUDICATION`.

No state named `SUCCESS` is legal. Case, obligation, evidence and review states are separate namespaces and never imply one another.

## Required invariants

1. `case_state` is not an obligation, retrieval or review state.
2. `owner_boundary` is exactly `GPT_OWNER_REVIEW_ONLY`; Owner acceptance remains external to REOS.
3. Obligation dependencies are acyclic and never imply truth inheritance.
4. Question amendments append `{from_digest, to_digest, reason, version}` against the compact validation-summary digest chain; silent replacement is invalid.
5. Artifact references require thin provenance (`kind` and `retrieved_at`), scope and privacy/publication class; REOS stores no source blob or evidence maturity.
6. Evidence retrieval state cannot set truth, proof, causal identification, external validity, claim ceiling or acceptance.
7. Claim candidates are explicitly `NONCANONICAL` and cannot be promoted by REOS.
8. Review decisions require a named question and independence declaration; `ABSTAIN` is legal; a decision is append-only and cannot overwrite an earlier decision; reviewer agreement cannot set Owner acceptance.
9. A material review finding must reference a repair obligation or remain an explicit residual.
10. Handoff projections require receiving authority, provenance/object refs, current noncanonical status where applicable, scope/ceiling, residuals and prohibited inference.
11. Provider/model identifiers are telemetry only and cannot be required capabilities in R1.
12. Privacy classes and prohibited inference are validated locally; public publication remains the existing Results Book/publication authority.
13. Validators and JSON loaders are fail-closed for malformed state, including duplicate object keys, and do not adjudicate external truth.
14. Budget contracts are closed to the bounded operator-accounted fields; nested canonical or evidence stores are rejected.
15. Handoff `allowed_claims` cannot contradict its noncanonical/prohibited-inference boundary.

## Deliberately absent from R1

`ExecutionPacket`, `ExecutorLease`, `ResumeCapsule`, continuous supervisor/heartbeat state, idempotency runtime, distributed queue, broad evidence adapters, automatic budget optimizer, UI/dashboard, provider lock-in, second canonical claim/evidence store and REOS-owned `EPISTEMICALLY_ACCEPTED` are not implemented or represented as available runtime features.

## Frozen negative fixture IDs

The negative fixture manifest at `tests/fixtures/reos_vnext/negative_cases.json` is frozen before behavior implementation. Every fixture must fail closed with a stable error code:

`CYCLE`, `UNKNOWN_DEPENDENCY`, `QUESTION_MUTATION`, `EVIDENCE_TRUTH_UPGRADE`, `REVIEW_OWNER_ACCEPTANCE`, `CANONICAL_CLAIM_MASQUERADE`, `HANDOFF_PROHIBITED_INFERENCE`, `PROVIDER_HARD_DEPENDENCY`, `FULL_UNAVAILABLE`, `ARTIFACT_PROVENANCE`, `CONFLICTING_STATE_NAMESPACE`, `GENERIC_SUCCESS`.

The pilot may produce `NO_INCREMENTAL_VALUE_OBSERVED`; this is a permitted bounded process conclusion and not generic completion.
