# When Systems Catch Fire / 点火

## 1. 项目与价值

> ## 丹无定形，火有法度；炼无终局，化有来路。

点火是一个仓库原生、版本化、可审计的跨领域研究与行动基础设施原型。它把来源、命题、证据、模型、证明、反例、验证、现实反馈和公开表达分开记录，允许结论在新证据出现后被修订、降级、隔离或撤回。历史上已撤回“物理大一统普遍不可能”等越界断言；撤回、降级和开放问题继续保持可见。

> ## 长瞻一宇同叩月, 此心相契共今宵。

项目的规范性方向由[生命共同体价值宪章](../ignition/docs/governance/life-community-value-charter.md)约束；宪章是价值边界，不是经验事实、数学证明或外部真值来源。工程与 epistemic ceiling 由 generated Current Snapshot 投影；工程完成、写作完成、测试通过、重复引用、跨域对应、模型美感或 Agent 共识都不能自动抬升命题的断言地位。

### 项目现状

按现有范围，点火的工程建设阶段已经收口，架构冻结在已发布基线；外部 Agent qualification / live completion 保持 `OWNER_DEFERRED`，不会自动继续。项目已经从“建设点火”切换到“使用点火生产”。

下一步等待 Owner production brief（`AWAIT_OWNER_PRODUCTION_BRIEF`），由 Owner 决定写哪篇文章、立哪本书。Task143 产生的三篇文章、Book Project R1 和两个样章只是 production capability smoke-test outputs，仍处于 `OWNER_REVIEW_PENDING / PUBLICATION_ACCEPTANCE_NOT_GRANTED`；它们不等同于 Owner 已选题、正式立项或出版接受。工程收口不推出 production safety、外部真值、作品质量或 Owner acceptance。

本地行动层保持 Reference / Conformance / Fallback 边界；外部 executor 不拥有 OS authority，仓库投影也不升级为现实证明。
<!-- CURRENT-SNAPSHOT:BEGIN profile=human schema=current-snapshot-r1 -->
- Current Snapshot（机器生成；请勿手改）。
- current_identity_epoch: `os-control-plane-r8-task-lifecycle-decoupling-executor-admission-r1`；system_role: `Ignition OS / orchestration-governance layer`。
- current_formal_task: `IGNITION-20260828-144` (ordinal `144`)；status: `COMPLETED_WITH_OPEN_OBLIGATIONS`；terminal: `true`；latest_architecture_changing_task: `IGNITION-20260827-142` (ordinal `142`)；current_iteration_boundary: `144` is a deprecated compatibility alias of `current_formal_task_ordinal`；publication_witness_task: `IGNITION-20260828-144`。
- formal_task_terminality: authority `FORMAL_TASK_LIFECYCLE`；task `IGNITION-20260828-144` status `COMPLETED_WITH_OPEN_OBLIGATIONS`；terminal `true`；scope_complete `true`；open references `['LIVE_EXTERNAL_INVOCATION']`。
- formal_task_terminal_history: `[{"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260828-144", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260827-143", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260827-142", "terminal": true}, {"execution_status": "COMPLETED_WITH_OPEN_OBLIGATIONS", "task_id": "IGNITION-20260826-141", "terminal": true}]`；Task141 terminality remains recorded independently of the carried obligation。
- open_obligation_registry: authority `OPEN_OBLIGATION_REGISTRY`；status `OPEN` ids `['LIVE_EXTERNAL_INVOCATION']`；count `1`；next eligible action `['OWNER_DEFERRED_REQUIRES_EXPLICIT_REOPEN_AND_LOCAL_ENVIRONMENT_PREPARATION']`。
- release_lifecycle: task `IGNITION-20260828-144`；content phase `RELEASE_READY`；publication authority `REMOTE_REF_OBSERVATION`；embedded publication assertion `NONE`；required ref `refs/heads/main`；post-publication verification must observe that remote ref。
- current_method: `1.4.0` Current；current_map: `0.16.0` Current；historical_map: `0.14.0` Historical。
- current_state_status: `CURRENT_WITH_OPEN_OBLIGATIONS`；EPISTEMICALLY_ACCEPTED=0；epistemic_acceptance: `0`；live_external_ceiling: `LIVE_EXTERNAL_PROCESS_OBSERVED_NO_VALIDATED_COMPLETION`；live dimensions: dispatch `OBSERVED`, process `OBSERVED`, inference `NOT_OBSERVED`, validated completion `NOT_VALIDATED`, reconciliation blocker `NONE`。
- live_attempt_projection: total `6`；validated `0`；unreconciled `0`；observation-incomplete `2`；obligation `OPEN`；next action `OWNER_DEFERRED_REQUIRES_EXPLICIT_REOPEN_AND_LOCAL_ENVIRONMENT_PREPARATION`；source `ignition/data/operations/iterations/141/live-current-projection-r3.json`。
- architecture_counts: `registry=99; visible_nodes=87; visible_edges=92`；active_overlays: `Formal Task Lifecycle, Open Obligation Registry, Executor Admission, Durability / Lifecycle, Steering / Intent / Goal / Obligation, Structural Governance Surface`。
- task_lineage: current `IGNITION-20260828-144` `COMPLETED_WITH_OPEN_OBLIGATIONS`；predecessor `HISTORICAL_UNEXECUTED_REBASED_INTO_127` / `REBASED_INTO_127`；successor `COMPLETED_WITH_CLASSIFIED_RESIDUALS`。
- source: ignition/data/operations/current-snapshot-r1.json；source_digest: `3c3d8a7c708c6ea79b55e8a907e8011ab45f71f4c788d1e66d3c3f002c31aa10`。
- claim_ceiling: Deterministic repository-local Current projection only; no Owner authority, external truth, production readiness or epistemic upgrade.
<!-- CURRENT-SNAPSHOT:END -->

