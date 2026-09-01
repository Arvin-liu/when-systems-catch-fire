# 点火项目现状

更新时间：2026-08-28。以下 Current 摘要先回答“现在是什么”；任务史保留为可回链证据，不再承担 Current 数字权威。
<!-- CURRENT-SNAPSHOT:BEGIN profile=human schema=current-snapshot-r1 -->
- Current Snapshot（机器生成；请勿手改）。
- current_identity_epoch: `os-control-plane-r8-task-lifecycle-decoupling-executor-admission-r1`；system_role: `Ignition OS / orchestration-governance layer`。
- current_formal_task: `IGNITION-20260829-148` (ordinal `148`)；status: `COMPLETED_WITH_OPEN_OBLIGATIONS`；terminal: `true`；latest_architecture_changing_task: `IGNITION-20260827-142` (ordinal `142`)；current_iteration_boundary: `148` is a deprecated compatibility alias of `current_formal_task_ordinal`；publication_witness_task: `IGNITION-20260829-148`。
- formal_task_terminality: authority `FORMAL_TASK_LIFECYCLE`；task `IGNITION-20260829-148` status `COMPLETED_WITH_OPEN_OBLIGATIONS`；terminal `true`；scope_complete `true`；open references `['LIVE_EXTERNAL_INVOCATION']`。
- formal_task_terminal_history: `[{"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260829-148", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260828-147", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260828-146", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260828-145", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260828-144", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260827-143", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260827-142", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260826-141", "terminal": true}]`；Task141 terminality remains recorded independently of the carried obligation。
- open_obligation_registry: authority `OPEN_OBLIGATION_REGISTRY`；status `OPEN` ids `['LIVE_EXTERNAL_INVOCATION']`；count `1`；next eligible action `['OWNER_DEFERRED_REQUIRES_EXPLICIT_REOPEN_AND_LOCAL_ENVIRONMENT_PREPARATION']`。
- release_lifecycle: task `IGNITION-20260829-148`；content phase `RELEASE_READY`；publication authority `REMOTE_REF_OBSERVATION`；embedded publication assertion `NONE`；required ref `refs/heads/main`；post-publication verification must observe that remote ref。
- current_method: `1.4.0` Current（Iteration Method，治理点火如何改变自己）；current_operating_method: `IGNITION_OPERATING_METHOD_R1` / `1.0.0` `CURRENT`（治理 Agent 如何使用点火）；current_map: `0.16.0` Current；historical_map: `0.14.0` Historical。
- current_state_status: `CURRENT_WITH_OPEN_OBLIGATIONS`；EPISTEMICALLY_ACCEPTED=0；epistemic_acceptance: `0`；live_external_ceiling: `LIVE_EXTERNAL_PROCESS_OBSERVED_NO_VALIDATED_COMPLETION`；live dimensions: dispatch `OBSERVED`, process `OBSERVED`, inference `NOT_OBSERVED`, validated completion `NOT_VALIDATED`, reconciliation blocker `NONE`。
- live_attempt_projection: total `6`；validated `0`；unreconciled `0`；observation-incomplete `2`；obligation `OPEN`；next action `OWNER_DEFERRED_REQUIRES_EXPLICIT_REOPEN_AND_LOCAL_ENVIRONMENT_PREPARATION`；source `ignition/data/operations/iterations/141/live-current-projection-r3.json`。
- architecture_counts: `registry=100; visible_nodes=87; visible_edges=92`；active_overlays: `Formal Task Lifecycle, Open Obligation Registry, Executor Admission, Durability / Lifecycle, Steering / Intent / Goal / Obligation, Structural Governance Surface`。
- task_lineage: current `IGNITION-20260829-148` `COMPLETED_WITH_OPEN_OBLIGATIONS`；predecessor `HISTORICAL_UNEXECUTED_REBASED_INTO_127` / `REBASED_INTO_127`；successor `COMPLETED_WITH_CLASSIFIED_RESIDUALS`。
- source: ignition/data/operations/current-snapshot-r1.json；source_digest: `59618581091196aa4dff2c385961d5bfb5122aa4d5164e6bcd885548878fc495`。
- claim_ceiling: Deterministic repository-local Current projection only; no Owner authority, external truth, production readiness or epistemic upgrade.
<!-- CURRENT-SNAPSHOT:END -->

当前工程阶段已按既定范围关闭：架构身份保持冻结，外部 Agent qualification 保持
`OWNER_DEFERRED`，不再自动恢复工程优化或 live 工作。既有成果册中的文章、Book Project
和样章保留为 capability smoke-test outputs，等待 Owner review；正式文章/书籍生产必须从
Owner production brief 开始。当前收口只处理 Current、入口、registry 与发布门禁的一致性，
已完成且不新增 Agent 能力，也不把仓库内生产证据解释成 Owner acceptance、外部出版或认识论接受。

