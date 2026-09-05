# IGNITION-20260905-155 result

Result status: `RESEARCH_COMPLETE / PARTIAL_INCREMENT / DRAFT_PR_PENDING_REVIEW / NON_CURRENT`

Task155 ran a data-level temporal blind test of the research-only `CROSS_CONTRACT_REVIEW_MAP` against 27 real repository events before the Task153 boundary. The corpus was frozen before unblinding, split deterministically into 20 discovery and 7 holdout cases, and scored with separate existing-contract-only and cross-contract passes.

The unblinded classifications are: 2 `INCREMENTAL_TRUE_POSITIVE`, 9 `REDUNDANT_TRUE_POSITIVE`, 2 `FALSE_POSITIVE`, 10 `TRUE_NEGATIVE_CONTROL_PASS`, 1 `MISS_FALSE_NEGATIVE` and 3 `UNDECIDABLE`. Both incremental signals are holdout cases from different families: CC-012 (Hermes timeout consequence/accountability binding) and CC-026 (Task150 Base/Delta admission scope). CC-020 is a concrete miss where a PASS cross-surface audit preceded four identity/projection failures.

Diagnostic dispositions:

- `PROVENANCE_WITHOUT_CEILING`: `SINGLE_CASE_SIGNAL`
- `ABSTENTION_AS_AVOIDANCE`: `FALSE_POSITIVE_PRONE`
- `BUDGET_AS_HARM_LICENSE`: `NO_HISTORICAL_SUPPORT`
- `SIGNATURE_WITHOUT_CONTESTABILITY`: `INSUFFICIENT_EVIDENCE`
- `COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY`: `SINGLE_CASE_SIGNAL`

Bounded verdict: `PARTIAL_INCREMENT`, with `CROSS_CONTRACT_FAILURE_SIGNAL_CONFIRMED` only as a research observation for CC-012 and CC-026. Keep `EXISTING_FEDERATED_CONTRACTS + CROSS_CONTRACT_REVIEW_MAP` as a non-canonical review lens. Do not add a failure class, canonical layer, schema, validator, gate, registry, runtime state, capability or authority.

The exact Task154 baseline is `56e57906ef6e54c3721499430aaec8da1182c322`; blind freeze commit is `6618f0b8d5dee9a63e2970c470da95eefc59f4f4`. Stale `1111/instructions/CURRENT.md` and `1111/relay/current` were preserved unchanged as a preflight residual. The formal candidate remains Draft and non-Current; final Git/CI/PR and independent 1111 receipt observations are separate evidence planes.
