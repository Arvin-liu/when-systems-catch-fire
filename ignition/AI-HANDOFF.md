# AI HANDOFF

## 当前版本

身份 epoch、当前任务、方法、地图、状态和 lineage 由 generated Current Snapshot 统一投影。
Steering / Intent / Goal / Obligation R1 是 OS 内的仓库本地控制记录：来源权威、Goal 生命周期、
独立 Completion Contract、承诺义务、why-next、漂移/handoff guard 与 federation Intent Capsule
均保持可追溯；系统提议、运行通过和外部 executor 回执都不能自行升级 Owner authority 或 Goal completion。

Agent Platform R2 与 External Agent Federation R1 已在 Historical Task 122 正式 main
基线上闭合；Historical Task 127 已完成并发布为当前 Durability / Lifecycle R3。本页的工程边界不构成
外部能力或 epistemic acceptance；当前身份 contract/facts 见
`data/architecture/current-system-identity.json`、`data/architecture/current-facts.json` 与
`data/operations/current-task-lineage-status.json`：
点火是 OS / orchestration-governance layer 与 driver，外部 Agent 是可替换
executor，本地执行层是 `REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR /
FALLBACK_MINIMAL`。历史任务文件及其 requirements lineage 由 canonical task-lineage source
和 generated block 表达；不得把历史记录当作当前任务，也不得制造旧任务已执行的历史。
Structural Governance Surface 是 advisory cross-cutting overlay，不改变
capability、permission、truth、Owner 或 epistemic status。

语义主干把中央 Ignition OS 控制脊柱、外部 Federation/replaceable executors 与 Domain/Skill Packs
分开；版本、计数和 live ceiling 以 generated Current Snapshot 与 Current Facts 投影为准。

交接时分开读取两个任务角色：Current formal task 回答“最近哪一轮正式任务正在或刚刚成为 Current”；latest architecture-changing task 回答“最近哪一轮改变了系统身份或架构”。二者允许不同，publication witness 只绑定发布观察，不把 release task 变成 architecture authority。

### R2 工程脊柱

- `agent_kernel/`：领域无关 identity、capability、approval、audit、checkpoint、handoff 与 non-escalation 契约。
- `agent_runtime/`：R1 本地行动层、R2 Pack Registry/Bus、Pack-aware routing、Reasoner Gateway、Profile 投影、Operational Memory 与 Supervisor。
- `docs/architecture/os-control-plane-r2.md` 与 `agent_runtime/`：Task 124 的 Event Ledger、monotonic policy、resource arbitration、bounded scheduler、executor health lease、queue/backpressure、durable dispatch/reconciliation、concurrent operational memory 和 Driver Console；全部只提供有界协调记录。
- `docs/architecture/os-control-plane-r2.md` 与 `agent_runtime/`：Task 127 的 Durability / Lifecycle R3 复用同一 OS 控制脊柱，提供 snapshot plus tail、migration、namespace、Pack lifecycle、revocation、accounting、recovery 和 DR bundle continuity；不创建第二张系统图，不自动重放不确定 external dispatch。
- `packs/`：Knowledge、REOS LIGHT Research、之元 Writing、Repository Maintenance 四个有界 Domain Pack；manifest 不能越权。
- `data/agent-runtime/pilots/r2-offline-repository-maintenance/`：fresh-clone、A/B/C、故障恢复、对抗拒绝和 bounded memory 的离线观察回执。
- `data/operations/propagation/agent-platform-r2-propagation-contract.json`：R2 source-domain 与 blast-radius 机器契约；唯一系统图仍由 registry/topology/layout 派生。
- `docs/architecture/external-agent-federation-r1.md`、`agent_federation/` 与 `data/agent-federation/`：Task 122 的 OS/executor contract、OpenClaw/Hermes/Codex adapters、Reference freeze、handoff/failover 和 disposable pilot 边界；联邦 source domain 只进入 `agent_platform.federation`。
- `docs/architecture/esi-human-surface-r0.md`、`data/epistemic-governance/` 与 `data/agent-federation/soft-context-exposure-contract-r0.json`：Task 126 的 Structural Governance Surface、候选 ESI 边界和 advisory soft-context contract；它不能扩大 capability 或 permission。