## 当前形态

点火当前是一个仓库原生、版本化、可审计、可恢复的跨领域研究与行动 Agent
Platform 原型。它负责长期状态、价值边界、目标与任务、权限、记忆、验证、
provenance、handoff 和结果吸收；它是 OS / orchestration-governance layer，
也是动作与外部 executor 的司机。OpenClaw、Hermes、Codex 是可替换执行器，
不是点火的替代系统；现有自研执行层冻结为
`REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL`。
Knowledge 是第一个大型 Domain Pack，不是整个系统本体；Research、Writing、
Maintenance 也各自受 manifest、schema、validator 和 authority ceiling 约束。
当前地图、身份、任务和状态的易变值由下方 Current Snapshot 统一投影；本段只解释稳定的
架构边界：中央 OS 控制脊柱、外部 Federation/replaceable executors 与 Domain/Skill Packs 分开。
Structural Governance Surface 作为 advisory cross-cutting overlay 单独登记，
只提供阅读/实验上下文，不增加 L7，不改变 capability、permission 或 epistemic status。
历史 Task 127 将 Durability / Lifecycle R3 登记为同一 OS 控制脊柱内的当前构件：它保存
snapshot、migration、namespace、Pack lifecycle、revocation、accounting、recovery
和 DR continuity；不建立第二张系统图，不把不确定外部 dispatch 自动重放为 completion。
版本、计数和 live ceiling 以 generated Current Snapshot、[Current Facts](./architecture/current-facts.md)
及其 JSON 投影为准，不在本段复制第二份值。

当前任务链由 [`current-task-lineage-status.json`](../data/operations/current-task-lineage-status.json)
统一表达；历史任务、requirements lineage、terminal status 和当前架构变更任务由 generated
Current Snapshot 投影。历史/环境 residual 仍按 receipt 保留，旧任务记录不会被重写为当前事实。

任务身份分成两个稳定可读的角色：Current formal task 回答“最近哪一轮正式任务正在或刚刚成为 Current”；latest architecture-changing task 回答“最近哪一轮改变了系统身份或架构”。二者允许不同，release-governance task 不会因为成为 formal task 就自动获得 architecture authority。工程阶段收口后，默认下一步是等待 Owner production brief，而不是自动创建新的工程任务或正文。

Steering 以 `OWNER_DECLARED`／`OWNER_APPROVED_DERIVED` 与 `SYSTEM_DERIVED_PROPOSAL` 分离
权威来源；Goal completion 需要独立 Completion Contract，`PASS` Run 不得推断完成。

历史 Task 124 的 [OS Control Plane R2](./architecture/os-control-plane-r2.md) 补上了
Event Ledger、monotonic policy compiler、resource arbitration、bounded concurrent
scheduler、executor health lease、queue/backpressure、durable dispatch/reconciliation、
concurrent operational memory 和 Driver Console。五子任务 disposable offline pilot
实际观察到最大并发 `2`，并覆盖资源冲突、stale executor、checkpoint/resume、取消、
deadline、伪造 completion receipt 和 stale memory capsule；这些是仓库内协调证据，
不是 live executor、生产安全、现实因果或外部有效性证据。

Durability / Lifecycle R3 在同一离线连续性 pilot 中覆盖 snapshot plus tail、schema
migration、namespace isolation、Pack pin/rollback、revocation、accounting、fault
recovery、DR fresh restore 和 external re-execution forbidden；这些是 repository-local
recovery evidence，不是 production durability、exact-once delivery、Owner acceptance
或 epistemic acceptance。

当前工程状态与 epistemic ceiling 由 generated Current Snapshot 投影；它们描述仓库接口，
不是产品成熟度、市场唯一性、AGI、生产安全、现实因果、外部有效性或 Owner acceptance 证明。

## 当前已实现能力

