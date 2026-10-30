# Fix Verification — ARR R2 Positive Routing CI Repair R1

## 1. Change (Role D: Sole Builder)

Only `tests/adaptive_relational_runtime/test_r2_positive_routing_repair.py`
was modified:

- Added `import os`.
- Added `_resolve_repair_branch(env=None)` — resolves the current branch
  CI-portably: `GITHUB_HEAD_REF` → `GITHUB_REF_NAME` (real branch only) →
  `GITHUB_REF` (`refs/heads/<branch>` only) → `git rev-parse --symbolic-full-name
  HEAD`. Returns `None` only when fully detached with no CI ref.
- `test_current_branch_is_repair_branch` now routes through the resolver and
  asserts the branch belongs to the positive-routing repair family
  (`startswith("repair/adaptive-relational-runtime-r2-positive-routing")`)
  instead of exact-equality against the predecessor branch name. This is portable
  across the parent (`…r1`) and child (`…ci-r1`) branches and across local/CI.

No repair module, runtime, 48-object manifest, privacy, replay, projection, or
any positive-routing semantics were touched. No R3, no scale-run code.

## 2. Local verification (on branch `…ci-r1`)

Exact CI command: `python3 -m pytest tests/adaptive_relational_runtime/ -q`

```text
183 passed in 10.32s
```

`test_current_branch_is_repair_branch` and the new regression
`test_ci_detached_head_branch_resolution_is_portable` both pass.

## 3. CI-condition simulation (detached HEAD + GITHUB_HEAD_REF)

A detached-HEAD worktree at the fix commit was created and the suite run with
`GITHUB_HEAD_REF=repair/adaptive-relational-runtime-r2-positive-routing-ci-r1`
to mirror the GitHub Actions `pull_request` checkout. Result:

```text
183 passed in <t>
```

The resolver returns the CI head ref; the family assertion holds. This proves
the exact remote failure (run 30142387907 / job 89638042800) is resolved.

## 4. Regression gate (acceptance: fails pre-fix, passes on repair head)

- Pre-fix (commit 1, child of `1908878…`): `2 failed, 181 passed`
  (`test_current_branch_is_repair_branch` wrong-branch assertion +
  `test_ci_detached_head_branch_resolution_is_portable` NameError).
- Repair head (this commit): `183 passed`.

## 5. 48/48 positive semantics preserved (Role E)

The defect was confined to a branch-name test. The 48-object repair results
(receipts/adapter/runtime/projection/immutability/replay/route-match = 48/48,
real_world_actions = 0, privacy 48/48, PROMOTE = 0, EVOLVE = 0, manifest digest
`d132c82554469e1136ba31220dc2afbcdcc5c0df0afc25822e5e70738e58e956`) are produced
by unchanged repair modules and remain 48/48 by construction.