### 当前主干怎样理解

Steering / Intent / Goal / Obligation R1 记录来源权威、Goal 生命周期、独立完成契约、承诺义务、
优先级、冲突、why-next、漂移和 handoff；`PASS` Run 不能推断 Goal 完成，系统提议不能晋升为
Owner authority。Current Snapshot、Current Facts、地图和本页都是仓库本地投影，易变值只从 canonical
machine sources 生成。

当前任务链以 [`current-task-lineage-status.json`](../ignition/data/operations/current-task-lineage-status.json)
为机器权威；历史 task、requirements lineage、terminal status 和本轮 Current 语义由 generated
Current Snapshot 提供，不把历史记录重写为当前事实。

- **它说什么：** Kernel、Runtime、Federation、Profile、Reasoner Gateway、Supervisor、Event Ledger、monotonic policy、resource arbitration、bounded concurrent scheduler、executor health lease、queue/backpressure、durable dispatch/reconciliation、concurrent operational memory、Durability / Lifecycle R3、Driver Console 和四个声明式 Domain Pack 已形成一条仓库内可检查的 Agent Platform R3 结构；OpenClaw、Hermes、Codex 只通过 provider-neutral adapter boundary 接入，当前唯一完整系统图仍是 registry/topology/layout 的确定性导航投影。
- **为什么重要：** 行动、批准、恢复、记忆、Pack 路由和知识治理的职责被分开记录，Agent 可以提出和执行有界动作，但不能自行扩大权限、改写真值或替代 Owner。
- **怎样使用：** 人类先读[十分钟阅读路线](../ignition/HUMAN-READING.md)与[当前结果](../ignition/RESULTS/LATEST.md)；Agent 先读[AI 冷启动](../ignition/AI-START-HERE.md)、[状态增量日志](../ignition/STATE-CHANGELOG.md)、[R2 架构契约](../ignition/docs/architecture/agent-platform-r2.md)和[联邦契约](../ignition/docs/architecture/external-agent-federation-r1.md)。
- **它不能证明什么：** 通过测试、Pack 加载、checkpoint、pilot 或系统图，都不等于外部真值、现实因果、生产安全、Owner acceptance 或 epistemic acceptance。
- **仍然开放：** live provider/inference、daemon、向量记忆、网络/浏览、外部仓库 mutation、物理 Pack 拆分和现实世界效果仍不在本轮授权范围内；`LIVE_EXTERNAL_INVOCATION` 仍是 OPEN，历史六次 attempt、零 validated completion、零 unreconciled 和两次 observation-incomplete 保持不变。Task143 不启动 live process；外部 Agent 线只有在 Owner 明确重新开启、且本机环境先完成准备/安装/attestation 后才可恢复。当前出版生产入口见[点火成果册](../ignition/PUBLICATIONS/pointfire-results-book/README.md)，写作产物不抬升外部真值。

