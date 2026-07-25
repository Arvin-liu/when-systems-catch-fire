# Narrow Repair Contract — ARR R2 Human-Front-Door Sync Repair R1

## Mandate (verbatim intent)
> 精确诊断系统图 100 节点与测试硬编码 99 的差异；不得直接把 99 改成 100，必须验证第 100
> 个节点是否合法，并建立不易漂移的 canonical node-set 闸门。

## Hard constraints
1. **Do NOT** blindly change `99` → `100`. The literal must be replaced by a
   drift-resistant canonical node-set gate that derives the expected set from the
   registry of record, not from a hand-maintained number.
2. **Verify the 100th node's legitimacy** before trusting the count. Proven in
   `CANONICAL_NODE_IDENTITY_AUDIT.md`: all 100 nodes are real, visible, registered
   components; there is no duplicate, orphan, hidden-without-representative, or `l7`
   node. The 100th node is legitimate.
3. **Build a drift-resistant gate** that:
   - Derives `expected_ids` independently from `data/operations/project-components.json`
     (`map_projection.visible`) **and** cross-checks `data/architecture/interactive-system-map-layout.json`
     (`node_order`) — an independent path from the validator's hardcoded `required_nodes`.
   - Compares **exact node identities** (not a bare count).
   - Retains an explicit **no-`l7`** assertion.
   - Fails on **missing / extra / orphan / duplicate / non-clickable / `l7`**.

## Forbidden (guardrails — all must remain 0)
- `R3_STARTED`, `WAIC_FULL_CORPUS_RUNS`, `REAL_WORLD_ACTIONS`, `FORMAL_ASSETS_PROMOTED`,
  `AUTO_EVOLVE_STARTED`, `FORMAL_READY_PRS`, `FORMAL_MERGES`, `MAIN_CHANGES`,
  `FORCE_PUSHES`, `HISTORY_REWRITES`, `EXTERNAL_ACCEPTANCE_CLAIMED`.
- No merge, no modify Main, no force push, no PROMOTE, no EVOLVE, no Ready, no R3.

## Branch / commit / PR structure
- Exactly **one** child branch: `repair/adaptive-relational-runtime-r2-human-front-door-sync-r1`
  from predecessor head `5771d6c`.
- Exactly **one** Draft PR (#124), base `repair/adaptive-relational-runtime-r2-positive-routing-ci-r1`.
- Exactly **two** ordinary commits (noreply identity `49422864+Arvin-liu@users.noreply.github.com`):
  - **Commit 1:** failure reproduction + narrow repair contract + canonical node-identity
    audit + (the existing brittle `== 99` test is retained, so the suite fails on the
    predecessor — this is the reproduction).
  - **Commit 2:** narrow repair — replace the brittle literal with the canonical node-set
    gate; regenerate artifacts only if canonical data changed (it did not); verification.
- No amend / rebase / force / history rewrite.
- Do not modify PR #109–#123.

## Publication
- 1111 evidence branch: `agent/adaptive-relational-runtime-r2-human-front-door-sync-r1-20260725`.
- Annotated frozen tag `archive/adaptive-relational-runtime-r2-human-front-door-sync-r1-frozen-head`
  created **after** green `foundation-validation`, then pushed.
- Stop state: `ARR_R2_HUMAN_FRONT_DOOR_SYNC_REPAIR_DRAFT_AWAITING_EXTERNAL_REVIEW`.
