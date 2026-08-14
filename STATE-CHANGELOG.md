# STATE-CHANGELOG

点火的 AI 优先项目状态增量日志。它记录相对于上一份正式 `main` 状态真正发生的变化，供新 Agent 先恢复最近状态；它不是 `README.md`、`docs/project-current-state.md`、Foundation registries 或 Results Book 的第二真相源。

## 读取与写入协议

- 冷启动先读 [README](./README.md)，再读本日志的 baseline 和最近几条 delta；随后回到[当前项目现状](./docs/project-current-state.md)、[迭代操作法](./ITERATION.md)和对象对应的权威 registry。
- 每次正式迭代合并 `main`，必须在同一轮追加一条 delta；旧条目 append-only，不改写成“现在看来”的新状态。
- 每条 delta 至少保留：日期/任务、对应的 main 状态与基线 tip、真实 delta、权威资产变化、claim/evidence/proof/scope/provenance 变化、open obligations、失效认知和下一步阅读入口。
- 本日志只记录仓库状态与可审计变化；工程完成、叙事完成、CI 通过或 Agent 共识不能由此升级外部真值。

## 2026-08-15 — BASELINE-CURRENT — main@19658de18d1c22fff2265f94bcd8a08cdddc0609

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; baseline 是远端 `main` 在 `19658de18d1c22fff2265f94bcd8a08cdddc0609` 的状态。
- delta: 建立当前主线恢复基线；不重新解释历史，只把当前权威入口和已知残余钉回链接。
- authority_changes: [迭代操作法 1.4.0](./ITERATION.md)、[系统图 0.5.0](./data/architecture/interactive-system-map.json)、[Charter System R1](./docs/governance/charter-system-r1.md)、[REOS vNext LIGHT](./docs/architecture/reos-vnext-light.md)、[Evidence Program](./evidence-program/README.md)、[任务 112 成果出版层](./PUBLICATIONS/pointfire-results-book/README.md)、[之元写作法 0.5.0](./docs/publication/zhiyuan-writing-method.md)均以各自权威资产为准；[九状态轴](./ARCHITECTURE.md#七层关系)保持独立。
- epistemic_state: 当前总上限仍为 `CURRENT_WITH_OPEN_OBLIGATIONS`；M/E、claim ceiling、proof、evidence、scope、provenance 和 lifecycle 不互相代替。撤回、quarantine、pending 与开放问题继续保留。
- obligations: [开放问题](./RESULTS/OPEN-QUESTIONS.md)、[纠正与撤回](./RESULTS/CORRECTIONS.md)、Foundation 的证明/实证义务和 Results Book 的显式残余继续开放；独立 GitHub Pages 阅读面已退出维护，仓库 Markdown 与相对链接是持续维护的人类阅读层。
- stale_knowledge: `0.4.0` 系统图和 `0.4.0` 之元写作法不再是当前版本；它们是历史资产。不要把旧页面、旧摘要或外部笔记中的旧 current 标签覆盖当前 main 记录。
- next_read: 先读 [AI 冷启动](./AI-START-HERE.md)、[AI 交接](./AI-HANDOFF.md)，再按任务进入 [Foundation](./FOUNDATION.md) 或 [成果/结果层](./RESULTS/README.md)。

## 2026-08-15 — STATE-CHANGELOG-ASSERTION-INFLATION-GUARD — main transition from 19658de18d1c22fff2265f94bcd8a08cdddc0609

- main_state: `CURRENT_WITH_OPEN_OBLIGATIONS`; 本条是从上述 main 基线进入下一正式主线状态的第一条 delta，提交后的精确 tip 由 Git 提交回执确定。
- delta: 新增本 AI 优先状态日志；把每次正式 main 合并追加 delta 写入 Agent 冷启动、交接、迭代、版本和 GetNote 工作流；在既有认识论治理内核中纳入 `ASSERTION_INFLATION_GUARD / K13_ASSERTION_NON_ESCALATION`。
- authority_changes: [认识论治理内核](./docs/architecture/epistemic-governance-kernel-and-federated-planes.md#共享-kernel-invariants)与其[机器关系索引](./data/governance/epistemic-governance-relationships.json)新增 K13；[同步表面注册表](./data/operations/synchronization-surfaces.json)新增本日志的 canonical source 义务。
- epistemic_state: 不提升任何具体 claim 的 M/E、proof、evidence、scope、provenance、disposition 或外部真值；新增的 K13 只把已有 Claim Ceiling、九轴独立、M/E 正交、回弹阻断和 provenance/adjudication/validation 约束组合成仓库级非晋级不变量。
- obligations: 此后每次正式 main 合并必须追加一条结构完整、链接可解析的 delta；长期风险登记为“系统可能从自我克制滑向大断言”，需在研究、裁决、写作、出版和系统总结中持续检查。现有开放义务不因本轮工程完成而关闭。
- stale_knowledge: 工程、写作、成果册、跨域呼应、重复引用、模型美感、CI 通过或 Agent 共识都不是新证据；被撤回/降级/quarantine 的结论不得借改名或上层综合文档回弹。
- next_read: 读 [K13 正式定义](./docs/architecture/epistemic-governance-kernel-and-federated-planes.md#k13_assertion_non-escalation--assertion_inflation_guard)、[断言治理](./docs/foundation/claim-governance-and-function-identity.md)和[迭代操作法的 Claim Ceiling](./ITERATION.md#4-claim-ceiling)。
