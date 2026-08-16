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
