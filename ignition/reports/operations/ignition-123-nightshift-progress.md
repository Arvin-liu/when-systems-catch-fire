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

## Step 01 — COMPLETE

### Contract and handshake

建立了唯一机器身份契约 [`current-system-identity.json`](../../data/architecture/current-system-identity.json)：

- `contract_id=CURRENT_STATE_SYNC_INVARIANT`，identity epoch 为 `agent-platform-federation-r1`，当前边界为 Task 122 正式 main。
- 当前状态仍是 `CURRENT_WITH_OPEN_OBLIGATIONS`，`EPISTEMICALLY_ACCEPTED=0` 保持不变。
- 当前身份明确为 Ignition OS / orchestration-governance layer、driver、replaceable external executors；Knowledge 是第一大 Domain Pack；本地执行层冻结为 `REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL`。
- 16 个 current-facts 指标使用 canonical JSON source + JSON-pointer derivation recipe，契约不复制维护第二份数量真相。
- 已显式记录 live external invocation、production/external validity、Knowledge proof/replication 三类开放义务和 authority ceiling。

加入了 receipt schema 与本迭代 receipt [`current-state-sync-receipt.json`](../../data/operations/iterations/123/current-state-sync-receipt.json)。Step 01 的影响分类是 `PRESENTATION_ONLY`：本步引入同步门禁和治理说明，不提前改写已在 Step 00 记录的 Current 文案、首页重复描述或 map 内容；所有十个声明 surface 都有 `NO_CHANGE_WITH_REASON`。这不是 architecture-content closure。

### Validator, governance and CI

- `ignition/tools/validate_current_state_sync.py --check` 校验 schema、路径不逃逸、当前 method/map identity、16 个 live-derived metrics、开放义务 source、receipt handshake 和 fixture manifest。
- 对 `ARCHITECTURE_CHANGED`，校验器要求每个声明 surface `CHANGE` + evidence，并额外检查 Current stale counts、首页重复 identity bullet、map-version coherence 和 bounded concepts。
- `AGENTS.md`、`ignition/ITERATION.md` 和 [`current-state-sync-invariant.md`](../../docs/governance/current-state-sync-invariant.md) 已把该 invariant 纳入冷启动与迭代规则。
- `.github/workflows/current-state-sync-validation.yml` 在 pull request/main push/手动运行时执行该 gate。
- [`test_current_state_sync.py`](../../tests/test_current_state_sync.py) 共 6 个测试：live receipt PASS、fixture 正负覆盖、ARCHITECTURE_CHANGED 缺 surface 失败、PRESENTATION_ONLY 越权 CHANGE 失败、自引用 SHA 失败。

### Targeted gates and boundary

JSON parse、current-state sync validator、6 个 unit/negative tests 和 `git diff --check` 均为 `PASS`。未读取 secret，未改外部配置，未安装/升级，未执行真实外部 Agent invocation；本步 live 状态为 `NOT_RUN_STEP_01`。正式 main 仍保持 `d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`。

本步 claim ceiling：repository synchronization contract and merge gate only；不推导 architecture-content synchronization、external truth、Owner acceptance、production safety 或 epistemic upgrade。精确 Step 01 commit/remote SHA 待本步独立提交、push、`ls-remote` 核验后由最终闭合回执绑定。

下一步：生成唯一 current-facts projection，并将当前数量从 contract recipe 投影到可审计机器事实源，继续保持历史快照不被覆盖。

## Step 02 — COMPLETE

### Deterministic projection

已建立 [`current-facts.json`](../../data/architecture/current-facts.json) 与其窄范围人读 block [`current-facts.md`](../../docs/architecture/current-facts.md)。生成器 [`generate_current_facts.py`](../../tools/generate_current_facts.py) 只读取并指纹化 canonical registry、topology、map/method、四个 Pack manifest、Federation executor inventory、Foundation closure summaries、Knowledge Experience manifest、Fire Seeds census、Human Surface materiality/config/synchronization registry，以及 contract/generator/schema 输入；不覆盖 `project-state.json` 等历史快照。