- 由 Kernel、Runtime、Supervisor、Operational Memory、Profile、Reasoner Gateway、Federation 和四个 Domain Pack 形成有界的仓库内协同骨架；Reasoner 提议，Profile 收窄，Pack 按声明范围验证，执行器在权限交集内行动。
- 从 canonical registries 保留来源、命题、形式对象、论证、证据、证明义务、反例、验证、迁移和人类结果的独立谱系；工程闭合不升级内容真值。
- 通过 `current-facts.json` 确定性投影同步可复算事实；本页不手抄第二份数量表。[Current Facts](../data/architecture/current-facts.json) 与[人读 facts block](./architecture/current-facts.md) 是窄范围派生入口。
- 以唯一 registry/topology/layout 生成系统图；图是仓库结构与依赖投影，SVG 中的 href 只表示 source link metadata，不是现实因果图、严格同构或完备性证明。
- 历史 Task 126 的 Structural Governance Surface 由候选 ESI、过渡语法、不越权合同和软上下文暴露合同共同限定；它是 advisory，不是权限、真值、Owner 或安全放行层。
- 控制平面把事件、权限收窄、共享资源、并发 ready-set、健康租约、队列、外部回执和操作记忆分别持久化；Driver Console 只投影下一步与开放义务，不成为第二真相源。
- Steering / Intent / Goal / Obligation R1 已形成仓库本地可复算骨架：Intent Registry、Goal lifecycle、独立 Completion Contract、Commitment/Obligation Ledger、时间语义、长期 Goal graph、优先级与 conflict arbitration、DecisionTrace/why-next、Episode binding、drift/handoff guard、Memory/Profile boundary、Durability、namespace/delegation 与 federation Intent Capsule；这些记录不授予 Owner authority，也不把运行通过推断为完成。
- R2/Federation conformance 仍以 disposable local fixture 为主；Task 139 延续 Task 136–138 的 live completion obligation，建立 host-side durable capture、append-only LiveAttemptLedger 和 ledger-derived Current projection。历史 ledger 共记录四次尝试，其中 Hermes136 与 Codex138 second 仍待 reconciliation；Codex138 second 确实发生，但 outer context overflow 使 observation incomplete，return code、structured result、lease、workspace 和 validator input 未恢复。当前 live provider/inference ceiling 仍未建立。

## 当前限制与开放义务

- 当前 closure summaries 的数量、quarantine/pending 和架构计数只从 `current-facts.json` 的确定性 derived facts 读取；本页不复制第二份数字权威，历史任务数字仍只在历史语境出现。
- live provider/inference、daemon、多 Agent 并发、向量记忆、网络/浏览、外部 Git mutation、物理 Pack 拆分和真实外部效果仍未被本仓库证明；Step 09 的显式 skip/timeout 不能升级为 live success，后续任何 smoke 仍不能为绿灯扩大权限。
- 大量资产仍缺精确定义、类型、量纲、证明、反例、外部来源、数据或复现；MCF、PSD、ARN、Function OS 与现实使用效用仍需独立证据和失败条件。
- 四力统一、量子引力、暗物质、暗能量、宇宙常数和测量问题没有被本项目解决；任何模型失败、相似性、工程完成或 Agent 共识都不能推出普遍 no-go theorem。
- 自动审计、系统图、Pack pilot、CI、fresh clone 和 receipt 都是仓库证据；它们不等于专家裁决、同行评审、外部真值、生产安全、Owner acceptance 或 epistemic acceptance。
- ESI 仍是候选 advisory reading surface；live provider 状态、术语/风格模仿、越权失败、过度谨慎和延迟迁移仍需独立复核。Durability / Lifecycle 的 production durability、exact-once external delivery、真实外部恢复和 Owner acceptance 仍未建立。当前任务链的易变值由 canonical source 和 generated block 表达；本轮不把历史任务记录重写为当前事实。

## 历史任务上下文（可回链，不是 Current 数字权威）

## Task 112 current publication layer

任务 112 把既有百轮材料整理为可连续阅读的前台成果，而不是继续扩张模块。入口是[成果书架](../PUBLICATIONS/README.md)，其下可直接到达[一页全景](../PUBLICATIONS/what-pointfire-knows-now.md)、[完整第一卷](../PUBLICATIONS/volumes/001-pointfire-after-one-hundred-iterations.md)、[研究笔记第一辑](../PUBLICATIONS/notes/001-pointfire-research-notes.md)和[百轮成果台账](../PUBLICATIONS/hundred-iteration-achievement-ledger.md)。出版层明确区分研究成果、纠正成果、有限实验、形式化、方法、基础设施、维护和开放问题，不把记录数或文件数当作知识总量。

任务 112 的正式证据与来源包位于 `data/operations/iterations/112/publication/`：其中保存 R0 不可变 intake、覆盖/主张/笔记独立性/读者审计、修订决定、三重出版审查、manifest 和未解决义务。R0 以固定基线保存；任务 111 的正式 `TERMINAL_SUCCESS` recovery-1 状态单独作为项目生命周期事实，不能被写成新的科学发现。仓库 Markdown 仍是持续维护的人类阅读层；本出版层没有复活已退出的独立阅读站。

## Task 113—114 current language and publication addition

任务 113 发布了[《当天意有了接口：宋徽宗与会自我证明的皇权》](./publication/works/when-an-emperor-manufactures-heaven.md)，并以历史／来源、反方／解释和编辑／文学三重审查守住私人信仰、唯一因果、宗教疗效和后见之明边界。任务 114 不改写其终态或历史接受哈希，而把当前文本登记为一个新 revision。