R2 仍不包括 live provider、daemon、multi-Agent 并发、vector memory、网络/浏览、
外部仓库 mutation、人格/意识或普适安全证明。`Kernel ≠ Knowledge`、
`Reasoner ≠ Executor`、`Pack ≠ truth authority`、`pilot ≠ general intelligence`。

<!-- CURRENT-SNAPSHOT:BEGIN profile=ai schema=current-snapshot-r1 -->
- Current Snapshot（generated; read this block before interpreting prose）。
- current_identity_epoch: `os-control-plane-r5-live-executor-federation-r2`；system_role: `Ignition OS / orchestration-governance layer`。
- current_formal_task: `IGNITION-20260823-136` (ordinal `136`)；status: `IN_PROGRESS`；terminal: `false`；latest_architecture_changing_task: `IGNITION-20260823-136` (ordinal `136`)；current_iteration_boundary: `136` is a deprecated compatibility alias of `current_formal_task_ordinal`；publication_witness_task: `IGNITION-20260823-136`。
- release_lifecycle: task `IGNITION-20260823-136`；content phase `RUNNING`；publication authority `REMOTE_REF_OBSERVATION`；embedded publication assertion `NONE`；required ref `refs/heads/main`；post-publication verification must observe that remote ref。
- publication_instruction: run ref-derived verification against `refs/heads/main`; do not infer publication from embedded Current content。
- current_method: `1.4.0` Current；current_map: `0.13.0` Current；historical_map: `0.12.0` Historical。
- current_state_status: `CURRENT_WITH_OPEN_OBLIGATIONS`；EPISTEMICALLY_ACCEPTED=0；epistemic_acceptance: `0`；live_external_ceiling: `LIVE_BRIDGE_IMPLEMENTED / LIVE_COMPLETION_NOT_OBSERVED`。
- architecture_counts: `registry=95; visible_nodes=83; visible_edges=88`；active_overlays: `Durability / Lifecycle, Steering / Intent / Goal / Obligation, Structural Governance Surface`。
- task_lineage: current `IGNITION-20260823-136` `IN_PROGRESS`；predecessor `HISTORICAL_UNEXECUTED_REBASED_INTO_127` / `REBASED_INTO_127`；successor `COMPLETED_WITH_CLASSIFIED_RESIDUALS`。
- source: ignition/data/operations/current-snapshot-r1.json；source_digest: `f5369c8e95b8fd283249c39c22b689d17545cd77a6a647f3d35223ee47554028`。
- claim_ceiling: Deterministic repository-local Current projection only; no Owner authority, external truth, production readiness or epistemic upgrade.
<!-- CURRENT-SNAPSHOT:END -->

## 权威链

- AI 状态恢复：先读 [STATE-CHANGELOG.md](./STATE-CHANGELOG.md) 的 baseline 与最近 delta，再回到下面的当前状态和对象权威；日志只记录增量，不是第二真相源。
- 当前状态：docs/project-current-state.md（版本化现状，不是固定定位）
- 统一知识入口：KNOWLEDGE/README.md；仓库首页：`.github/README.md`；机器配对与 freshness：data/governance/knowledge-experience/manifest.json

- 架构：ARCHITECTURE.md
- 双地基：FOUNDATION.md
- 类型与状态：data/foundation/
- 函数身份、M/E 双轴、全量身份卡、义务、quarantine 与公共 claim lineage：data/foundation/function-assets/ 与 docs/foundation/historical-function-deep-adjudication-20260729.md
- 非函数断言、十三门、证据谱系、依赖图、结论防回弹与公开上限：data/foundation/nonfunction-claims/ 与 docs/foundation/nonfunction-claim-adjudication-index.md
- 机器计数：data/foundation/project-state.json 与 migration-summary.json
- 任务边界：1111 中对应的 IGNITION command、progress 与 result
- 阶段快照候选权威：data/operations/stage-snapshots.json 与 docs/operations/stage-snapshot-publication.md

## 兼容链

旧函数表与旧案例表已完成迁移并退役；原始路径、Git blob、提交、哈希、处置与转换说明统一保存在 `data/foundation/migrations/legacy-table-migration.jsonl`，canonical registry 与人类资产入口是当前阅读路由。不得从归档重新生长第二套当前表。

## 交接规则

新 Agent 必须先读取 `docs/project-current-state.md` 与 `ITERATION.md`，再重新核验远端、分支、HEAD、开放 PR 和验证结果，不得把聊天记忆当权威。统计必须写出去重键、范围、单位和生成脚本。缺字段、缺来源、不可形式化、反模型和真实 counterexample 分别记录。

