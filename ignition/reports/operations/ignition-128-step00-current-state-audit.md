# IGNITION-128 Step 00 — Current-State semantic audit

Formal baseline: `origin/main@681f86d79b1112af3c07e0f8091335860c237ef2`.
Control source: `1111 relay/current@3b6d27441395492cf633e53d3d1e985d0b2ec933`.
The formal `main` fetch and baseline equality check passed before this audit.

The search covered repository text and machine records for `DEFERRED_PENDING_REBASE`,
`Task 125`, `IGNITION-125`, `Task 127`, `IGNITION-127`,
`DEFERRED_REBASED_INTO_127`, and `COMPLETED_WITH_CLASSIFIED_RESIDUALS`.
It recorded 24 old pending-status hits, 22 `Task 125` hits, 5 `IGNITION-125`
hits, 57 `Task 127` hits, and 4 `IGNITION-127` hits.

Only four Human/AI Current entry surfaces still state the stale pending status:
`ignition/docs/project-current-state.md`, `ignition/AI-START-HERE.md`,
`ignition/AI-HANDOFF.md`, and `ignition/llms.txt`. The homepage, current identity,
current-facts and map surfaces contain the R3 identity but need to be checked against
the new canonical task-lineage/status source.

The Task 126 progress/receipt, Task 127 audit/progress/receipt, append-only
`STATE-CHANGELOG.md`, and generated Knowledge/Foundation projections are explicitly
preserved. Their old wording is historical source evidence or a derived projection,
not permission to describe the same state as Current. The unrelated historical
IGNITION-125 follow-up queue/report is also preserved.

The full path-level classification is recorded in
`ignition/data/operations/iterations/128/step00-audit-ledger.json`.

Claim ceiling: this step proves only a fresh repository audit and classification;
it does not prove production readiness, external truth, Owner acceptance or
`EPISTEMICALLY_ACCEPTED`.