任务 114 的[语言—思维逻辑平面](./architecture/language-thought-logic-plane.md)横穿 L0—L6：十二维有限基底服务来源保存、命题框架、对象／事件包装、篇章连接、机制视角、跨语言验证和目标语言实现。现代普通话书面中文与当代标准书面英语为完整配置；日语与土耳其语为不能独立批准出版的有界试点。研究同时保留正效应、空效应和混合结果，不采用强语言决定论，也不增加 L7。

之元写作法 `0.5.0` 是当前 L6 使用者，`0.4.0`、`0.3.0` 为历史已合并版本。两个当前作品均由任务 114 冻结旧 SHA-256、执行全篇语言审计、四类角色复核和实质修订；机器 registry 分开保存历史接受哈希与当前修订哈希。自动 validator 只证明结构化框架差异账本一致，不证明人类级语言理解或文学质量。

## Task 119 current agentization boundary

任务 119 在 118 的正式基线 `4f4358ef09d1871a48d7e32575a63453130b333c` 之上建立 `Agentization Boundary R0`。新增的 Generic Kernel 只承载身份、状态、来源引用、capability、授权、审计、checkpoint、handoff、resume lineage、结构化记忆事件和不变量；Agent Runtime 只编排 `Observe → Frame → Plan → Authorize → Act → Validate → Remember → Continue/Stop`。Kernel 不导入 Foundation、claims、Evidence、Functions、Non-Functions、Results、Knowledge、REOS 或 writing；Runtime 不要求 provider、model、网络或常驻 daemon。

现有知识治理系统被登记为第一个 `Knowledge Domain Pack`，REOS vNext LIGHT 与之元写作法分别作为有界 research/writing Pack 引用；R0 没有全仓物理迁移。机器边界以 [`agentization-boundary-r0.json`](../data/architecture/agentization-boundary-r0.json)、`DomainPackManifest`、Agent Profile 和当时的唯一系统图 `0.6.0` 为准；后续 `0.7.0`、`0.8.0` 均是后续历史/当前投影。非知识 pilot 只读取两个 fixture 文本、生成排序 SHA-256 manifest，在不同 executor 间 checkpoint/resume，并在 validator 通过后进入 `COMPLETED_VALIDATED`；它是仓库范围隔离证据，不是 AGI、长期自主性或知识真值证据。

Task 119 保持 `CURRENT_WITH_OPEN_OBLIGATIONS`：Task 115 Draft prior art 仅完成采纳审计，真实 provider/API、daemon、多 agent scheduler、向量记忆、Pack 物理拆分和外部 Owner acceptance 均未实现或未证明。

## Task 121 current Agent Platform R2 spine

任务 121 在 R0/R1 边界上完成了仓库内 Agent Platform R2 的主要工程连接：
Pack Registry/Bus、四个声明式 Domain Pack、跨运行非向量 operational memory、
Supervisor multi-Run DAG、Profile narrowing、Reasoner Gateway、Pack-aware
routing、source-driven propagation blast-radius，以及一个真实离线的 fresh-clone
`audit → repair → validate` episode。机器入口是
[`Agent Platform R2 架构`](./architecture/agent-platform-r2.md)、
[`夜班 ledger`](../data/operations/iterations/121/nightshift-progress.jsonl)、
[`Agentization boundary`](../data/architecture/agentization-boundary-r0.json)和
[R2 pilot receipt](../data/agent-runtime/pilots/r2-offline-repository-maintenance/pilot-receipt.json)。

这使点火的工程主干可以被准确地描述为：**一个有界、可审计、可恢复的 Agent
Platform 原型；知识治理是第一个大型 Domain Pack，而不是整个系统本体。**
Reasoner 只提出 proposal，Profile 只能收窄，Pack 不能获得 truth/Owner/generic
permission，Memory 不是 Knowledge truth registry，Supervisor 不能扩大 child
scope。R2 pilot 的 `COMPLETED_VALIDATED` 和对抗 episode 的独立失败只表示这组
仓库合同在 disposable offline fixture 上被观察到，不表示通用智能、长期自主性、
生产安全、现实世界普适性、外部有效性或 `EPISTEMICALLY_ACCEPTED`。

R2 仍保留开放义务：live provider/API、daemon、并发 multi-Agent 调度、向量记忆、
网络/浏览、外部 Git mutation、物理 Pack 拆分、真实 Owner acceptance 和现实效果
尚未实现或证明。R2 的工程完成不得覆盖 Foundation、M/E、claim ceiling、九状态
轴、既有研究结果或之元写作法的独立来源边界。

