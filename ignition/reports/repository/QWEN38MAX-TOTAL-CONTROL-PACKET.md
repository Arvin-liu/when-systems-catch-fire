# QWEN38MAX Total-Control Packet — Whole-Repository Convergence R1

Final campaign state: `QWEN38MAX_WHOLE_REPO_CANDIDATE_PACKAGE_AWAITING_GPT_OWNER_TOTAL_CONTROL`

This is a read-only campaign packet. It does not merge, Ready, tag, terminalize, or promote anything. Machine companion: `reports/repository/QWEN38MAX-CAMPAIGN.json`.

## 1. Exact baselines

| baseline | identity |
|---|---|
| control repository | `Arvin-liu/1111` |
| control branch tip | `relay/parallel/qwen38max-whole-repo-convergence-20260803-r1` @ `6bf7357707a2292bcc9f525a5b621da977fc6d7d` (verified match) |
| relay/current tip | `6a95666cb256c8a3c21c8f14858fcd9b9fed9128` |
| formal repository | `Arvin-liu/when-systems-catch-fire` |
| formal main | `cac043d438bea6c4dc2c57c1169093df715ef5df` (accepted iteration 114) |
| Task 115 WorkBuddy branch | `workbuddy/task115-research-executive-os-draft-r1-20260803` @ `f56edf33…` (Checkpoint B) |
| PR #189 head | `046570c6b69c3817b53167bebf8cf09cbf75e6d0` |
| R2 branch | `research/eight-track-deep-validation-20260803-r2` @ `ae777859…` |
| R1 replay lock tip | `232299483f701e8304265c1484b5b50e5dcf2799` |

## 2. Lines A–D identity and changed surface

| line | branch / PR | base | changed surface |
|---|---|---|---|
| A | `qwen38max/task115-checkpoint-c-recovery-r1-20260803`, PR #190 @ `16f3d83b` | `main` | Research OS strategy packs/gates/adapters/executor schema, R1 replay episodes + doc, bounded R2 loop + doc, Checkpoint C + resumability tests, recovery manifest, review packet, path manifest |
| B | `qwen38max/pr189-independent-review-ci-repair-r1-20260803`, PR #191 @ `266d3fd7` | PR #189 branch | canonical-generator outputs to fixed point (manifest, census, adjudications, migration, governance, knowledge), independent review doc, path manifest |
| C | `qwen38max/eight-track-r2-auditability-repair-r1-20260803`, PR #192 @ `e702a0e0` | R2 branch | Track 005/004/006/007 metadata corrections, NOT_RECORDED markers, offline validator + 5 fixtures, replay scripts/results/report, path manifest |
| D | `qwen38max/whole-repo-state-convergence-r1-20260803`, PR (this) | `main` | state ledger + lineage registry + invariant engine + results, schemas, tests + fixtures, five reports, this packet, campaign JSON |

## 3. Task 115 local recovery evidence

WorkBuddy workspace `/Users/zhiyuan/Workbuddy/Claw/arr-r2-formal-115` held unpushed working-tree work on branch `workbuddy/task115-…` whose HEAD already matched the remote tip `f56edf33` (zero unpushed commits). Before any mutating operation the workspace was archived byte-for-byte (status, tracked diff, untracked list, patch bundle). The applied tree's `git diff` is byte-identical to the preserved diff (sha256 match recorded in `TASK115-RECOVERY-MANIFEST.json`). Recovered content: 8 strategy packs, review gates, adapters, executor-return schema, templates, docs. Two real defects found and minimally repaired (`consume_iteration_delta`, `cli resume`).

## 4. CI runs and failure explanations

At PR #189 head `046570c6`: `repository-path-accounting-preflight` FAIL (missing=4 added paths), `iteration-lifecycle-validation` FAIL (same embedded Layer-A line), `foundation-validation` FAIL (census/deep-adjudication/nonfunction stale + path accounting), `iteration-planner-ci` PASS. Line B repaired all via canonical generators to a fixed point; see `reports/publication/pr189-independent-review-and-ci-repair-r1-20260803.md` for the full log-by-log account. Lean foundation replay runs only in CI (toolchain not installed locally) and is recorded as externally covered.

## 5. Test commands and results

- Line A: `python3 tests/test_research_os.py`, `tests/test_research_os_checkpoint_c.py`, `tests/test_research_os_resumability.py` — all pass.
- Line C: `python3 tools/research_campaigns/validate_eight_track_r2.py --campaign RESULTS/research-campaigns/2026-08-03-eight-track-deep-r2 --ref ae777859` — 657 checks, 0 failures; `--self-test` — 5/5 fixtures.
- Line D: `python3 tests/test_repository_state_invariants.py` — all pass; `validate_global_invariants.py --run` — `GLOBAL_INVARIANTS_CLOSED` 11/11; `--self-test` — 5/5 fixtures.

## 6. Unresolved conflicts among candidates

- #189 module substance: no method blocker found by independent review; acceptance is an owner decision.
- R2 acceptance: Line C restored metadata trustworthiness; R2 remains candidate research.
- Old record drafts (#3, #5, #16–#21, #31, #32): supersession undecidable by rules; flagged `UNKNOWN_REQUIRES_OWNER_ADJUDICATION`.

## 7. Review safety and ordering

Independently reviewable: Lines A, B, C, D (isolated branches, ordinary commits, non-forced pushes). Ordering constraints: #191 before any #189 substance step; #192 before any R2 adjudication; #190 gated by `R2_EMPIRICAL_CALIBRATION_PENDING`. Full graph in `CANDIDATE-CONVERGENCE-PLAN.md`.

## 8. Recommendations (each RECOMMENDATION_ONLY)

- R1: review Line B first (repairs deterministic CI, unblocks human review of #189).
- R2: review Line C next (restores R2 metadata before judging R2 results).
- R3: review Line A (recovered Task 115 work with replay evidence).
- R4: review Line D (installs the state ledger + invariant gate).
- R5: adjudicate #189 substance, R2 acceptance, and Task 115 continuation as separate owner decisions after the repair lines land.
- R6: periodically re-adjudicate the component path-overlap table (`ARCHITECTURE-COHERENCE-REVIEW.md` F1).

## 9. No-merge decision graph

See `CANDIDATE-CONVERGENCE-PLAN.md` §"No-merge decision graph". Summary: every Draft PR requires explicit owner evidence review, stacked children never land before parents, research branches never promote to formal knowledge, and only an explicit owner authorization triggers any merge. This campaign itself performs no terminal action.
