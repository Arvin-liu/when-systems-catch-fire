# Current-State Drift Audit R1 — IGNITION-20260816-123 Step 00

基线：`d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`

任务分支：`codex/ignition-123-current-state-sync-compact-map-federation-r2-20260816`

本审计只记录仓库 Current-State 漂移、可推导事实与唯一系统图几何基线；Step 00 不修改 Current 文案，不改变任何 claim、Owner 权限或 `EPISTEMICALLY_ACCEPTED=0`。

## 结论

| 分类 | 发现 | 证据 |
| --- | --- | --- |
| `CURRENT_FACT_STALE` | Current State 能力段仍写函数/非函数 `5,663 / 17,333` | `ignition/docs/project-current-state.md:79-80`; 当前 closure summaries 为 `5,603 / 15,899` |
| `CURRENT_FACT_STALE` | Current State 限制段仍写 quarantine/pending `3,887 / 5,581` | `ignition/docs/project-current-state.md:130-131`; 当前 closure summaries 为 `4,804 / 4,615` |
| `CURRENT_FACT_STALE` | `project-state.json` 仍是 `IGNITION-20260729-100` 快照，若无历史标注会被误读为 Current | `ignition/data/foundation/project-state.json:2,35,45,58,60` |
| `CURRENT_IDENTITY_DUPLICATED` | 首页两个可见 bullet 都叫“它说什么”，重复 R2/system-map 说明 | `.github/README.md:17-18` |
| `CURRENT_IDENTITY_CONTRADICTED` | materialized map 为 `0.7.0`，subtitle 却说 `0.6.0 Current` | `interactive-system-map-layout.json:2-3`; `interactive-system-map.json:3,7` |
| `HISTORICAL_FACT_VALID` | Task 121/122 pre-release/final-candidate 日志明确标注历史 baseline 与 branch projection | `ignition/STATE-CHANGELOG.md` append-only entries |

完整逐项记录、canonical source 和未来处置见同目录的机器记录 [`current-state-drift-audit-r1.json`](../../data/architecture/current-state-drift-audit-r1.json)。

## 当前可推导事实

- Architecture registry：82 components、70 visible nodes、12 hidden components；topology 共 107 条 typed relations，其中 77 条进入可见图。
- Function assets：5,603 canonical identity cards、4,804 explicit quarantine/pending、1,923 dependency edges、12 counterexample records。
- Non-function claims：15,899 canonical claims、4,615 explicit quarantine/pending、28,567 candidate fragments、5,615 dependency edges、435 public-surface records。
- Knowledge Experience：370 cards、292 changes、308 layered readings、21,810 search records、779 aliases、53 subject indexes。
- Fire Seeds：64 seeds/clusters、371 source-census records。
- Human Surface：48 human entries、25 surfaces、14 machine/human pairs、20 two-click destinations。
- Agent Platform/Federation：4 Packs、10 capability routes、3 external adapter inventory entries；Step 00 live invocation 为 `NOT_RUN_STEP_00`。

这些是 Step 02 current-facts projection 的候选来源，不是人工复制到多个 Current 页面的新权威。

## 系统图几何基线

当前 `render_svg()` 使用 row-max：每一行先取最大 group height，再让同行所有 group 共享 `row_y`，下一行在最大高度之后开始。这个结构会把同行短 group 下方的空区和后续 row 一起推远；问题来自布局算法，不是 SVG 格式。

- Canvas：`1800 × 3988`，宽高比 `0.4513540622`。
- Group union occupancy：`46.6823%`；row-max short-group waste：`1,219,680`，占 canvas `16.9910%`。
- 最大同列连续垂直空白带：`622`；其他主要空带：`576`、`490`。
- node-center straight-segment crossing proxy：`173`；共享端点不计入，供后续布局前后比较。
- `models` group 当前 group-level degree 为 0；`agentization` 是唯一 bottom-only group，18 个节点、3 个跨组连接，row-max 使其驱动总高度。
- SVG 保留 70 个 clickable targets 和 solid background；本轮目标是紧凑、关系导向的布局重构，不是修复点击或背景缺失。

机器几何基线见 [`system-map-geometry-baseline-r1.json`](../../data/architecture/system-map-geometry-baseline-r1.json)。

## 基线门禁与安全边界

以下只读 targeted gates 均通过：system-map check、Agent Platform Human Surface、Human front door、State Changelog、Human Surface contract、Human visibility、Federation ownership、Federation routing、Pack Registry。

本步没有读取 secret 内容、没有改外部 Agent 配置、没有安装/升级、没有进行 live external invocation，也没有修改正式 `main`。