## Task 122 current External Agent Federation R1 projection

任务 122 在 R2 之下建立点火 OS 与可替换 executor 之间的 provider-neutral
contract：它保留目标、policy、approval、workspace、capability/health/
privacy/granularity 路由、handoff/failover、独立 validation、receipt 和
pointer-only operational memory。OpenClaw、Hermes、Codex 只作为 adapter family
接入；现有自研 action plane 冻结为 `REFERENCE_EXECUTOR /
CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL`，未来 executor 只能先满足同一
contract 才能进入候选槽位。

Step 10 的 Pilot A/B/C 只在 disposable local fixture 上比较 protocol
compatibility，live external invocation 保持 `NOT_RUN_LIVE_EXTERNAL_INVOCATION`。
外部 session、vendor telemetry、prompt、token、secret、hidden reasoning 和
channel 状态不进入 Knowledge、Writing、Human Surface 或 canonical memory。
传播契约将 `agent_federation/` 单独投影到 `agent_platform.federation`，并禁止
它直接生成 Knowledge census、Fire Seeds、publication、Human front-door 或
Pack registry；若要改变这些表面，仍须由各自 canonical source 独立声明与验证。

## Task 136 current Live External Executor Bridge R1

Task 136 将 Federation contract 落到 OS-owned 的 bounded live bridge：由
LiveDispatchEnvelope、LiveCapabilityLease、受限 transport、严格 receipt、
独立 fixture validation、timeout/cancel 与 conservative reconciliation
组成。pilot 仍严格是 synthetic、disposable、read-only；不启用 message/channel、
browser、remote Git、executor configuration 或 new billing。

Step 13 只做了一次 Hermes bounded attempt，结果为 TIMED_OUT_EFFECT_UNKNOWN，
cancel 与 reconciliation 保持 OPEN，fixture 未变更且没有 retry。OpenClaw 因
无法证明 disposable workspace、显式 read-only ceiling 与 channel-off 边界而
未调用。当前 live bridge 状态精确为
LIVE_BRIDGE_IMPLEMENTED / LIVE_COMPLETION_NOT_OBSERVED，LIVE_EXTERNAL_INVOCATION
仍是开放义务；任何 executor PASS 都必须先经独立 OS validator。

## Task 137 validated live completion and reconciliation continuation

Task 137 没有新增持久核心组件、typed topology relation 或地图版本；因此 identity
epoch、latest architecture-changing task=Task 136 和 map `0.13.0` 保持不变。它把正式任务
推进到 137，并把失败边界写成可审计的 Current 事实：Task 136 Hermes timeout 因旧 receipt
缺少 attempt PID/PGID 和持久 disposable workspace 绑定，历史 effect 仍不能被证明为 absent，
所以 reconciliation 继续 OPEN；OpenClaw 仍因 workspace/channel 边界不安全而跳过。

重新观察到的 Codex CLI 为 `codex-cli 0.144.4`，获得新的 bounded read-only capability
lease 后只进行了一次 synthetic/read-only dispatch。进程在启动 helper 阶段因 read-only HOME
权限失败，退出码为 1、没有 exact public JSON result；fixture workspace digest 前后一致、
process group 已确认退出、formal worktree 未变更。Pointfire 因而没有进入 independent validation，
更没有写入 `COMPLETED_VALIDATED`。`LIVE_EXTERNAL_INVOCATION`、`CURRENT_WITH_OPEN_OBLIGATIONS`
和 `EPISTEMICALLY_ACCEPTED=0` 都保持原状；不得把本次失败过程解释成成功、Goal completion、
production readiness、Owner acceptance 或外部真值。

## Task 138 executor runtime scratch separation continuation

Task 138 没有新增持久核心组件、typed topology relation 或地图版本；因此 identity
epoch、latest architecture-changing task=Task 136 和 map `0.13.0` 保持不变。它把
task workspace、executor runtime scratch 与 auth/config source 分成三个独立域：任务工作区
仍为 disposable read-only，runtime scratch 只允许 attempt-specific 的短命最小可写，已有
登录状态只能作为 read-only reference，不能复制 secret、修改真实 config 或 billing。

第一次修复后的真实 Codex dispatch 在启动阶段 failed closed，没有 structured public result；
process group 已确认退出，fixture workspace digest 前后一致，runtime scratch 已清理，因而
没有进入 independent validation。第二次调用没有被盲目重试：public CLI 的 auth/config 边界
不能在不暴露真实登录域的前提下证明合规的 read-only reference，因此按硬门禁禁止。Hermes
reconciliation、`LIVE_EXTERNAL_INVOCATION`、`CURRENT_WITH_OPEN_OBLIGATIONS` 和
`EPISTEMICALLY_ACCEPTED=0` 都保持原状；这不是 validated live completion、production
readiness、Owner acceptance 或外部真值。

