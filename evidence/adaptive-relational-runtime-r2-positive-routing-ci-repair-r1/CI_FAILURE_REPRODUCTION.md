# CI Failure Reproduction — ARR R2 Positive Routing CI Repair R1

**Authoritative source:** complete remote job log
`REMOTE_CI_JOB_LOG_89638042800.txt` (805 lines), fetched from
`gh api repos/Arvin-liu/when-systems-catch-fire/actions/jobs/89638042800/logs`.
No guessing was used.

## 1. Exact failing command (from remote log lines 736–738)

```text
python3 -m pip install pytest
python3 -m pytest tests/adaptive_relational_runtime/ -q
```

CI uses the **system** `python3` (pytest 9.1.1), matching the local environment.

## 2. Exact failure (remote log lines 769–788)

```text
tests/adaptive_relational_runtime/test_r2_positive_routing_repair.py:564: AssertionError
FAILED tests/adaptive_relational_runtime/test_r2_positive_routing_repair.py::test_current_branch_is_repair_branch
  - AssertionError: assert 'HEAD' == 'repair/adaptive-relational-runtime-r2-positive-routing-r1'
1 failed, 181 passed in 26.10s
##[error]Process completed with exit code 1.
```

Traceback root (line 773–776):

```python
def test_current_branch_is_repair_branch():
    res = _git("rev-parse", "--abbrev-ref", "HEAD")
>   assert res.stdout.strip() == REPAIR_BRANCH
E   AssertionError: assert 'HEAD' == 'repair/adaptive-relational-runtime-r2-positive-routing-r1'
```

## 3. Root cause

GitHub Actions checks out the PR head as a **detached HEAD**. Under a detached
HEAD, `git rev-parse --abbrev-ref HEAD` returns the literal string `'HEAD'`
rather than the branch name. The assertion `== REPAIR_BRANCH` therefore fails in
CI while passing locally (where a branch is checked out). This is a pure
CI-portability defect in the test; it does **not** touch any of the verified
48-object repair semantics.

The other git call in the same file (`git merge-base --is-ancestor FROZEN_HEAD HEAD`,
line 558) is detached-HEAD-safe and was not implicated.

## 4. Local clean-environment reproduction (Role B)

A git worktree was created at the exact predecessor head
`1908878c051de15e5934d38e017d469c0430cc83` (detached), and the exact CI command
was run. Result (`LOCAL_DETACHED_HEAD_REPRODUCTION.txt`, 18 lines):

```text
FAILED tests/adaptive_relational_runtime/test_r2_positive_routing_repair.py::test_current_branch_is_repair_branch
1 failed, 181 passed in 10.38s
```

and `git rev-parse --abbrev-ref HEAD` in that worktree returned `HEAD`. This is
byte-for-byte identical to the remote failure, confirming the reproduction is
exact and the cause is the detached-HEAD checkout, not environment drift.

## 5. Scope confirmation

- The failure is isolated to one test (`test_current_branch_is_repair_branch`).
- 181 of 182 tests pass locally and in CI; the only red test is the branch-name
  assertion.
- All 48/48 positive-routing repair semantics (receipts / adapter / runtime /
  projection / immutability / replay / route-match = 48/48, real_world_actions =
  0, privacy 48/48, PROMOTE = 0, EVOLVE = 0, manifest digest
  `d132c82554469e1136ba31220dc2afbcdcc5c0df0afc25822e5e70738e58e956`) are
  untouched by this defect and remain unchanged by the repair.
