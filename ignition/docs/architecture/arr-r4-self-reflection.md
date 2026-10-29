# ARR R4 — WAIC Corpus-Scale Self-Reflection and Failure-Attribution R1

- task_id: `ARR-R4-WAIC-SELF-REFLECTION-R1-RELAY-20260725`
- control_commit: `e8530a7d87f13ef09cea58d34f6f548a695d7955`
- predecessor: R3 (`d6719a74859f278b6166b11e6bd5235c2fa46879`, PR #126, DRAFT)
- terminal_verdict: `ARR_R4_WAIC_SELF_REFLECTION_DRAFT_AWAITING_EXTERNAL_REVIEW`
- authorization boundary: R4 only. No R5, no PROMOTE/EVOLVE/Ready/merge/Main change/force push.

This document is the **public, non-private** R4 report. It contains only counts,
distributions, dispositions and structural facts. No note titles, raw text,
transcript content, URL lists or reconstructive features appear here; those live
only in the 1111 private evidence branch.

## 1. Why R4 exists

R3 proved **operational scale properties** (deterministic inventory, sharding,
processing, receipting of 836 notes with no silent disappearance, source
mutation, leak, real-world action, PROMOTE or EVOLVE). It did **not** prove
semantic understanding, independent verification, causal modeling, temporal
resolution, or promotion-worthiness. R4 answers: *what did the system actually
succeed at, what remained unknown, which weaknesses belong to the material or
evidence, which to extraction/representation, which are metric/observability
defects, which are runtime defects, and which — only after lower-level
alternatives are excluded — qualify as architecture candidates?*

R4 consumes the **frozen** R3 evidence; it does not improve or rerun the corpus.

## 2. Four-axis outcome model

For each of the 836 objects R4 derives exactly one status on each of four axes,
without rewriting the R3 receipt.

| Axis | Distribution over 836 | Note |
|------|----------------------|------|
| Pipeline | `PIPELINE_COMPLETE` 836 | All R3 outcomes recorded SUCCESS. |
| Semantic | `SEMANTIC_REPRESENTATION_LIMITED` 836, `SEMANTIC_REPRESENTATION_SUFFICIENT` 0 | R3 assigned a `claim_class` (representation) but performed **no** semantic-understanding/verification step. All are limited; none sufficient. |
| Evidence | `SOURCE_DEPENDENT` 545, `AUTHOR_OR_SPEAKER_REPORT` 276, `TRANSCRIPT_OR_INTERPRETER_INFERENCE` 15, `INDEPENDENTLY_SUPPORTED` 0 | 0 objects reach independent support — there is no independent verification in the sealed evidence. |
| Governance | `BOUNDARY_HELD` 27, `CONSENT_OR_RIGHTS_LIMITED` 809, `ACTION_PROHIBITED` 0 | Safety boundary held for all; 809 source-less notes cannot have consent/rights verified. |

**Invariant (test-guarded):** `PIPELINE_COMPLETE` never implies
`SEMANTIC_REPRESENTATION_SUFFICIENT`; `INDEPENDENTLY_SUPPORTED` is never assigned
without sealed independent verification; a repeated/source-dependent note is never
upgraded to independent support; a transcript inference is never upgraded to
verified fact or speaker belief.

## 3. Mandatory metric contradictions (all resolved)

R4 recomputed each apparent contradiction from the sealed ledgers and assigned
exactly one disposition. None are unresolved.

| ID | Contradiction | Disposition |
|----|---------------|-------------|
| M1 | `outcome_counts.SUCCESS = 836` while semantic verification absent | `DEFINITION_CORRECT_VALUE_MISREAD` |
| M2 | `unknown_retention = 0` while 449 event times UNKNOWN | `DEFINITION_CORRECT_VALUE_MISREAD` |
| M3 | `crash_recovery_success_rate = 0.0` while 3 demos passed | `AGGREGATION_DEFECT` |
| M4 | `incremental_selectivity = 0.0` while 1/836 reprocessed | `AGGREGATION_DEFECT` |
| M5 | capability `all_pass = true` but no semantic coverage | `REPORTING_DEFECT` |
| M6 | 836 notes vs ~9 independent sources | `DEFINITION_CORRECT_VALUE_MISREAD` |

**Key R4 finding (M3/M4):** an internal R3 cross-report inconsistency.
`AGGREGATE_METRICS.json` reports `crash_recovery_success_rate = 0.0` and
`incremental_selectivity = 0.0`, but the authoritative `CORPUS_RUN_LEDGER.json`
reports `1.0` and `0.001196` (and `CRASH_RECOVERY_REPORT` / `INCREMENTAL_RERUN_REPORT`
confirm the demos passed). The aggregate uses a different denominator and
understates demo success → `AGGREGATION_DEFECT`.

## 4. Capability-coverage reinterpretation

`all_pass = true` aggregates 27 **operational / safety / governance** checks. It
does **not** assert semantic or evidence coverage.

- operational_coverage: 27/27 pass (measured)
- semantic_coverage: 0 items measured (R3 performed no semantic-understanding stage)
- evidence_coverage: `INDEPENDENTLY_SUPPORTED` = 0 (measured)
- governance_coverage: boundary held 836/836, 0 prohibited actions (measured)

## 5. Limitation attribution (primary class + exclusion)

Every observed weakness gets one primary class with an exclusion record.

| ID | Primary class | Excluded as |
|----|---------------|-------------|
| L1 | `TEMPORAL_LIMITATION` | not MATERIAL (dates absent in source), not RUNTIME (never guessed), not ARCHITECTURE (source property) |
| L2 | `SOURCE_DEPENDENCY_LIMITATION` | not RUNTIME (concentration in host map), not ARCHITECTURE |
| L3 | `REPRESENTATION_LIMITATION` | not RUNTIME (completed), not ARCHITECTURE (measurement-only by contract) |
| L4 | `METRIC_OR_OBSERVABILITY_DEFECT` | not RUNTIME (pipeline correct), not ARCHITECTURE (reporting fix) |
| L5 | `RIGHTS_OR_ACCESS_LIMITATION` | not ARCHITECTURE (provenance property), not RUNTIME (boundary held) |

## 6. Architecture-candidate gate — default NO_EVOLVE

The eight-condition gate (§7) is implemented and mutation-tested. **R4 produces
0 architecture candidates.** Every observed weakness is explained by a lower-level
class, so the gate's `not_explained_by_lower_level` / `primitives_cannot_represent`
/ `lower_cost_adapter_insufficient` conditions fail. R4 does not implement any
candidate and does not start R5.

## 7. Red-line adherence (counters)

`EVOLVE_CALLS=0`, `PROMOTE_CALLS=0`, `REAL_WORLD_ACTIONS=0`, `WAIC_CORPUS_RERUNS=0`,
`MAIN_CHANGES=0`, `FORCE_PUSHES=0`, `HISTORY_REWRITES=0`, `R5_STARTED=0`,
`EXTERNAL_ACCEPTANCE_CLAIMED=0`, `PRIVATE_CONTENT_PUBLICATION_EVENTS=0`.

## 8. Next step (R5 candidates, not implemented)

See `R5_AUTHORIZATION_CANDIDATES.md` (private evidence): semantic-understanding
stage, source-provenance/consent verification, and metric-definition hardening are
requested as future, separately authorized work. R4 does not self-declare
`EXTERNALLY_ACCEPTED_FOR_NEXT_ITERATION`.