## 历史快照（Historical, append-only context）

## 当前形态

点火是一个仓库原生、版本化、证据可追溯、对象有类型、推断可检查、结论可降级的跨领域研究与行动基础设施原型。这个描述只绑定当前提交，不是永久项目身份。

现行组织包括 L0—L6 架构、横穿其间的语言—思维逻辑平面、Agent Platform R2 工程脊柱、External Agent Federation R1、Foundation registries、Function OS 候选、MCF、PSD、ARN、效果与机制平面、注意力/分布/压缩控制、地图集、迭代与同步系统、生命共同体价值宪章、Charter System R1、之元写作法和现实反馈入口。

## 当前已实现能力

- 保存来源、命题、形式对象、论证、证据、证明义务、反例、验证和迁移历史。
- 对任务 102 排除生成投影回灌后重算的 function identity cards 建立 identity card、M/E 双轴、义务、依赖、处置与 quarantine；当前可复算数量见 current-facts projection（`5,603`）。
- 对同次重算的 non-function claims 建立类别、来源、证据谱系、十三道门禁、依赖、M/E、处置与公开表述上限；当前可复算数量见 current-facts projection（`15,899`）。
- 自动发现本轮知识资产变化并生成 Claim Delta、影响分析、证据谱系变化、审计发现和整改计划。
- 检测证明/实证义务、跨域越界、量词膨胀、循环论证、类比冒充同构、单模型失败推出普遍不可能和撤回结论回弹。
- 检查机器记录与人类结果成对存在、`.github/README.md` 两次点击可达、重要内容不被默认折叠、当前状态不残留退役阅读面。
- 通过 Git 历史、supersession lineage 与追加式历史记录保留撤回、降级、隔离和修订过程。
- 对语言敏感转换保存来源／候选意义／目标形式、十二维框架差异、未映射残余和 claim ceiling；认识相关静默变化失败关闭，中文自然度与文学标记性进入人工门。
- 从统一入口按时间、研究问题、自然语言词、旧称和阅读时长探索知识，不要求读者预知目录或资产编号。
- 为全部恢复的结果/文章来源生成统一卡片和 1 分钟、5 分钟、完整阅读，并为全部函数/断言 registry 建立可回链来源、状态、依赖、反向依赖和历史的分片搜索索引。
- 以 Kernel、Runtime、Federation、Profile、Gateway、Supervisor、Memory 和声明式 Domain Pack 形成有界 Agent Platform R2 工程脊柱；各组件的能力与禁止 authority upgrade 由 manifest/schema/validator/receipt 分开记录。

## 当前人类阅读面

GitHub 仓库 Markdown 是唯一持续维护的人类阅读层：

- [统一知识入口](../KNOWLEDGE/README.md)
- [最新变化](../KNOWLEDGE/WHATS-NEW.md)
- [知识地图](../KNOWLEDGE/MAP.md)
- [搜索与交叉引用](../KNOWLEDGE/SEARCH.md)
- [统一资产卡](../KNOWLEDGE/ASSET-CARDS.md)
- [分层阅读](../KNOWLEDGE/READING-LAYERS.md)
- [README](../../.github/README.md)
- [人类阅读总入口](../HUMAN-READING.md)
- [RESULTS](../RESULTS/README.md)
- [当前结果](../RESULTS/LATEST.md)
- [纠正与撤回](../RESULTS/CORRECTIONS.md)
- [开放问题](../RESULTS/OPEN-QUESTIONS.md)
- [裁决总结](../RESULTS/ADJUDICATION-SUMMARY.md)
- [研究与文章](../RESULTS/RESEARCH-AND-ARTICLES.md)

此前独立部署的阅读站已退出产品与同步面，独有系统图迁移到 [仓库内唯一完整 SVG](./generated/ignition-system-architecture.svg)。历史部署证据仍留在 Git 与旧报告，不再构成当前完成门禁。

## 当前治理结论

- registry closure 表示每项有处置或明确 quarantine，不表示全部命题成立。
- 数学成熟度和外部证据成熟度独立；任何一轴不能替代另一轴。
- 自动提取、分类、依赖计算和 CI 只提供仓库范围证据，不裁决外部现实。
- 当前门控乘积模型没有统一四种基本相互作用；物理统一问题保持开放。
- 点火没有证明“大一统普遍不可能”。模型失败、哥德尔类比、跨域相似或旧编号不能充当普遍 no-go theorem。
- 系统图和传播闭包是导航/仓库关系，不是现实因果、严格同构或项目完备性证明。
- 语言配置只描述有边界的语法义务、语篇倾向和允许空间；它不代表每位使用者、民族或文明，也不改变真值逻辑。
- 生命共同体价值宪章是规范边界，不是事实、数学或授权证据。

