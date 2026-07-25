# Narrow Repair Contract — ARR R2 Positive Routing CI Repair R1

This is the binding contract for the minimal fix. It is intentionally narrow: it
repairs only the CI-portability defect and leaves the verified 48-object
positive-routing repair semantics byte-for-byte intact.

## 1. Defect (one line)

`test_current_branch_is_repair_branch` relies on
`git rev-parse --abbrev-ref HEAD`, which returns `'HEAD'` under the detached
HEAD that GitHub Actions uses to check out a PR. The assertion therefore fails
in CI.

## 2. Fix shape (Role C: test-contract reviewer approved)

Introduce a single CI-portable branch resolver `_resolve_repair_branch()` and
route `test_current_branch_is_repair_branch` through it. Resolution order:

1. `GITHUB_HEAD_REF` — set for `pull_request` events; this is the head branch of
   the PR (e.g. `repair/adaptive-relational-runtime-r2-positive-routing-ci-r1`).
2. `GITHUB_REF_NAME` — set for `push` and other events; used only when it is a
   real branch (not `refs/pull/...` and not ending in `/merge`).
3. `GITHUB_REF` — used only when it is a `refs/heads/<branch>`.
4. Git fallback — `git rev-parse --symbolic-full-name HEAD`, which yields
   `refs/heads/<branch>` on a checked-out branch and `HEAD` when detached.

The assertion is relaxed from an exact equality against the *predecessor* branch
name to a **repair-branch family** check:

```python
branch = _resolve_repair_branch()
assert branch is not None, "could not resolve a repair branch (detached, no CI ref)"
assert branch.startswith("repair/adaptive-relational-runtime-r2-positive-routing"), \
    f"expected a positive-routing repair branch, got {branch!r}"
```

Rationale for the family check (not `== REPAIR_BRANCH`): the child repair runs on
a different branch (`...ci-r1`), so an exact-equality assertion would fail
locally and in CI for this very repair. The family check preserves the test's
intent — "this suite runs on a positive-routing repair branch, not `main`, not a
feature branch, not a PR merge ref" — while being portable across the parent and
child repair branches and across local/CI contexts.

## 3. What is explicitly NOT changed (Role D: Sole Builder guard)

- No change to `adapter_protocol.py`, `pilot_runner.py`, `aggregation.py`, or any
  runtime/repair module.
- No change to the 48-object manifest, receipts, projection, replay, or any
  positive-routing semantics.
- No change to `MANIFEST_DIGEST` (`d132c825…`).
- No new executor, no scale-run code, no R3 code.
- No change to `Main`, PR #109–#122, their tags, heads, bases, or states.
- No force push, amend, rebase, squash, or history rewrite.

## 4. Acceptance gates (from IGNITION)

- Exact remote failure reproduced before repair. ✅ (see CI_FAILURE_REPRODUCTION.md)
- New regression fails on the pre-fix state (child of `1908878…`) and passes on
  the repair head. (verified at commit 1 = fail, commit 2 = pass)
- Exact workflow command passes in a clean checkout.
- All ARR tests pass.
- Foundation / human-front-door / iteration-sync / propagation / system-map
  checks pass or match predecessor with no new failure.
- Same 48 objects remain 48/48 positive.
- No changed-path residue.
- New Draft PR CI completes successfully.
- Main and PR #109–#122 unchanged.

## 5. Commit plan (exactly two ordinary commits)

1. **Commit 1** — this contract + the complete CI log + local reproduction +
   a deterministic regression test (`test_ci_detached_head_branch_resolution_is_portable`)
   that is RED until the resolver lands.
2. **Commit 2** — minimal implementation of `_resolve_repair_branch`, the
   CI-portable `test_current_branch_is_repair_branch`, full regression, and
   docs/evidence/CI synchronization.

A third commit is NOT required; if it becomes necessary the repair stops and
requests separate authorization.
