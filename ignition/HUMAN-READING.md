# 点火人类阅读路线

无需预知路径的 canonical 入口已经迁移到[点火知识入口](./KNOWLEDGE/README.md)。本页保留十分钟阅读路线；它与机器注册表并行，但不要求读者先理解 JSON、JSONL、schema 或 CI。任何机器记录都必须有可发现的人类对应物；人类摘要不得改变原记录的成熟度和断言上限。

## 当前身份一句话

点火当前主干是一个有界、可审计、可恢复的 Agent Platform 原型；知识治理是
第一个大型 Domain Pack，而不是整个系统本体。Task 122 的 External Agent
Federation R1 让 OpenClaw、Hermes、Codex 作为可替换 adapter 接入，并把现有
执行层冻结为 Reference / Conformance / Fallback。要理解这句话的工程含义，读
[Agent Platform R2](./docs/architecture/agent-platform-r2.md) 与
[External Agent Federation R1](./docs/architecture/external-agent-federation-r1.md)；要核对当前公开
结果，读[当前结果](./RESULTS/LATEST.md)。测试、pilot、图和工作流回执都不等于
通用智能、现实因果、生产安全、Owner acceptance 或 `EPISTEMICALLY_ACCEPTED`。

## 十分钟了解当前状态

1. 先读唯一[《点火成果册》](./PUBLICATIONS/pointfire-results-book/README.md)；需要百轮历史层时再读[成果书架](./PUBLICATIONS/README.md)或[一页全景](./PUBLICATIONS/what-pointfire-knows-now.md)，不需要理解内部目录就能看见全局。
2. 再读[完整第一卷](./PUBLICATIONS/volumes/001-pointfire-after-one-hundred-iterations.md)，跟随问题、发现、纠正、有限实验和未知的连续叙事。
3. 需要核对具体记录时，再从书架进入[研究笔记](./PUBLICATIONS/notes/001-pointfire-research-notes.md)和[百轮成果台账](./PUBLICATIONS/hundred-iteration-achievement-ledger.md)。
4. 从[统一知识入口](./KNOWLEDGE/README.md)选择“最近变化”“按主题探索”“搜索”或“分层阅读”。
5. 读 [当前结果](./RESULTS/LATEST.md)，先看仓库现在能支持什么。
6. 读 [纠正与撤回](./RESULTS/CORRECTIONS.md)，避免继承已经撤回的强结论。
7. 读 [开放问题](./RESULTS/OPEN-QUESTIONS.md)，区分完成的治理工作与尚未完成的科学、数学和实证工作。

8. 读 [任务 110 的独立复制结果](./evidence-program/runs/IGNITION-EVIDENCE-PILOT-R1-OPENALEX-DOI-REPLICATION-20260801/RESULT.md)，先确认 117 条完整返回、116 条主分母和 7 条 null，再读[完成状态与独立复制文章](./docs/editorial/articles/009-system-completion-state-and-independent-replication.md)。这里的“完成”是生命周期事实，不等于科学命题被证明。

9. 读 [任务 111 苹果案例证据档案](./data/operations/iterations/111/historical/EVIDENCE_DOSSIER.md) 和[文章 010](./docs/editorial/articles/010-failure-case-evidence-gate-and-apple-case-adjudication.md)，确认历史 provenance、可执行 target 和复现状态彼此分开；目录分类与“可能会输出”不能代替运行证据。

## 按目的阅读

|你的目的|先读|继续读|
|---|---|---|
|不知道名称或路径，只想探索|[知识地图](./KNOWLEDGE/MAP.md)|[最新变化](./KNOWLEDGE/WHATS-NEW.md)、[搜索](./KNOWLEDGE/SEARCH.md)|
|快速读懂一篇长文|[分层阅读](./KNOWLEDGE/READING-LAYERS.md)|对应完整来源、[统一资产卡](./KNOWLEDGE/ASSET-CARDS.md)|
|判断点火是什么、当前做到哪里|[当前结果](./RESULTS/LATEST.md)|[项目现状](./docs/project-current-state.md)、[架构](./ARCHITECTURE.md)|
|理解 Agent Platform、Federation、Pack、Memory 与 Supervisor|[Agent Platform R2](./docs/architecture/agent-platform-r2.md)|[External Agent Federation R1](./docs/architecture/external-agent-federation-r1.md)、[Runtime](./agent_runtime/README.md)、[四个 Pack](./packs/)、[离线 pilot 简报](./data/agent-runtime/pilots/r2-offline-repository-maintenance/HUMAN-REPORT.md)|
|查看历史错误怎样修正|[纠正与撤回](./RESULTS/CORRECTIONS.md)|[历史纠正日志](./docs/foundation/historical-correction-log.md)|
|查看函数、断言资产裁决|[裁决总结](./RESULTS/ADJUDICATION-SUMMARY.md)|[函数深度裁决](./docs/foundation/historical-function-deep-adjudication-20260729.md)、[非函数断言索引](./docs/foundation/nonfunction-claim-adjudication-index.md)|
|查看物理复算与边界|[物理资产纠偏](./docs/foundation/physics-asset-correction-20260729.md)|[开放问题](./RESULTS/OPEN-QUESTIONS.md)|
|阅读研究、文章和迭代成果|[研究与文章](./RESULTS/RESEARCH-AND-ARTICLES.md)|[按时间台账](./RESULTS/CHRONOLOGY.md)|
|贡献新知识资产|[贡献指南](../.github/CONTRIBUTING.md)|[未来断言准入协议](./docs/foundation/future-claim-admission-protocol.md)、[自纠错引擎](./docs/governance/self-correction-engine.md)|
|让 AI 协助阅读|[AI 助手使用参考](./docs/ai-assistant-usage-reference.md)|[AI 冷启动](./AI-START-HERE.md)、[AI 状态增量日志](./STATE-CHANGELOG.md)、[AI 交接](./AI-HANDOFF.md)|

## 结果记录怎样读

每项人类可读结果至少说明：

- 研究问题或变更问题；
- 方法或证据类别；
- 当前结论和它的最大表述边界；
- 数学成熟度与外部证据成熟度，或说明为何不适用；
- 相比上一版本发生了什么变化；
- 局限、开放义务和最终处置；
- 原始来源和机器记录入口。

自动生成的历史条目只是导航和保真摘要，不是新的裁决。发生冲突时，以原始来源、现行治理资产和明确状态字段为准。

任务 102 的资产卡、What's New、主题索引、别名和分层阅读由同一机器 manifest 生成并校验。旧称可继续搜索，但必须跳到当前 replacement 与 supersession；不得把撤回结论当作现行知识。

## 当前权威层次

1. Git 当前 `main` 的正式资产、schema、测试和状态字段；
2. 任务 98—105 的现行函数与非函数裁决、编辑叙事层与 Function OS 有界基准；
3. 知识体验层的人类结果、搜索与 Claim Delta 投影；
4. 历史报告、旧表和旧措辞，仅作为来源与变更证据。

独立 GitHub Pages 阅读站已退出维护，不再是权威或同步面。仓库 Markdown 与其中的相对链接是唯一持续维护的人类阅读层。

面向 Agent 的最近状态恢复入口是 [STATE-CHANGELOG.md](./STATE-CHANGELOG.md)；它只记录相对于上一主线状态的增量，不取代本页的人类阅读路线或任何权威资产。