## AI 状态恢复与断言非晋级不变量

新 Agent 先读 [STATE-CHANGELOG.md](../STATE-CHANGELOG.md) 的 baseline 与最近 delta，再回到本页、`ITERATION.md`、Foundation、claim/evidence registry 和任务权威资产。状态日志记录相对于上一正式 `main` 的增量，不替代当前状态、registry、Results Book 或任何原始来源；每次正式迭代合并 `main` 必须在同一轮追加一条结构可验证的 delta。

认识论治理内核的 `K13_ASSERTION_NON_ESCALATION`（[正式定义](./architecture/epistemic-governance-kernel-and-federated-planes.md#k13_assertion_non-escalation--assertion_inflation_guard)）把 Claim Ceiling、九状态轴独立、M/E 正交、回弹阻断和 provenance/adjudication/validation 组合为仓库级不变量：知识可以增长，但工程完成、写作完成、跨域呼应、模型美感、重复引用或 Agent 共识不能自动抬升断言地位。长期风险“从自我克制滑向大断言”保持为开放治理义务。

## 当前限制与开放义务

- 函数资产中 `4,804` 项仍 quarantine/pending；非函数断言中 `4,615` 项仍 quarantine/pending；数字来自 current-facts projection，不能解释为内容验证完成。
- 大量资产仍缺精确定义、类型、量纲、证明、反例、外部来源、数据或复现。
- MCF、PSD、ARN、Function OS 与现实使用效用尚需独立证据和失败条件。
- 四力统一、量子引力、暗物质、暗能量、宇宙常数和测量问题没有被本项目解决。
- 自动审计是启发式门禁；它可以发现风险和阻断已知回弹，但不能替代专家裁决、同行评审或实验。
- 日语与土耳其语仍是 preliminary profile；相应语言正式出版需要母语和语言特定来源复核。韵律、自然度、复杂指称和文学收益仍不能自动裁定。
- 主题分类、重要性规则和自动摘要只建立导航；machine-only 不表示资产不重要、错误或已被删除。

## Task 110 current-state addition

任务 110 将 planner 的完成状态与 Evidence Program 生命周期连接起来：任务 109 的
原始 C-01 推荐被保留为历史缺陷，C-01/task 103 与 C-04/task 105 被登记为已完成并从
active queue 排除；同一冻结评分模型的 task-110 projection 保留 C-03 作为已执行的
OpenAlex 独立元数据复制。首轮主分母为 116：101 supported、8 partial、7 null、0
contradicted、0 invalid。

当前结论的上限仍是跨源书目元数据一致性。OpenAlex 结果不验证论文内容、科学真理、
Pointfire 物理、MCF、PSD、ARN、现实因果或任何成熟度/处置提升。生命周期事实由候选
事件、内容合并、终端化投影、annotated tag 和全新克隆 resolver 分层确认；不以旧候选
标签自动生成下一任务。

## Task 111 current-state addition

任务 111 对 `case_failures/` 的三项原始 `IMPLEMENTATION_DEFECT` 分类做证据门禁，而不把
目录存在或“系统可能会输出”当作缺陷复现。苹果案例经 Stukeley、Conduitt 和 Newton
Project 材料复核，外部证据仅为 `EVIDENCE_PARTIAL_OR_DISPUTED`；Function OS v0.1/v0.2
没有该历史因果命题的可执行接口，故 target 为 `EXECUTABLE_TARGET_ABSENT`、形式化为
`FORMALIZATION_UNDERSPECIFIED`、复现为 `NO_REPRODUCTION_POSSIBLE_WITH_CURRENT_TARGET`。

任务 111 新增的 fail-closed gate 只接受绑定完整 repository executable commit、精确
输入/输出、trace、run、重复失败、oracle、claim ceiling、保留首次失败和 regression
guard 的 `REPRODUCED_IMPLEMENTATION_DEFECT`。三项历史案例仍可检索，但不再以已知缺陷
进入 active queue；C-03 则按 task-110 的权威 OpenAlex result 保持 `COMPLETED_PARTIAL`
并排除。该门禁提升记录资格与可复现性，不提升历史故事、点火物理或 Function OS 的外部
真理等级，不创建 task 112。

## 当前操作法

[`OPERATING-METHOD.md`](../OPERATING-METHOD.md) 是外部用户和 Agent **使用点火完成任务**的规范入口，独立身份为 `IGNITION_OPERATING_METHOD_R1 / 1.0.0`：默认 `READ_ONLY_RUN`，从 Current capability registry 解析 operation，并把仓库链接与输入对象分别约束为操作法来源和 `INPUT_OBJECT`。Iteration Method `1.4.0` 是独立的**点火如何改变自己**协议；只有当前请求明确要求修改点火自身时，Operating Method 才把任务路由为 `REPOSITORY_CHANGE_RUN` 并调用它。二者不得合并，版本与 source of truth 不得互相覆盖，也不得用 Iteration Method 代替一般任务入口。Task148 Draft 上的 `1.0.0` 仍是 Current candidate；在接受、合并与同步前不属于正式 `main` Current。

任务 101 增加机器/人类双输出；任务 102 进一步要求有意义的知识变化声明人类目的地、What's New、主题、资产卡、分层阅读（适用时）、别名/supersession、来源和双向依赖。缺失、断链、断锚、过期、隐藏、无来源摘要或回弹时，CI 失败。

候选、Ready、Accepted、Merged、Current 和 Closed 仍是不同状态。普通合并、main 验证、远端 CI 与全新克隆复验都必须分别记录；仓库没有需要继续维护的独立阅读站生产门。

## 证据程序（Task 103）

任务 103 建立了最小可用 Evidence Program 并完成首个预注册、可证伪验证试点，使重要断言开始接受外部现实检验：

- **最小基建：** `evidence-program/`（候选组合 schema、预注册 schema、来源溯源 manifest、运行 manifest、结果裁定 schema、偏差日志 schema、E 轴转移 schema + 确定性校验器 + CI 门）。每个字段/校验器都被真实试点或回归固件触发。
- **首个试点：** 用公共 Crossref REST API 独立复验 `data/external-research/104-source-registry.jsonl` 中 117 条 `crossref_verified: true` 来源的 DOI。结果 **SUPPORTED_WITHIN_SCOPE**（117/117 解析、117/117 标题匹配、117/117 年份匹配、0 撤稿；1 条注册表内部重复 DOI 判定为有意跨 gap 引用，已保留并移交 104 数据负责人）。
- **预注册先于结果：** 协议提交于 `a4d13a69…`，早于任何 Crossref 查询；校验器强制“预注册提交是结果提交的祖先、无事后阈值替换、来源溯源完整、无未登记指标”。
- **处置：** 确认 `evidence_tier_104 = METADATA_VERIFIED` 不变；RUN-1 发现的 5 条 `crossref_year` 缺口已回填/修正并复跑验证（year_match=117/117），重复 DOI 判定为有意跨 gap 引用已保留（移交 104 数据负责人）——均为同层级数据修正，非降级。备用试点（OpenAlex 跨源、案例表历史锚点）与下一试点（Function OS v0.2 正确性）已排入开放问题。

## 任务 104—105（编辑叙事层与 Function OS 有界基准）

任务 104（PR #160，已合并）建立编辑文章层与语料关系分析；任务 105（PR #161，已合并，精确 head `9d7d5ab512ffe3fd109a60ebd3d9d246b3a42d19`，普通合并 `9b5b4b9bfb243fe4cc52f7b163a9613ee6628321`）执行 Function OS v0.2 核心能力基准、对抗验证与传播。二者均已合并且人类可读对应物齐备，本段描述其 Current 接口。

- 任务 104：六篇编辑文章 + 语料关系图，作为叙事层刻意与机器注册表、人类结果层分离；本身对首页系统图为 **NO_MAP_IMPACT**（未改动 `project-components.json` / `change-propagation-topology.json` / `interactive-system-map-layout.json` 与生成器）。
- 任务 105：Function OS v0.2 基准——**原始目标** `PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES`（25 个 false_reject，源自 N2 嵌套相等提取缺陷），**修复后目标** `SUPPORTED_WITHIN_BOUNDED_DOMAIN`；有界 N2 缺陷已修复并复跑通过。
- 证据上限：有界域内可信；**不声称**完整沙箱化、生产就绪或普遍正确。原始与修复判定保持区分，不合并为单一结论。
- 任务 106（本迭代）建立了合并后真相传播基础设施：规范化 merged-iteration ledger、9 维 impact 引擎、确定性 current-truth 投影、fail-closed 验证器、编辑文章 stale/review 生命周期与系统图 impact 审计，使后续合并的当前真相可确定性传播并在矛盾时 fail closed。

## 更新规则

未来工作只要改变能力、状态、结论、纠正、开放问题、证据或公开表述，就必须同步 `.github/README.md`、`HUMAN-READING.md`、`KNOWLEDGE/`、相应 `RESULTS/` 页面、机器 Delta/impact/lineage、知识体验 manifest 和历史记录。历史证据不删除，Git 历史不改写。