当前 projection 事实为：82 components、70 visible map nodes、12 hidden represented components、107 typed relations、77 visible typed edges；map `0.7.0` Current、method `1.4.0` Current；4 Packs/10 capability routes；3 external adapter inventory entries，live ceiling 仍为 `NOT_RUN_LIVE_EXTERNAL_INVOCATION`；function/non-function `5,603 / 15,899` canonical records 和 `4,804 / 4,615` quarantine/pending；Knowledge Experience `370 / 292 / 308 / 21,810 / 779`；Fire Seeds `64 / 371`；Human Surface materiality entries `48`、registered sync surfaces `20`、machine/human pairs `14`。环境残余仍逐字保留为来源 inventory 的声明，不被解释为真值或 proof status。

### Determinism and authority boundary

- `current-facts.schema.json` 锁定 projection 结构；`current-system-identity.json` 现在声明 JSON、Markdown、schema 和 generator 的 canonical projection 路径。
- `generate_current_facts.py --check` 与 `validate_current_state_sync.py --check` 均为 `PASS`。
- 同一输入连续两次生成的 JSON 和 Markdown 都 byte-identical；7 个 current-state sync unit/negative tests 为 `PASS`。
- JSON 记录所有 canonical 输入及 generator/schema 的 SHA-256 source fingerprints；没有生成时间、self-referential commit SHA 或手工期望数量表。
- 人读 block 只承载 bounded current-facts marker，Step 03 再将其作为 Current State 的事实锚点；本步没有把 `project-current-state.md` 变成机器模板，也没有修写历史章节。

Step 02 receipt 保持 `architecture_identity_impact=PRESENTATION_ONLY`，所有十个已声明 identity surface 仍有明确的 `NO_CHANGE_WITH_REASON`；本步是确定性 derived projection，不是 architecture-content closure。未读取 secret，未改外部配置，未安装/升级，未执行真实外部 Agent invocation；本步 live 状态为 `NOT_RUN_STEP_02`。正式 main 仍保持 `d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`。

本步 claim ceiling：deterministic repository-derived current facts and navigation support only；不推导 external truth、Owner acceptance、production safety 或 epistemic upgrade。精确 Step 02 commit/remote SHA 待本步独立提交、push、`ls-remote` 核验后由最终闭合回执绑定。

下一步：依据 contract + current-facts，修订 `project-current-state.md` 的 Current 区域、清除首页重复 identity 描述，并把历史数字显式留在历史语境。

## Step 03 — COMPLETE

### Current State re-convergence

`docs/project-current-state.md` 现在先回答当前系统是什么，再保留 Task 112—122 的可回链历史。Current 主体明确：点火是长期状态、价值、任务、权限、记忆、验证、provenance、handoff 与 executor 协同的 OS / orchestration-governance layer 和 driver；OpenClaw、Hermes、Codex 是可替换执行器；Knowledge 是第一个大型 Domain Pack；本地执行层冻结为 `REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL`。

Current 区域不再使用旧的 `5,663 / 17,333` 与 `3,887 / 5,581` 作为当前数字；它改为指向确定性 `current-facts.json`，并使用 `5,603 / 15,899` canonical counts 与 `4,804 / 4,615` quarantine/pending。旧任务史仍保留在明确的历史上下文中，不再承担 Current 数字权威。Current 限制同时明确 live provider/inference、daemon、multi-Agent、vector memory、network/browser、external Git mutation、物理 Pack 拆分与真实外部效果的开放边界。

### Front-door and AI identity repair

- `.github/README.md` 删除重复的“它说什么”条目，并把 OS/driver 与 replaceable executor 关系、Reference/Conformance/Fallback 冻结和 facts pointer 说清楚。
- `AI-START-HERE.md`、`AI-HANDOFF.md` 和 `llms.txt` 都指向 identity contract/current facts；handoff 不再把已正式闭合的 Task 122 误写成仍待正式 main 的 pre-release。
- 因 `AI-HANDOFF.md`、`project-current-state.md`、`llms.txt` 和 Step 01 的 `ITERATION.md` 是 Human Surface materiality 的声明来源，manifest 中对应 source SHA-256 已按实际字节刷新；没有改写任何 claim/content registry。

