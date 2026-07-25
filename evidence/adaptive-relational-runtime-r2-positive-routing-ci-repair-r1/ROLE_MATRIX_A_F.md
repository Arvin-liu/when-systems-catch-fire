# Independent Role Matrix (A–F) — ARR R2 Positive Routing CI Repair R1

The IGNITION requires at least six distinct verification roles. Each is recorded
here with its finding. All roles were executed against the same locked
predecessor head `1908878c…`; findings are reproducible from the artifacts in
this directory.

## Role A — Remote CI / log auditor
- Fetched the **complete** job log (805 lines) for job `89638042800` of run
  `30142387907`. No truncation, no guessing.
- Located the single failing test and traceback (lines 769–788).
- Confirmed every other step (including the ARR static gate) passed.
- **Verdict:** failure is `test_current_branch_is_repair_branch`, cause =
  detached-HEAD `git rev-parse --abbrev-ref HEAD` → `'HEAD'`.

## Role B — Clean-environment reproducer
- Built a git worktree at `1908878c…` (detached HEAD), ran the exact CI command
  `python3 -m pytest tests/adaptive_relational_runtime/ -q`.
- Reproduced `1 failed, 181 passed` with the identical traceback.
- Confirmed `git rev-parse --abbrev-ref HEAD` returns `HEAD` in the worktree.
- **Verdict:** reproduction is exact; cause confirmed, not environment drift.

## Role C — Test-contract reviewer
- Reviewed the proposed fix shape (CI-portable resolver + repair-branch family
  assertion). Confirmed it is the minimal change that fixes CI without altering
  any repair semantics, and that the family check is correct for both the parent
  (`…r1`) and child (`…ci-r1`) branches.
- **Verdict:** contract approved (see NARROW_REPAIR_CONTRACT.md §2).

## Role D — Sole Builder
- Implemented ONLY the resolver and the test change. No repair module, no
  runtime, no 48-object manifest, no R3, no scale-run code touched.
- **Verdict:** build surface limited to `tests/…/test_r2_positive_routing_repair.py`
  plus evidence/docs. No scope creep.

## Role E — 48-object regression and privacy auditor
- The defect is in a branch-name assertion only. The 48-object repair results
  (receipts/adapter/runtime/projection/immutability/replay/route-match = 48/48,
  real_world_actions = 0, privacy 48/48, PROMOTE = 0, EVOLVE = 0, manifest
  digest `d132c825…`) are exercised by the unchanged repair suite and are
  preserved by construction.
- **Verdict:** 48/48 positive semantics provably unchanged (no code path
  touching them was modified).

## Role F — Publisher / final remote gate
- Will: push via `gitops push` (no force), create a Draft PR (base
  `repair/adaptive-relational-runtime-r2-positive-routing-r1`), watch CI to
  green, then create the annotated frozen tag
  `archive/adaptive-relational-runtime-r2-positive-routing-ci-repair-r1-frozen-head`
  and the 1111 evidence branch
  `agent/adaptive-relational-runtime-r2-positive-routing-ci-repair-r1-20260725`.
- Verifies, via a final live remote refetch, that Main and PR #109–#122 are
  unchanged and the new artifacts are in place.
- **Verdict:** pending CI green (gated; see published result).
