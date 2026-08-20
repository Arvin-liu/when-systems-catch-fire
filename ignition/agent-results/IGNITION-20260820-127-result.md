# IGNITION-20260820-127 执行结果

状态：`COMPLETED_WITH_CLASSIFIED_RESIDUALS`

本任务执行的是 `IGNITION-127`，不是旧 `IGNITION-125`。旧 125 已记录为
`DEFERRED_REBASED_INTO_127`；未执行旧文件，也未复制旧文件作为权威任务。

## 范围与边界

- 仓库：`Arvin-liu/when-systems-catch-fire`
- 起始正式 main：`c5cec3a212dbf42564985b71c0fcec3b1fb1e564`
- 任务分支：`codex/ignition-127-os-durability-lifecycle-r3-rebased-20260820`
- Step 18 tip：`2952d53bbc113c75b506f12ddaaf96a4083013d8`
- Step 19 最终 SHA：`681f86d79b1112af3c07e0f8091335860c237ef2`；任务分支已推送并以远端 SHA 核验。
- `main` ordinary fast-forward 后 SHA：`681f86d79b1112af3c07e0f8091335860c237ef2`；fresh clone 精确 tip 与 fresh fetch `origin/main` 均一致且工作树干净。
- `CURRENT_WITH_OPEN_OBLIGATIONS` 与 `EPISTEMICALLY_ACCEPTED=0` 保持不变。

## Step 00–19 提交台账

| Step | Commit | Push / remote SHA |
|---|---|---|
| 00 | `b1129cc919c580fd7f8ade3e66856b2f0c6a2bcd` | verified |
| 01 | `c05f693bd5329b9506b7dea1bc9167d553d9f305` | verified |
| 02 | `5b6184ac02ddc9d574ed6223361da9761b221388` | verified |
| 03 | `3c05df0e812c705a0858adf432feca061fc287d6` | verified |
| 04 | `09ed5662149de37edc646fa91a0830e6d5c941e0` | verified |
| 05 | `31c36a5d188524327d3daded38e4af0fed3f935b` | verified |
| 06 | `7906d486722560d5c0d81a0c4f5650560b72d92f` | verified |
| 07 | `b2b032963db5f38a0c99f7d63533b916c685f317` | verified |
| 08 | `25dab10977f6cf4a9ceb395c7e618dd625000a9d` | verified |
| 09 | `68c28a5fad1ce63477e5e48dafad56332b75d362` | verified |
| 10 | `cd43f2d29a5f755441378396df15b8ba08448208` | verified |
| 11 | `2760799507ce0db7b5739977c0eac5a56611d2c9` | verified |
| 12 | `a8b17fa3bdadd4763e577743a7636444155413cd` | verified |
| 13 | `0ce29b959c7da32f9ec0557808bb8ce4d5a97585` | verified |
| 14 | `a7ab5c5bb211b100c79fc621cb48e650eb5766ae` | verified |
| 15 | `2ba089c65df9eda56187523b6cac4a100037ae0a` | verified |
| 16 | `c5db7ebb1a48cf364efde1c9c3b969642b79fc08` | verified |
| 17 | `39a9e5307776b8e24fc7899218660d62e74b37af` | verified |
| 18 | `2952d53bbc113c75b506f12ddaaf96a4083013d8` | verified |
| 19 | `681f86d79b1112af3c07e0f8091335860c237ef2` | verified |

## Rebase matrix

All 13 old-125 requirements are represented in the Step 00 matrix: 8 remain required,
4 are modified by Task 126 boundaries, and 1 was already present. They bind to
Steps 02–19 for snapshot/restore, three-epoch migration, namespace/delegation,
Pack lifecycle, admission/revocation, accounting, recovery/DR, Driver Surface,
continuity, adversarial regression, Current sync, and provider-neutral non-escalation.

## Evidence summary

