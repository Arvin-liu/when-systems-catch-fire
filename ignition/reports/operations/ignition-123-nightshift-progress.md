# IGNITION-20260816-123 架构真相同步 R1 夜班进度

任务分支：`codex/ignition-123-current-state-sync-compact-map-federation-r2-20260816`  
正式基线：`d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`  
控制面：`1111 origin/relay/current = 7a1cfff86f1f9ad25535e277105901a9647a2222`

本报告是机器 ledger 的人类读本。每步先写入本步记录，再做独立 commit、push 和 `git ls-remote` 精确核验；commit/remote 字段在本步提交前保持待绑定，最终由闭合回执绑定，不通过 amend 或 force push 修改历史。所有结果都是仓库工程证据，不是外部真值、Owner acceptance、生产安全或 `EPISTEMICALLY_ACCEPTED`。

## Step 00 — COMPLETE

### 基线与范围

- 从 live `origin/main` 创建了全新隔离工作树；起点干净，正式 main 未修改。
- 只读检查了 Current State、首页、架构/AI 入口、状态日志、Agent Platform/Federation、Kernel/Runtime、四个 Pack、Foundation/Function/Nonfunction、Knowledge Experience、Fire Seeds、Human Surface 和唯一系统图生成链。
- 没有读取 secret 内容，没有改外部 Agent 配置，没有安装/升级，没有进行 live external invocation。

### Current-State 漂移审计

已建立机器审计 [`current-state-drift-audit-r1.json`](../../data/architecture/current-state-drift-audit-r1.json)。确定的基线问题：

- `ignition/docs/project-current-state.md` 当前能力段仍把函数/非函数数量写成 `5,663 / 17,333`；当前 closure summaries 可直接推导出的记录数是 `5,603 / 15,899`。
- 同一页当前限制段仍写 `3,887 / 5,581` quarantine/pending；当前 closure summaries 是 `4,804 / 4,615`。
- `data/foundation/project-state.json` 是 `IGNITION-20260729-100` 历史快照；若当作 Current 使用，其 `7,371 / 18,351` 和 `5,071 / 6,084` 也会漂移。该历史快照保留，不在本步原地覆盖。
- `.github/README.md` 第 17–18 行重复了同一个“它说什么”条目。
- map projection 的 `map_version=0.7.0` 与 subtitle 中“`0.6.0 Current`”相互冲突；`0.6.0` 应只作为 Historical。
- `STATE-CHANGELOG.md` 中 Task 121/122 的 pre-release/final-candidate 记录明确标注了历史基线和 branch projection，属于有效历史恢复证据，不作为 Current 漂移误报。

### 当前可推导事实快照

| 域 | 基线事实 |
| --- | --- |
| Architecture registry | 82 components；70 visible nodes；12 hidden components；107 typed topology relations；77 visible typed edges |
| Function assets | 5,603 canonical cards；4,804 explicit quarantine/pending；1,923 dependency edges；12 counterexample records |
| Non-function claims | 15,899 canonical claims；4,615 explicit quarantine/pending；28,567 candidate fragments；5,615 dependency edges；435 public-surface records |
| Knowledge Experience | 370 cards；292 changes；308 layered readings；21,810 search records；779 aliases；53 subject indexes |
| Fire Seeds | 64 seeds/clusters；371 source-census records |
| Human Surface | 48 human entries；25 surfaces；14 machine/human pairs；20 two-click destinations |
| Agent Platform/Federation | 4 Packs；10 capability routes；3 external adapter inventory entries；live invocation remains `NOT_RUN_STEP_00` |

这些数字已经写入 audit JSON，Step 02 将把可推导事实收敛到唯一 current-facts projection；本步不把 JSON 倾倒成 Human Surface 正文。

### 系统图几何基线

已建立 [`system-map-geometry-baseline-r1.json`](../../data/architecture/system-map-geometry-baseline-r1.json)。当前生成器 `render_svg()` 使用“每 row 取最大 group height，再让整行共享 row_y”的 row-max 机制。其可测后果：

- canvas `1800 × 3988`，宽高比 `0.4513540622`；group union occupancy 仅 `46.6823%`。
- row-max 产生 `1,219,680` 的同排短 group 下方空置面积，占 canvas `16.9910%`。
- 最大同列连续垂直空白带为 `622`；其次为 `576` 和 `490`。
- 直线 node-center crossing proxy 为 `173`，定义和计算方式已固定，供新布局比较。
- `models` group 当前 group-level degree 为 0；`agentization` 是唯一 bottom-only group，18 个节点并把 row-max canvas 拉到最底部，但自身仍有 3 个跨组连接。
- SVG 当前有 70 个 clickable targets 和固体背景；因此问题是布局算法及关系组织，不是 SVG 本身不可点击或缺少背景。

### 本步 targeted gates

`generate_interactive_system_map.py --check`、Agent Platform Human Surface、Human front door、State Changelog、Human Surface contract、Human visibility、Federation ownership、Federation routing 和 Pack Registry 均为 `PASS`。本步没有引入修复回合，也没有提前修改 Current 文案。

### Step 00 交付物

- `ignition/data/architecture/current-state-drift-audit-r1.json`
- `ignition/reports/architecture/current-state-drift-audit-r1.md`
- `ignition/data/architecture/system-map-geometry-baseline-r1.json`
- `ignition/data/operations/iterations/123/fixtures/current-state-sync-fixtures-r1.json`
- `ignition/data/operations/iterations/123/nightshift-progress.jsonl`
- 本步精确 commit/remote SHA 待本步独立提交及 `ls-remote` 核验后由最终闭合回执绑定。

下一步：建立 `CURRENT_STATE_SYNC_INVARIANT` 的唯一机器 identity contract、schema、validator 和负向 fixture 门禁。