本步 receipt 明确标为 `PRESENTATION_ONLY`：五个受影响 surface 为 `CHANGE` + evidence，其余 architecture/map/Federation/state-changelog surface 各有 `NO_CHANGE_WITH_REASON`。`PRESENTATION_ONLY` 现在允许有证据的 scoped presentation change，但仍禁止 `surface_sync_complete=true`；只有真正的 architecture identity change 才触发全 surface closure。这样保持了“解释同步”与“架构语义变更”的边界。

### Targeted gates and boundary

Current-state validator、current-facts determinism、Human Surface contract、Human front door、Human visibility、State Changelog 和 7 个 unit/negative tests 均为 `PASS`，`git diff --check` 通过。未读取 secret，未改外部配置，未安装/升级，未执行真实外部 Agent invocation；本步 live 状态为 `NOT_RUN_STEP_03`。正式 main 仍保持 `d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`。

本步 claim ceiling：Current State/front-door presentation synchronization plus deterministic derived facts and materiality fingerprints only；不推导 architecture-content closure、external truth、Owner acceptance、production safety 或 epistemic upgrade。精确 Step 03 commit/remote SHA 待本步独立提交、push、`ls-remote` 核验后由最终闭合回执绑定。

下一步：重构唯一系统图的布局根因，从 row-max 改为紧凑、关系导向的 packing，并保留单一可点击总图。

## Step 04 — COMPLETE

### Compact layout refactor

`generate_interactive_system_map.py` 已移除 row-max 共享行游标：现在从 typed visible relation graph 构造 group dependency graph，先做确定性 SCC condensation/topological rank，再在每个 semantic column 内按 rank、声明 row、group id 排序；每个 column 使用自身 cursor 和自身 group height，组间使用显式 `vertical_gap`。布局契约把算法固定为 `deterministic-scc-ranked-column-packing-r1`，并把 `top_offset`、`vertical_gap` 与全部几何尺寸纳入 schema 和生成器校验。

唯一物化图已从 layout `1.4.0` 更新为 `1.5.0`，当前 SVG canvas 从基线 `1800×3988` 压缩为 `1800×2978`，高度减少约 `25.3261%`。`models` 不再作为底部孤立模块，`agentization` 虽然仍是高组但不再以 row-max 机制把其他列整体向下撑开；节点身份、typed edges、canonical targets 和单一图入口保持不变。

### Targeted gates and boundary

`generate_interactive_system_map.py --check` 输出 `SYSTEM_MAP_DERIVED_OK nodes=70 edges=77`；新增确定性几何测试 3 项全部通过：两次 projection/render byte-identical、canvas 高度显著低于 row-max baseline、同列 group 不重叠且每个 visible node 仍有 clickable target。SVG 保留一个 solid background rect 和 70 个 links。current-facts projection 已重生成并通过 check，Current State sync validator 通过，`git diff --check` 通过。

未读取 secret，未改外部 Agent 配置，未安装/升级，未进行真实外部 Agent invocation；本步 live 状态为 `NOT_RUN_STEP_04`。正式 main 仍保持 `d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`。

本步 claim ceiling：deterministic repository layout/projection and accessibility evidence only；不推导 architecture-content、external truth、Owner acceptance、production safety 或 epistemic upgrade。

下一步：在紧凑图上固定语义主干、关系类型和阅读路径，继续保持 geometry 与 semantic projection 分离。

## Step 05 — COMPLETE

### Semantic trunk and ownership boundary

