# IGNITION-20260822-132 Step 00 — Canonical Current stale-source reproduction

Status: `BASELINE_REPRODUCED`

The refreshed control ref is `origin/relay/current@995a4bc560749c199be94f93f9b76417a4c967b1`. The formal task worktree starts from `origin/main@e04752d20d071bac8f0c4a1e5cff20fb3004dae1`, the exact Task131 publication candidate and remote `main` observed in the prior 1111 receipt.

The repository-local validators pass because the canonical files agree with one another:

- `current-task-lineage-status.json` says current formal task `IGNITION-20260821-130`;
- `current-release-lifecycle-r1.json` binds `task_id` to `IGNITION-20260821-130`;
- `current-snapshot-r1.json` and the compiler-generated Current blocks project Task130;
- lineage, lifecycle, snapshot determinism, Current semantic and Current State sync checks pass.

The prior Task131 1111 witness independently records `candidate_sha == remote main SHA == fresh checkout HEAD` and 18 post-publication checks passing. It does not contain a task-id binding, so it can be exact on Git publication while remaining blind to the stale canonical Current source.

This is the reproduced failure: formal history and control-repository publication evidence identify Task131, while the canonical Current source and all of its projections identify Task130. The compiler is behaving deterministically; the missing invariant is source advancement before release-candidate formation.

The existing gates did not block because they compare canonical Current files to each other rather than to a task execution contract, and the post-publication path has no required expected task-id parameter. Step 01 onward therefore needs one task identity model, one deterministic advancement transaction, a release-candidate identity gate, and a witness validator that checks both SHA/ref binding and task-id binding.

The map remains `0.12.0`; the latest architecture-changing task remains `IGNITION-20260821-129`. This audit does not claim Owner authority, external truth, production readiness or epistemic acceptance.
