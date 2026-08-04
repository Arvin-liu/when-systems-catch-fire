# GPT-OWNER-REVIEW-PACKET.md — Deep Research Queue (WorkBuddy Takeover)

**For:** GPT owner / reviewer of the Task 115 deep-research-queue relay.
**Branch:** `workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`
**Base (frozen Qwen Round 0):** `qwen38max/task115-deep-research-queue-checkpoint-d-r1-20260803` (`f4fe6fad`)
**Repo:** `Arvin-liu/when-systems-catch-fire`

## What to verify

This is a **candidate** delivery produced under the relay takeover mandate.
Please verify the control branch, the exact remote tips, and the following
claims independently.

## Summary of delivered rounds

| Round | Deliverable | Commit | Tests |
|-------|-------------|--------|-------|
| 1 | 13 fail-closed schemas + records + 27 fixtures | `0c07b798` | 19 PASS |
| 2 | serial crash-resumable queue (`SerialQueue`) | `3d88af6a` | 24 PASS |
| 3 | episode controller + offline-safe adapters + CLI/API | `e0176d67` | 18 PASS |
| 4 | transparent stopping: 10 hard gates + 8-dim vector | `a2413475` | 13 PASS |
| 5 | 27 frozen anti-overfit fixtures + replay + separate metrics | `7ceb4280` | 4 (27 sub) PASS |
| 6 | bounded sleep-timing pilot → `BLOCKED_WITH_EVIDENCE` + trace | `965e796e` | 2 PASS |
| 7 | docs + handoff + candidate state + Draft PR | see below | — |

**Total local tests:** 99 PASS across R1–R6 + 3 baseline Research OS kernel
suites PASS + queue smoke OK. No regression.

## Pilot outcome (Round 6)

The frozen sleep-timing question was driven through the real queue + episode +
evaluator interfaces. Because the capability's adapters are offline-safe and no
live public-web tool is wired in, the Round 6 precondition "required tool
access is available" is **not met**, and the pilot ends as `BLOCKED_WITH_
EVIDENCE` with a full machine trace (`round6-trace/`). The in-episode
evaluator independently corroborated this (`blocked_evidence_route` gate). This
is the legitimate "blocker" end state, **not** a code defect.

## Unresolved obligations (carried forward)

- **O1 — Live public-web tooling** for a true live pilot (resume commands in
  `CODEX-HANDOFF.md`).
- **O2 — Contradiction/entailment gate** to eliminate the 1 known false-positive
  stop in `r5-006-conflicting-estimands` (Round 5 metrics surface it, do not
  hide it).

## CI honesty

- **`R2_EMPIRICAL_CALIBRATION_PENDING`** is **retained and visible** in the
  Draft PR body — empirical calibration against live evidence is pending O1.
- **Remote exact-head CI:** where a Foundation/workflow CI runs against the
  branch head, its status must be verified by the owner/GPT; it is **not**
  asserted as passed here. Local suites all pass. Do not interpret this packet
  as claiming remote CI green.
- The Draft PR is intentionally **Draft**; do **not** merge / mark Ready / tag
  / terminalize Task 115.

## Draft PR

Head = WorkBuddy takeover branch; base = Qwen Round 0 branch. Remains Draft,
retains `R2_EMPIRICAL_CALIBRATION_PENDING`, and states failed/pending CI
honestly. See `CODEX-HANDOFF.md` for exact resume commands.

## Discipline notes

Rounds were executed **strictly serial** (tests → commit → non-forced `gitops`
push → verify exact remote tip → next round). No force-push / amend / rebase /
squash; no modification of the Qwen Round 0 branch, PR #190 parent, `formal`
`main`, `relay/current`, Task 114 history, Codex 631-note, or PRs
#189/#191/#192/#193. No approval window was encountered during any push.
