# Open PR and Branch Disposition — Line D

Snapshot: `data/operations/campaign-inputs/open-prs-20260803.json` (81 open PRs, all Draft).
Every recommendation below is `RECOMMENDATION_ONLY`. This campaign closes, edits, merges or re-bases nothing.

## Disposition rules applied

- base `main` -> `OPEN_DRAFT_CANDIDATE`; other base -> `STACKED_REPAIR_CANDIDATE`;
- stacked families land child-into-parent only, and only after owner adjudication;
- research branches never merge to main as formal knowledge;
- no auto-merge, no Ready transition anywhere.

## PR families (16)

| family root | base | members | depth | category | disposition |
|---|---|---|---|---|---|
| #109 | `main` | #109, #110, #111, #112, #113, #114, #115, #116… | 23 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #82 | `main` | #82, #83, #84, #85, #86, #87, #88, #90… | 17 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #82 | `main` | #82, #83, #84, #85, #86, #87, #88, #89… | 17 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #65 | `main` | #65, #66, #67, #68, #69, #70, #71, #72… | 17 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #189 | `main` | #189, #191 | 2 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #31 | `records/ignition-121-fulltext-resolver-and-120-repair-20260714` | #31, #32 | 2 | STACKED_REPAIR_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #192 | `research/eight-track-deep-validation-20260803-r2` | #192 | 1 | STACKED_REPAIR_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #190 | `main` | #190 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #21 | `main` | #21 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #20 | `main` | #20 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #19 | `main` | #19 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #18 | `main` | #18 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #17 | `main` | #17 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #16 | `main` | #16 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #5 | `main` | #5 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |
| #3 | `main` | #3 | 1 | OPEN_DRAFT_CANDIDATE | REMAIN_DRAFT_NO_MERGE_WITHOUT_OWNER_ADJUDICATION |

## Campaign lines A–D

| line | PR | base | relation |
|---|---|---|---|
| A — Task 115 Checkpoint C recovery | #190 | `main` | child of exact Task 115 tip f56edf33; Draft; R2_EMPIRICAL_CALIBRATION_PENDING |
| B — PR #189 review + CI repair | #191 | PR #189 branch | stacked on #189; repairs CI root causes via canonical generators |
| C — R2 auditability repair | #192 | R2 research branch | stacked on R2; metadata fixes + offline validator + replays |
| D — whole-repo state convergence | this branch | `main` | observes A–C as candidates; absorbs none of them |

## Independent-review safety classes

- safe to review independently: Lines A, B, C, D (isolated branches, ordinary commits, no shared-history mutation);
- ordering constraints: #191 must land into the #189 branch before #189 could ever proceed; #192 must land into the R2 branch; #190 and Line D target main directly but remain Draft;
- stacked merge is never performed by this campaign — the no-merge decision graph lives in `QWEN38MAX-TOTAL-CONTROL-PACKET.md`.

## Old/unclear drafts requiring owner adjudication

#3, #5, #16–#21, #31, #32 (records/protocol era) remain open Draft with bases `main` or records branches. Rules here cannot decide whether they are superseded by later accepted iterations; they are recorded as `UNKNOWN_REQUIRES_OWNER_ADJUDICATION` and left untouched.