当前系统图已从单一底部 `agentization` 长条改为三个有明确职责的投影：中央列的 `os_spine` 包含 Owner/Human、Agent Profile、Kernel、Runtime 与 Memory；右侧 `federation` 明确承载 External Agent Federation、OpenClaw、Hermes、Codex、Reference/Future Executors 与环境接口；`domain_packs` 单独承载 Pack Contract、Knowledge、Research、Writing 与 non-knowledge pilot。原有 70 个可见节点和 77 条 typed edges 均保留，registry 的 map projection group 已同步升至 `1.7.0`。

布局 overlay 现在声明 `semantic-trunk-r1` 的六段有界阅读路径：`Owner / Value Charter → Ignition OS control / governance spine → Pack / Federation routing → External replaceable executors → Actions / observations / receipts → Validation / provenance / state update / feedback → OS`。生成器校验每个阶段的 node/relation ids 来自现有 registry/topology，并在 SVG 顶部渲染同一条可读主干带；它不合成新边、不声明现实因果，且显式保留“外部完成不等于 OS acceptance”和权限不升级边界。

当前 map version 按版本制度推进为 `0.8.0 Current`，`0.7.0` 作为 Historical；layout 为 `1.6.0`。Step 04 的 `1800×2978` canvas 在语义分组后进一步收敛为 `1800×2470`，中央 OS group 位于 `x=620,y=122`，外部 Federation 与 Domain/Skill Pack 不再被误读为 Kernel 或底部孤立平台。

### Targeted gates and boundary

`generate_interactive_system_map.py --check` 输出 `SYSTEM_MAP_DERIVED_OK nodes=70 edges=77`；新增 semantic-trunk/clickability 测试与 Current State sync 回归共 11 项通过。layout schema、current-facts schema、两次 current-facts 生成、Current State sync、`git diff --check` 均为 `PASS`。current-facts 已记录 `semantic-trunk-r1` 与 6 个 route stages；Canonical map guide 已同步 0.8.0 与 OS/Federation/Pack 阅读边界。

未读取 secret，未改外部 Agent 配置，未安装/升级，未进行真实外部 Agent invocation；本步 live 状态为 `NOT_RUN_STEP_05`。正式 main 仍保持 `d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`；正式 `STATE-CHANGELOG` architecture delta 保留到 Step 12。

本步 claim ceiling：deterministic repository semantic navigation, group projection and current-facts evidence only；不推导 external truth、Owner acceptance、production safety 或 epistemic upgrade。

下一步：把 compact layout 的空白、重叠、越界、点击覆盖、crossing、孤立 group 与移动端 viewport 条件固化为 deterministic geometry quality gate，并加入旧 row-max negative fixture。

## Step 06 — COMPLETE

### Geometry quality gate

新增 [`system-map-geometry-quality-r1.json`](../../data/architecture/system-map-geometry-quality-r1.json) 与 [`validate_system_map_geometry.py`](../../tools/validate_system_map_geometry.py)。门禁从生成的 canonical SVG 和 typed projection 重新测量 group/node boxes、内部空白、包络 padding、label baseline、click target、solid background、group isolation、edge crossing proxy 与移动端 viewport，不把“文件可生成”当作布局质量。

相对 Step 00 row-max baseline，当前 `1800×2470` canvas 高度下降 `38.0642%`；按实际同列内部 corridor 面积计算的无信息空白下降 `87.4101%`；edge crossing proxy 为 `160`，基线 `173`，比例 `0.9248554913`；最大内部垂直 gap 为 `28`；group occupancy 为 `0.784957265`。13 个 group 与 70 个 visible node 均无重叠、无越界、无 label clip；70/70 clickable targets 覆盖正确；固体背景为 1；两个代表性 mobile viewport 均无需横向拖动才能 fit；底部 group 中没有 degree-zero 孤立组。

加入两个负向 fixture：恢复 Step 00 的旧 row-max baseline 必须因 blank reduction、height reduction、max gap、node geometry 与 mobile-fit 失败；把两个 group 压到同一坐标的“伪紧凑”布局必须因 `group_box_overlap` 失败。质量报告 schema 与 14 项 geometry/map/current-state tests 全部通过。

### Targeted gates and boundary