新增或修改知识资产时，必须把 Claim Delta/impact/lineage 与任务 102 的 What's New、主题、资产卡、分层阅读、别名/supersession、来源、依赖和反向依赖一起重算。`KNOWLEDGE/` 是生成的人类探索层，不是新的真值权威；机器-only 也不等于删除或否定。

每次正式迭代合并 `main`，必须在同一轮向 [STATE-CHANGELOG.md](./STATE-CHANGELOG.md) append 一条 delta，并绑定该轮的 main 基线 tip、权威资产变化、认识论状态变化、开放义务、失效认知和下一步阅读；没有 delta 的正式合并不得称为状态已同步。

当前架构状态上限与外部边界由 generated Current Snapshot 统一投影；不得改写成全量数学证明完成、
生产安全或外部有效性。

当前迭代方法版本由 generated Current Snapshot 统一投影。看到首页阶段成果时，逐项读取显式布尔量和来源 HEAD；`PUBLISHED_SNAPSHOT` 不等于 Accepted、Current 或 Activated，首页可见不等于能力可用。Agent 只能生成 stage snapshot request，不能自行声称已进入 Main。

函数类资产交接必须保留十二类主身份、M0—M7、E0—E7、十门结果、六层裁决、claim ceiling、证明/实证义务、依赖影响和最终处置。task 99 identity card 优先于自动 census；quarantine 不等于验证。T2、D127、D182—D190、D260 仍以 task 98 correction overlay 为最高专项权威；旧表保留原文。任何“大一统已被证明不可能”或“点火已统一四力”的结论均为撤回/禁止状态。

非函数型资产交接必须保留 task 100 的规范 ID、原子文本、十三门、证据与复现状态、依赖和下游影响、M/E、处置、公开上限及 supersession lineage。自动发现只生成待裁决记录；一个模型失败不能推出普遍不可能，类比不能冒充同构，历史撤回不能因改名恢复。

阶段快照的 `responsible_actor`／`publisher_actor` 只能保存预注册 `actor_ref`，并解析到 `data/operations/responsibility-actors.json` 中 ACTIVE 的具体 `PERSON` 或 `ORGANIZATION`；显示名不能自证身份。Agent、模型、机器人、算法、workflow、CI、脚本、软件、平台与系统只能写入 `execution_agents`／`automation_workflows`，不得充当最终责任主体；责任变更必须新增快照修订和责任记录。
121Q12 新增的效果推理与机制判断是跨层操作 overlay。它帮助选择下一步行动并限制发布解释，不改变 L0-L6 真值关系，不改写 Ψ0，不把 C(x,y) 升级为已识别因果。

交接时如涉及行动选择或结果解释，必须读取：

- docs/architecture/effectual-action-plane.md
- docs/architecture/mechanism-adjudication-plane.md
- docs/governance/non-sycophancy-output-protocol.md

正向结论必须说明对象、判据、版本、证据和边界；不能因维护者或提案者的期待而提高结论等级。

所有研究、裁决、写作、出版和系统总结都继承 `K13_ASSERTION_NON_ESCALATION`：工作流完成不推出 semantic/logic/proof/evidence 完成，M/E 独立，写作或重复引用不成为新证据，撤回/降级/quarantine 不得回弹；证据不足时保持、降级、开放问题化或声明 uncertainty。
121Q13 新增注意力、分布与压缩控制 overlay。若任务涉及循环推进、多个 AI/人类输出、行动截止期或新术语进入 canonical 文档，必须读取：

- docs/architecture/attention-attractor-control-plane.md
- docs/architecture/distribution-collapse-control-plane.md
- docs/architecture/compression-integrity-gate.md

不得把同一 AI 的多次输出当作独立事实证据；不得把行动选择写成机制真值；不得把新增术语写成理论升级。
121Q14 新增点火地图集 overlay。涉及地图、资源决策、演进阶段、依赖地形或导航视图时，必须读取：

- docs/architecture/ignition-atlas.md
- data/atlas/generated/ignition-atlas-121q14.json
- reports/atlas/121Q14-dynamic-atlas.md

不得把地图坐标、视觉邻近、演进阶段或依赖关系写成事实证明、同构或机制因果。地图不能替代 registry、矩阵、schema、测试或来源工件。