- State taxonomy: canonical event-sourced, derived rebuildable, advisory soft context,
  external pointer-only, historical sealed, and ephemeral process-local classes; snapshots
  are recovery accelerators and never a second truth source.
- Snapshot/tail/restore/compaction: replay equivalence and fail-closed tamper, stale,
  partial, corrupt-tail, wrong-epoch and cross-namespace cases passed.
- Migration: `state-epoch-1` / `state-epoch-2` / `state-epoch-3` fixtures passed;
  lossy downgrade requires approval and direct legacy rewrite is forbidden.
- Namespace, delegation, Pack lifecycle, revocation, accounting, memory, recovery and
  DR bundle gates passed; DR bundle has 12/12 chunks and fresh-directory canonical-digest
  restore passed.
- Adversarial matrix: 19 cases; expected fail-closed, reconciliation-required and
  restart/replay outcomes passed. External invocation and automatic external rerun were
  not performed.
- Offline continuity pilot: 2 namespaces, 2 workspaces, 11 recovery phases, 12 DR
  chunks, pinned Pack versions, revocation fail-closed, accounting/memory pass,
  advisory-only soft governance, external invocation `NOT_RUN`.
- Architecture/current sync: registry 93, visible nodes 81, hidden 12, typed relations
  125, visible typed edges 85; Current map `0.11.0`, Historical `0.10.0`, layout `1.9.0`;
  geometry height 2846.0, blank reduction 0.8741007194, crossing count 184.
- Foundation: `ALL_FOUNDATION_VALID` 63/63; function closure 46/46; claim governance
  39/39; non-function closure 54/54 with 16,240 canonical claims; current facts and
  path classification pass.
- Knowledge: 403 cards, 315 changes, 332 layers, 22,183 search entries, 851 aliases;
  full audit and two-pass deterministic rebuild pass.
- Human Surface / Fire Seeds: 48 human entries, 25 human surfaces, 14 machine-human
  pairs, 20 two-click destinations; Fire Seeds 64 (40 content, 24 methodology), 393
  sources, 332 layered origins.
- Privacy and non-authority: owner-observation privacy, public-artifact secret/local-path
  scan, feedback-loop scan, soft-governance runtime scan and 174 Task127-related tests
  pass; production-profile local-validator test passes.

## Regression and residuals

The correct `ignition/` working-directory full discovery recorded 885 tests, with the
first terminal run reporting 11 failures and 1 skip. Seven generated-projection failures
were repaired by regenerating canonical non-function, Knowledge, Fire Seeds and Current
Facts outputs and by aligning the current Agent Platform human-surface validator. The
post-repair affected gates and production-profile test pass. The remaining non-green
legacy checks are explicitly classified, not hidden:

1. `T16_SYMPY_COUNTEREXAMPLE`: `SYMPY_UNAVAILABLE:ModuleNotFoundError`, environmental
   residual preserved by the Foundation contract.
2. Three propagation checks for sealed historical Tasks 104–106, covering nine
   MACHINE_RECORD_IMPACT, SYSTEM_MAP_IMPACT and PROJECT_STATE_IMPACT dimensions;
   the direct validator reports the historical mismatch, while the Task127 hygiene gate
   records `HISTORICAL_RESIDUAL_PRESERVED` and forbids rewriting those specifications.

These are inherited/environmental or historical residuals, not new Task127 regressions.

## Publication boundary

Fresh-clone exact-tip replay, final task-tip SHA, ordinary fast-forward `main`, fresh
fetch SHA, and the independent receipt branch are the final publication actions. The
fresh clone was clean at exact task tip `681f86d79b1112af3c07e0f8091335860c237ef2`,
and fresh fetch `origin/main` matched that SHA. No
Owner relay, external provider invocation, production claim, exact-once claim, truth
claim, permission expansion, or epistemic acceptance is implied.

The machine-readable receipt is
`agent-results/IGNITION-20260820-127-machine-receipt.json`; its receipt-branch copy
contains the exact final task SHA and main SHA after publication.