`SYSTEM_MAP_GEOMETRY_OK height=2470.0 blank_reduction=0.8741007194 crossing=160`、`SYSTEM_MAP_GEOMETRY_FIXTURES_OK`、system-map generator、current-facts、Current State sync、Human Surface/front door/visibility、State Changelog、schema 和 `git diff --check` 均为 `PASS`。生成器同时显式写入 `preserveAspectRatio=xMidYMin meet`、group `data-group` 和两行可验证的 group descriptions。

未读取 secret，未改外部 Agent 配置，未安装/升级，未进行真实外部 Agent invocation；本步 live 状态为 `NOT_RUN_STEP_06`。正式 main 仍保持 `d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`；正式 `STATE-CHANGELOG` architecture delta 保留到 Step 12。

本步 claim ceiling：deterministic repository geometry, accessibility and regression evidence only；不推导 external truth、Owner acceptance、production safety 或 epistemic upgrade。

下一步：以同一 identity contract 收敛所有 Current Human/AI、Architecture、Federation、Results 与 State Changelog 表面，消除 0.7/0.8 和旧 agentization 叙述残余。

## Step 07 — COMPLETE

### Current identity surface synchronization

以 `CURRENT_STATE_SYNC_INVARIANT`、`current-system-identity.json` 和确定性
`current-facts.json` 为同一身份基线，完成 Current Human/AI、Architecture、
Federation、Results 与系统图维护说明的收敛。当前一致语义为：点火是 OS /
orchestration-governance layer 与 driver；OpenClaw、Hermes、Codex 是外部可替换
executors；Knowledge 是第一个大型 Domain Pack；本地执行层冻结为
`REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL`；外部完成不自动
成为 OS validation。当前地图是 `0.8.0`，`0.7.0` 及更早版本均为 Historical。

修订了 `AGENTS.md`、首页、`project-current-state.md`、`ARCHITECTURE.md`、AI
cold-start/handoff、`llms.txt`、Human Reading、Agent Platform/Federation 文档、
当前 Results、成果册的正式仓库结果章节和 system-map maintenance guide。系统图
维护说明不再把当前 R2 说成单一旧 `agentization` overlay，而是明确中央 `os_spine`、
外部 `federation` 与 `domain_packs` 三个有界投影。Current Results/成果册改为
引用 current-facts 的 `5,603 / 15,899` counts 与 `4,804 / 4,615`
quarantine/pending；历史报告、生成 Knowledge 索引和 provenance 不被重写。

`STATE-CHANGELOG.md` 新增了明确标注为 task-branch projection 的 Step 07 recovery
entry，声明正式 `main` 仍为 `d60ec8687fb1cc6b972e831a8f0dcd348ba0e83e`；它不是
Step 12 的 formal main release delta。相关 materiality source fingerprints 已刷新，
current-facts JSON/Markdown 重新生成并保持 byte-deterministic。

### Targeted gates and boundary

`CURRENT_FACTS_DETERMINISTIC_OK`、`CURRENT_STATE_SYNC_OK`、
`AGENT_PLATFORM_HUMAN_SURFACE=PASS surfaces=18 map=0.8.0 registry=82 visible=70
edges=77 hidden=12`、Human front door/contract/visibility、system-map generator
和 `git diff --check` 全部为 `PASS`。未读取 secret，未改外部配置，未安装/升级，
未执行真实 external invocation；本步 live 状态为 `NOT_RUN_STEP_07`。

本步 claim ceiling：Current Human/AI/Architecture/Federation/Results identity
同步与 deterministic current-facts 导航证据仅限仓库范围；不推导 external truth、Owner
acceptance、production safety 或 epistemic upgrade。正式 main architecture/state
delta、Reference Executor 长期 CI 边界、真实外部 smoke/cross-executor pilot、独立
review 与 final release 仍开放。

下一步：把 default integrate、Reference/Conformance/Fallback freeze、禁止 runtime
层扩张和 conformance evidence 做成长期 CI 边界，进入 Step 08。