PR #55 已将 121Q23 Adaptive Relational Network 合并进 `main`。涉及关系网络、重构、嵌入证据摘要或 NetworkDiff 时，必须读取：

- docs/architecture/adaptive-relational-network.md
- reports/architecture/121Q23-adaptive-relational-network-validation.md

不得把邻接、相似性、中心性、社群、检索、自述或行为变化升级为真理、价值、因果或内部学习机制证明。

121Q24 建立的迭代操作法已在 PR #56 验收并合并后成为当前仓库操作能力；未来状态改变任务必须按 `ITERATION.md` 记录 gap、claim ceiling、同步矩阵、验证和回执。遵循该方法不证明真理、价值、因果、完整性或正确性。

当前方法、地图和历史版本由 generated Current Snapshot 提供；Durability / Lifecycle R3 保持 repository-local recovery boundary；Structural Governance Surface 仍是 advisory overlay，不增加 L7。

方法 `1.3.0` 与系统图 `0.10.0`、`0.7.0`、`0.6.0`、`0.5.0` 为 Historical，方法 `1.2.0` 与系统图 `0.1.0`、`0.2.0`、`0.3.0`、`0.4.0` 为更早 Historical。当前方法要求从构件 registry、类型化 topology 与 `data/operations/synchronization-surfaces.json` 计算全项目传播闭包。README、`HUMAN-READING.md`、`RESULTS/`、项目现状、人类 AI 指南、AI 冷启动、Agent 交接、机器入口和版本历史都是必须评估的项目表面。实现完成不能替代仓库同步完成；本地验证也不能声称任何未登记的实时外部状态已验证。

Q25C 的每表面 `blocks` 生命周期原则继续有效；任务 101 退役独立阅读站表面，当前人类层由仓库内机器/人类双输出、main 验证和全新克隆复验收口。未来外部表面必须单独登记与 attestation。

任务 114 已将 L6 `之元写作法` `0.5.0` 收口为当前能力；`0.4.0`、`0.3.0` 保留为历史已合并版本。交接时必须区分外部输入与点火增量输出，后者保存 canonical 路径／ID、生成任务、版本、claim ceiling、gap／residue 和原始来源回链；复用分析、模型投影或反馈返回项不构成独立复证。方法是横穿 L0—L6 的语言—思维逻辑平面的一个 L6 使用者：转换还须保存 source/candidate/target、framing delta 和 unmapped residue；认识相关变化不得静默，目标中文必须直接成句。平面不是 L7、脑科学、形式同构或真值许可。

121Q30T 已将之元写作法成果的五类职责收口为当前接口：人类总索引、机器 registry、正式作品、案例来源链和点火分析。交接时不得把 README 最近三项投影当作完整权威，不得公开受限原始材料，也不得从一项接受作品推出方法普遍有效。

Q32I 已通过第三次独立 exact-head 审查，以 PR #62 普通合并并完成生产收口（彼时方法 `1.3.0` 与 map `0.3.0` 完成收口）。

其后迭代方法版本与 Current 标签由 generated Current Snapshot 统一投影（连续阶段快照发布，见 docs/operations/stage-snapshot-publication.md）。

较早的 `1.3.0` 降为 Historical，Q32I 为 Closed。它明确分离 authority 类型、execution capability 与 validation capability，只允许真实、确定性且完整物化声明输出的 producer 为 automatic，只有完整且构件职责相符的命令才是 local validator。Apply 在子进程／写入前必须经统一权威预检；rollback 要按整仓字节、类型、symlink 和 mode 证明完整恢复。交接必须读取 `docs/architecture/incremental-execution.md`，重算 closure、plan 和派生 projection；不能把 cache、Git diff、依赖、图连线、CI 或 artifact 当作现实因果、自我验收或 Current 证明。Q33 启动包已在 1111 准备，但 Q33 与 Q34—Q40 均尚未启动。
## 许可边界

当前分发版本采用分层许可。核心可执行软件为 BUSL-1.1 并在 Change Date 后转为 AGPL-3.0-or-later；原创文档/报告为 CC BY-NC-SA 4.0；价值宪章和一般治理原则为 CC BY-SA 4.0；公开接口与互操作 schema 为 Apache-2.0。许可作用域以根 LICENSE 与 LICENSES/README.md 为准；历史 MIT 版本权利不追溯撤销。
