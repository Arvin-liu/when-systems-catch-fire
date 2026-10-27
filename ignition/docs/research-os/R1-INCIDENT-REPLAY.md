# R1 Incident Replay — Eight Rounds through the Research Executive OS

Status: **CANDIDATE (Task 115 Line A, Draft phase)** — `R2_EMPIRICAL_CALIBRATION_PENDING`

This document is not acceptance of R1. R1 is failure evidence. The replay
shows what the Research Executive OS would have done had it been in control
during the overnight campaign.

## 1. Replay identity

- R1 campaign: `POINTFIRE-OVERNIGHT-PUBLIC-EVIDENCE-RESEARCH-CAMPAIGN-20260803-R1`
- R1 branch: `research/overnight-public-evidence-20260803-r1`
- locked replay tip: `232299483f701e8304265c1484b5b50e5dcf2799` (mandatory Task 115 source lock; the branch has since advanced to `495b4304`, replay is frozen at the locked tip)
- replay tool: `tools/research_os/r1_replay.py` (deterministic; reads exported `ROUND.json` / `SOURCES.jsonl` / `STATUS.json` only)
- machine episodes: `data/operations/iterations/115/candidate/r1-replay/round-001..008.json` + `REPLAY-SUMMARY.jsonl`
- executor/model: Qwen 3.8 Max campaign Line A; replay is a kernel + diagnosis + scheduler computation, no LLM judgment inside the loop

## 2. What the OS saw

For each round the builder derives episode signals strictly from committed R1
metadata; nothing is invented:

- elapsed time = `end_time - start_time` from `ROUND.json`;
- batch timestamps: all `accessed_at` values inside a round identical
  (`source_timestamps_identical`), which cannot prove reading;
- declared reading window = the elapsed window itself (the only window that
  existed); the floor is a documented conservative lower bound of 0.5 hours of
  full-text reading per source;
- obligations: a listed URL is identification, not verified access, so
  `PRIMARY_SOURCE` is `PARTIAL` at best; every other pack-required obligation
  is `OPEN` because the R1 metadata contains no full-text access record, no
  recomputation, no adversarial search and no independence accounting;
- campaign closeout: `STATUS.json` declares `COMPLETE_AWAITING_GPT_OWNER_ADJUDICATION`
  with `completed_rounds: 8` at ~03:12 against the authorized deadline of
  10:00 the same day.

Data-integrity note: round-002 `ROUND.json` at the locked tip is not valid
JSON (missing comma after `report_sha256`). The replay applies a documented
syntactic-only repair and records the failure and repair in the episode
provenance. This defect is itself an R1 finding.

## 3. Results

| round | slug | strategy pack | elapsed (h) | gap findings | OS verdict | selected action |
|---|---|---|---|---|---|---|
| 1 | ai-weather-extremes | QUANTITATIVE_DATA_RECONCILIATION | 0.0231 | 12 | REJECTED_AS_COMPLETED | ESCALATE_TO_GPT_OWNER |
| 2 | handwriting-learning | SYSTEMATIC_EVIDENCE_SYNTHESIS | 0.0792 | 11 | REJECTED_AS_COMPLETED | ESCALATE_TO_GPT_OWNER |
| 3 | heat-action-plans | POLICY_EFFECT_EVALUATION | 0.0406 | 13 | REJECTED_AS_COMPLETED | ESCALATE_TO_GPT_OWNER |
| 4 | clean-electricity-2025 | QUANTITATIVE_DATA_RECONCILIATION | 0.0453 | 12 | REJECTED_AS_COMPLETED | ESCALATE_TO_GPT_OWNER |
| 5 | glp1-cardiovascular-evidence | RANDOMIZED_CLINICAL_EVIDENCE | 0.0606 | 14 | REJECTED_AS_COMPLETED | ESCALATE_TO_GPT_OWNER |
| 6 | ai-coding-productivity | ENGINEERING_BENCHMARK | 0.0364 | 12 | REJECTED_AS_COMPLETED | ESCALATE_TO_GPT_OWNER |
| 7 | ev-fire-risk | OBSERVATIONAL_CAUSALITY | 0.0364 | 13 | REJECTED_AS_COMPLETED | ESCALATE_TO_GPT_OWNER |
| 8 | microplastics-cardiovascular | SYSTEMATIC_EVIDENCE_SYNTHESIS | 0.0333 | 11 | REJECTED_AS_COMPLETED | ESCALATE_TO_GPT_OWNER |

Eight of eight rounds are rejected as completed research. No round reaches
`CANDIDATE_COMPLETE`; the scheduler never selects `PUBLISH_CANDIDATE_PACKET`.
Total round time is ~0.35 hours (~21 minutes) for eight claimed studies; the
campaign window was ~43 minutes.

Recurring gap codes across rounds (from the machine episodes):
`TIMESTAMP_BATCH_NOT_PROOF_OF_READING`, `READING_TIME_SCOPE_INCONSISTENT`,
`PRIMARY_SOURCE_MISSING`, `FULL_TEXT_MISSING`, `NUMERIC_CLAIM_NOT_RECOMPUTED`,
`RAW_DATA_OR_CODE_MISSING`, `NEGATIVE_EVIDENCE_NOT_SEARCHED`,
`UNAUTHORIZED_EARLY_CLOSEOUT`, `HUMAN_JUDGMENT_REQUIRED`, plus round-specific
codes such as `SOURCE_DEPENDENCE_HIGH`, `OUTCOME_DEFINITION_CONFLICT`,
`POPULATION_SCOPE_MISMATCH`, `CAUSAL_IDENTIFICATION_MISSING`,
`REPLICATION_STATUS_UNKNOWN`, `ADVERSARIAL_REVIEW_MISSING`.

## 4. Directional comparison with the R2 initial adjudication

The R2 eight-track design independently treats the same eight topics as open
research requiring deep validation, which is directionally consistent with this
replay's refusal to accept R1 completions. This replay does not read R2
results as proof; R2 is a human-authored comparison target and provisional
telemetry only (Task 115 §4).

## 5. What the OS would have dispatched instead

For every round the ranked plan begins with `ESCALATE_TO_GPT_OWNER` (forced by
integrity findings such as `UNAUTHORIZED_EARLY_CLOSEOUT` and
`READING_TIME_SCOPE_INCONSISTENT`), followed by concrete repair actions —
`SEARCH_PRIMARY_SOURCE`, `CHECK_SOURCE_DEPENDENCE`, `BRANCH_QUESTION`,
`FREEZE_OR_NARROW_QUESTION`, and for the clinical rounds
`SEEK_METHODOLOGICAL_CRITIQUE` / `STOP_WITH_INSUFFICIENT_EVIDENCE`. The full
ranked candidate lists are in each machine episode.

## 6. Limits

- Strategy-pack adjudication per round is a replay-time classification recorded
  in episode provenance; it can be challenged by review.
- The reading floor (0.5 h/source) is a conservative lower bound, not a
  psychometric claim; any larger floor strengthens the findings.
- The replay consumes R1 packet metadata only; it does not re-read the report
  prose, and it does not need to: the completion rejection follows from state,
  obligations and timestamps alone.
