# Global Invariant Closure — Line D (D4)

Engine: `tools/operations/validate_global_invariants.py` (stdlib-first, deterministic, non-mutating). Results artifact: `data/operations/global-invariant-results.json`. Test: `tests/test_repository_state_invariants.py`. Negative fixtures: `tests/fixtures/global_invariants/` (5 cases).

## Invariant matrix at main `cac043d4` + Line D commits

| id | invariant | result |
|---|---|---|
| INV-01 | ledger covers all 81 open PRs exactly once | PASS |
| INV-02 | exactly one ACCEPTED_CURRENT; matches current-truth projection (114) | PASS |
| INV-03 | terminalized iteration chain contiguous 104..114 | PASS |
| INV-04 | no open candidate represented as accepted/current | PASS |
| INV-05 | research branches never formal knowledge | PASS |
| INV-06 | stacked PR parent/head identity resolves (PR head or existing branch) | PASS |
| INV-07 | Task 114 terminal history immutable (tag + current acceptance intact) | PASS |
| INV-08 | component registry closes into system map (in-map or justified non-projection) | PASS |
| INV-09 | public-surface relative links resolve | PASS |
| INV-10 | ledgers satisfy their JSON schemas | PASS |
| INV-11 | ledger regeneration byte-identical (determinism) | PASS |

Verdict: `GLOBAL_INVARIANTS_CLOSED` (11/11). External authoritative validators (path accounting, foundation 63/63, lifecycle) were re-verified green at the Line B repaired head and are recorded as external checks rather than reimplemented.

## Calibration history (findings before closure)

The first engine run produced three failures; each was investigated against bytes before any rule change:

1. INV-06 flagged PRs #192 and #31. Evidence: their bases are long-lived branches (`research/eight-track-...`, `records/...`) present in the branch snapshot. Rule refined to resolve parents against open-PR heads **or** existing branches. Real stacked-parent absence still fails (fixture `stacked-parent-missing`).
2. INV-08 flagged 11 registry components absent from the system map. Evidence: all 11 carry explicit `map_projection.no_change_reason` (interpretation boundaries / infrastructure). This was a **non-defect** encoded as a closure rule instead.
3. INV-09 flagged two llms.txt links. Evidence: `(Current)` and `(Continuous Stage Snapshot Publication)` are prose status labels, not path references. Rule refined to path-like targets only; real broken links still fail.

## Negative fixtures

| fixture | triggered invariant |
|---|---|
| `duplicate-pr-classification` | INV-01 |
| `two-accepted-current` | INV-02 |
| `iteration-chain-gap` | INV-03 |
| `research-branch-accepted` | INV-05 |
| `stacked-parent-missing` | INV-06 |

Additional fixture classes required by the TASK (open burden-bearing obligations, missing calculation outputs) are covered at the research-campaign level by Line C's `validate_eight_track_r2.py` fixtures (`open-obligation-final`, `missing-calculation-outputs`); the repository-level engine integrates that validator by reference rather than duplicating it.

## What closure does not claim

Closure is a property of the encoded invariants over committed inputs at this head. It is not semantic acceptance of any candidate, not proof of external truth, and not a substitute for owner/GPT adjudication.
