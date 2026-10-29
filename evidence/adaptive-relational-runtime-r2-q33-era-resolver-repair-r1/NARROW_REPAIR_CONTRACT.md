# Narrow Repair Contract — ARR R2 Q33 Era Resolver Repair R1

## Mandate (verbatim intent)
> 同步并锁定 Arvin-liu/when-systems-catch-fire@81e6054b。先读取本机最新 gitops 规则，并从
> 完整远端日志精确复现 q33-governance-validation 中 test_era_resolver_generalization 的
> era_ref 解析失败。从该 HEAD 创建一条窄 child Draft，只修 era resolver/generalization、
> 必要回归测试与证据；要求 q33-governance-validation 和 foundation-validation 同时 success。
> 不得改变 ARR 48/48 语义，不启动 R3，不 Ready、merge、修改 Main、force push、PROMOTE 或
> EVOLVE。持续运行至 Q33_ERA_RESOLVER_REPAIR_DRAFT_AWAITING_EXTERNAL_REVIEW 或精确 blocker。

## Hard constraints
1. **Narrow scope.** Touch ONLY the era-resolver/generalization test file and its
   evidence. Do **not** modify the resolver (`tools/operations/era_resolver.py`), the
   121Q33 manifest, Main, or any prior repair PR (#109–#124).
2. **Fix correctness, not symptom-by-coincidence.** Re-classify merged `121Q33` as
   frozen (verified ancestor of `origin/main`, `status.merged=True`), and rewrite the
   request-based test to use a genuinely live iteration (`121Q25B`). No assertion is
   weakened or deleted; both still assert `era_ref is None` for a real live candidate.
3. **Preserve ARR 48/48 semantics.** No change to the 48/48 corpus, projection,
   aggregation, or routing semantics. The frozen `era_ref=cf321f9` for 121Q33 is the
   canonical, already-validated value.
4. **Both gates must be green.** Require `q33-governance-validation` AND
   `foundation-validation` simultaneously `success` before stopping.

## Forbidden (guardrails — all remain 0)
- `R3_STARTED`, `WAIC_FULL_CORPUS_RUNS`, `REAL_WORLD_ACTIONS`, `FORMAL_ASSETS_PROMOTED`,
  `AUTO_EVOLVE_STARTED`, `FORMAL_READY_PRS`, `FORMAL_MERGES`, `MAIN_CHANGES`,
  `FORCE_PUSHES`, `HISTORY_REWRITES`, `EXTERNAL_ACCEPTANCE_CLAIMED`.
- No merge, no modify Main, no force push, no PROMOTE, no EVOLVE, no Ready, no R3.

## Branch / commit / PR structure
- Exactly **one** child branch:
  `repair/adaptive-relational-runtime-r2-q33-era-resolver-repair-r1`
  from predecessor head `81e6054b`.
- Exactly **two** ordinary commits (noreply identity
  `49422864+Arvin-liu@users.noreply.github.com`), neither an amend / rebase / force /
  history rewrite:
  - **Commit 1:** the narrow test re-classification + regression guarantee + root-cause
    evidence (CI_FAILURE_REPRODUCTION.md, ERA_RESOLVER_FINDING.md, NARROW_REPAIR_CONTRACT.md,
    full remote log).
  - **Commit 2:** fix-verification evidence (FIX_VERIFICATION.md) recording both gates
    success; corrects this contract's commit count.
- Exactly **one** Draft PR, base
  `repair/adaptive-relational-runtime-r2-human-front-door-sync-r1`.
- Do not modify PR #109–#124.

## Publication
- 1111 evidence branch: `agent/adaptive-relational-runtime-r2-q33-era-resolver-repair-r1-20260725`.
- Annotated frozen tag
  `archive/adaptive-relational-runtime-r2-q33-era-resolver-repair-r1-frozen-head`
  created **after** both gates are green, then pushed.
- Stop state: `Q33_ERA_RESOLVER_REPAIR_DRAFT_AWAITING_EXTERNAL_REVIEW`.