## 2. 如何使用

点火同时提供人类和机器两个通道：普通读者从[十分钟人类阅读路线](../ignition/HUMAN-READING.md)开始；Agent 从[AI 冷启动](../ignition/AI-START-HERE.md)开始，先读[项目状态增量日志](../ignition/STATE-CHANGELOG.md)的 baseline 与最近 delta，再回到[当前项目现状](../ignition/docs/project-current-state.md)、[迭代操作法](../ignition/ITERATION.md)和任务相关的 canonical registry。机器使用者还可读 [llms.txt](../ignition/llms.txt)；机器入口不能替代人类结果或对象权威。

执行、协作和贡献请看[使用说明](../ignition/docs/USAGE.md)、[AI 交接契约](../ignition/AI-HANDOFF.md)和[贡献指南](CONTRIBUTING.md)。探索知识时进入[统一知识入口](../ignition/KNOWLEDGE/README.md)，再按[知识地图](../ignition/KNOWLEDGE/MAP.md)、[全局搜索](../ignition/KNOWLEDGE/SEARCH.md)或[演化与旧称](../ignition/KNOWLEDGE/EVOLUTION.md)分流。仓库内相对链接是持续维护的人类公共阅读面；已退出维护的独立 GitHub Pages 不再是当前入口。

需要进入具体能力时，可从[点火迭代操作法](../ignition/ITERATION.md)、[MCF](../ignition/docs/architecture/multiscale-causal-fabric.md)、[PSD](../ignition/docs/architecture/probabilistic-system-dynamics.md)和[ARN](../ignition/docs/architecture/adaptive-relational-network.md)开始；这些都是有边界的项目构件，不是新的真值层。

## 3. 结果与火种

先看[《火种：点火跑出来的发现、问题与写作种子》](../ignition/PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)：它把现有成果、失败、边界和仍值得继续写作/研究的问题整理成可继续追踪的人类条目，不增加外部新颖性，也不替代来源、registry、M/E、proof、evidence 或 claim ceiling。

随后按目的进入唯一[点火成果册](../ignition/PUBLICATIONS/pointfire-results-book/README.md)、[当前结果](../ignition/RESULTS/LATEST.md)、[开放问题](../ignition/RESULTS/OPEN-QUESTIONS.md)、[函数资产](../ignition/docs/human/function-assets/README.md)或[非函数资产](../ignition/docs/human/nonfunction-assets/README.md)。机器闭合摘要仍是机器记录入口；闭合只表示状态已被记录，不表示证明、外部证据、复制或现实真值已完成。

## 4. 整体架构

![点火唯一完整总架构图](../ignition/docs/generated/ignition-system-architecture.svg)

[打开透明可点击完整总架构图 SVG](../ignition/docs/generated/ignition-system-architecture.svg) · [查看 Agent Platform R2 架构](../ignition/docs/architecture/agent-platform-r2.md) · [查看 Human Surface 编辑契约](../ignition/docs/governance/human-surface-editorial-contract.md) · [查看架构维护说明](../ignition/docs/architecture/interactive-system-map.md)

整体架构图是确定性导航投影：它表达仓库内的来源、状态、治理、执行、验证、人类阅读和出版之间的声明关系，不表达现实因果、严格同构、理论完备性或任何具体命题的新证据。图的 registry、topology 和 layout 仍是机器维护输入；总架构图不是新的真值层。

## 5. 致谢

感谢所有提出问题、保留反例、指出边界、维护来源、修订文字、建设工具和认真阅读的人。点火的公共价值不在于永远正确，而在于让“当前能说什么、还不能说什么、下一步如何被推翻”保持可见。

参与边界见[参与说明](../ignition/docs/participate.md)与[支持说明](SUPPORT.md)：欢迎独立审查和非商业使用，但支持、赞助或商业咨询都不能购买合并权、治理权、证据等级或结论。

许可范围以根目录 [LICENSE](../LICENSE) 与 [LICENSES/README.md](../ignition/LICENSES/README.md) 为准；历史 MIT 版本只保留为历史边界，不代表当前分发许可。
