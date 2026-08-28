# When Systems Catch Fire / 点火

## 1. 项目与价值

### 项目现状

点火是一个面向长期研究、判断与创作的认知—行动工作系统。它把问题、来源、证据、模型、反例、记忆、任务、工具与公开表达组织在同一套可追溯、可修订的结构中，使跨时间、跨领域的工作能够持续积累、检验、纠错，并最终转化为文章、书籍和其他成果。它不替人决定目标，也不把模型、Agent、工程状态或写得漂亮的结论当作真理；它负责保存上下文、约束边界、协调可替换的工具与执行器，让人始终知道依据从哪里来、哪里仍然未知，以及工作如何继续。

### 价值宪章

> 长瞻一宇同叩月，此心相契共今宵。

点火的价值方向来自[完整《生命共同体价值宪章》](../ignition/docs/governance/life-community-value-charter.md)。它把生命共同体的规范性范围延伸至未来世代、非人类生命、生态系统、沉默主体，以及可能具备道德地位的新型智能；不因主体尚未被命名或理解就将其排除。任何局部效率、扩张或创新，都不能以不可逆、不可补偿、非自愿的重大伤害为代价。重大行动应保留纠错、退出、恢复与未来选择空间；当高不确定性伴随不可逆风险时，应提高证据门槛并采用预防原则。完整宪章是规范性价值前提，不是经验事实、数学证明或外部真值来源。

## 2. 如何使用

点火同时提供人类和机器两个通道：普通读者从[十分钟人类阅读路线](../ignition/HUMAN-READING.md)开始；Agent 从[AI 冷启动](../ignition/AI-START-HERE.md)开始，先读[项目状态增量日志](../ignition/STATE-CHANGELOG.md)的 baseline 与最近 delta，再回到[当前项目现状](../ignition/docs/project-current-state.md)、[迭代操作法](../ignition/ITERATION.md)和任务相关的 canonical registry。机器使用者还可读 [llms.txt](../ignition/llms.txt)；机器入口不能替代人类结果或对象权威。

执行、协作和贡献请看[使用说明](../ignition/docs/USAGE.md)、[AI 交接契约](../ignition/AI-HANDOFF.md)和[贡献指南](CONTRIBUTING.md)。探索知识时进入[统一知识入口](../ignition/KNOWLEDGE/README.md)，再按[知识地图](../ignition/KNOWLEDGE/MAP.md)、[全局搜索](../ignition/KNOWLEDGE/SEARCH.md)或[演化与旧称](../ignition/KNOWLEDGE/EVOLUTION.md)分流。仓库内相对链接是持续维护的人类公共阅读面；已退出维护的独立 GitHub Pages 不再是当前入口。

需要进入具体能力时，可从[点火迭代操作法](../ignition/ITERATION.md)、[MCF](../ignition/docs/architecture/multiscale-causal-fabric.md)、[PSD](../ignition/docs/architecture/probabilistic-system-dynamics.md)和[ARN](../ignition/docs/architecture/adaptive-relational-network.md)开始；这些都是有边界的项目构件，不是新的真值层。

## 3. 结果与火种

历史上已撤回“物理大一统普遍不可能”等越界断言；撤回、降级和开放问题继续保持可见。

先看[《火种：点火跑出来的发现、问题与写作种子》](../ignition/PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)：它把现有成果、失败、边界和仍值得继续写作/研究的问题整理成可继续追踪的人类条目，不增加外部新颖性，也不替代来源、registry、M/E、proof、evidence 或 claim ceiling。

随后按目的进入唯一[点火成果册](../ignition/PUBLICATIONS/pointfire-results-book/README.md)、[当前结果](../ignition/RESULTS/LATEST.md)、[开放问题](../ignition/RESULTS/OPEN-QUESTIONS.md)、[函数资产](../ignition/docs/human/function-assets/README.md)或[非函数资产](../ignition/docs/human/nonfunction-assets/README.md)。机器闭合摘要仍是机器记录入口；闭合只表示状态已被记录，不表示证明、外部证据、复制或现实真值已完成。

## 4. 整体架构

![点火整体架构图](../ignition/docs/generated/ignition-system-architecture.svg)

这张图展示点火的整体结构；想了解具体组件，可展开下面的组件列表。

<details>
<summary>组件导航：核心控制与状态</summary>

- [Ignition Generic Kernel R0](../ignition/agent_kernel/README.md)
- [Agent Runtime R2](../ignition/agent_runtime/README.md)
- [OS Control Plane R2](../ignition/docs/architecture/os-control-plane-r2.md)
- [Steering / Intent / Goal / Obligation R1](../ignition/docs/architecture/os-steering-intent-r1.md#os-steering-intent-and-obligation-r1)
</details>

<details>
<summary>组件导航：执行与协作</summary>

- [External Agent Federation R1](../ignition/docs/architecture/external-agent-federation-r1.md#architecture-hierarchy)
- [Executor Admission R1](../ignition/docs/architecture/external-agent-federation-r1.md#provider-neutral-executor-admission)
- [Live External Executor Bridge R1](../ignition/docs/architecture/external-agent-federation-r1.md#live-external-executor-bridge-r1)
- [Reference Executor](../ignition/docs/architecture/external-agent-federation-r1.md#reference-executor-freeze)
</details>

<details>
<summary>组件导航：研究与知识</summary>

- [统一知识入口](../ignition/KNOWLEDGE/README.md)
- [Foundation](../ignition/FOUNDATION.md)
- [MCF 多尺度因果织体](../ignition/docs/architecture/multiscale-causal-fabric.md)
- [PSD 概率系统动力学](../ignition/docs/architecture/probabilistic-system-dynamics.md)
- [ARN 自适应关系网络](../ignition/docs/architecture/adaptive-relational-network.md)
</details>

<details>
<summary>组件导航：人类入口与成果</summary>

- [人类使用说明](../ignition/docs/USAGE.md)
- [当前项目现状](../ignition/docs/project-current-state.md)
- [之元写作法 0.5.0](../ignition/docs/publication/zhiyuan-writing-method.md)
- [成果索引](../ignition/docs/publication/zhiyuan-writing-showcase.md)
</details>

<details>
<summary>组件导航：治理与边界</summary>

- [生命共同体价值宪章](../ignition/docs/governance/life-community-value-charter.md)
- [Human Surface 编辑契约](../ignition/docs/governance/human-surface-editorial-contract.md)
- [认识论治理内核与联邦平面](../ignition/docs/architecture/epistemic-governance-kernel-and-federated-planes.md)
- [智能体化边界 R0](../ignition/docs/architecture/agentization-boundary-r0.md)
- [许可与权利边界](../ignition/docs/governance/licensing-rights-inventory.md)
</details>

## 5. 致谢

感谢所有提出问题、保留反例、指出边界、维护来源、修订文字、建设工具和认真阅读的人。点火的公共价值不在于永远正确，而在于让“当前能说什么、还不能说什么、下一步如何被推翻”保持可见。

参与边界见[参与说明](../ignition/docs/participate.md)与[支持说明](SUPPORT.md)：欢迎独立审查和非商业使用，但支持、赞助或商业咨询都不能购买合并权、治理权、证据等级或结论。

许可范围以根目录 [LICENSE](../LICENSE) 与 [LICENSES/README.md](../ignition/LICENSES/README.md) 为准；历史 MIT 版本只保留为历史边界，不代表当前分发许可。
