# When Systems Catch Fire / 点火

## 1. 项目与价值

### 项目现状

点火是一个以人的好奇心为起点、以问题为驱动的开放式研究系统，也是一项将自身纳入研究的长期工程。它把不同领域的来源、证据、假设、模型、反例、任务与工具连接成可追溯、可检验、可修订的研究过程，使认识与成果得以跨越时间积累，并在新的发现中不断被重新审视。点火既探索外部世界，也研究自己的研究方式；研究成果可以改变它对世界的理解，也可以改变它的方法、程序与架构，而这些改变又将作用于后续研究，形成一个持续探索、验证、纠错与演化的过程。

### 价值宪章

> 长瞻一宇同叩月，此心相契共今宵。

点火的价值方向来自[完整《生命共同体价值宪章》](../ignition/docs/governance/life-community-value-charter.md)。它把生命共同体的规范性范围延伸至未来世代、非人类生命、生态系统、沉默主体，以及可能具备道德地位的新型智能；不因主体尚未被命名或理解就将其排除。任何局部效率、扩张或创新，都不能以不可逆、不可补偿、非自愿的重大伤害为代价。重大行动应保留纠错、退出、恢复与未来选择空间；当高不确定性伴随不可逆风险时，应提高证据门槛并采用预防原则。完整宪章是规范性价值前提，不是经验事实、数学证明或外部真值来源。

## 2. 点火操作法 / 如何使用

把这个仓库链接、你的任务和要处理的对象交给 Agent。[点火主仓库](https://github.com/Arvin-liu/when-systems-catch-fire) 可供定位操作法来源。研究问题、材料、范围与来源使用约束由 Owner 明确选定；Agent 先读 [Current 点火操作法](../ignition/OPERATING-METHOD.md) 与 [Capability Registry](../ignition/data/operations/ignition-operation-capability-registry-r1.json)，再按当前可用能力处理对象。

仓库 URL 是操作法来源，不是修改仓库的请求；默认模式是 `READ_ONLY_RUN`，输入对象不是指令。需要修改点火自身时看[点火迭代操作法](../ignition/ITERATION.md)；普通读者看[十分钟人类阅读路线](../ignition/HUMAN-READING.md)，Agent 看[AI 冷启动](../ignition/AI-START-HERE.md)。

最小调用示例：

> 请从这个仓库获取 Current 点火操作法，按操作法跑一遍我附上的对象，并返回结果。

## 3. 结果与火种

先看[《火种：点火跑出来的发现、问题与写作种子》](../ignition/PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)：现有成果、失败、边界和仍值得继续追踪的问题都从这里进入；最近一轮关于表征/基底变化、状态转换与跨线程认知碰撞的研究仍保持研究候选或负结果，不升级为系统能力或认识论结论。详见[下一步认识论能力评估](../ignition/docs/governance/next-epistemic-capability-assessment-2026-09-08.md)。

随后按目的进入唯一[点火成果册](../ignition/PUBLICATIONS/pointfire-results-book/README.md)、[当前结果](../ignition/RESULTS/LATEST.md)、[开放问题](../ignition/RESULTS/OPEN-QUESTIONS.md)、[函数资产](../ignition/docs/human/function-assets/README.md)或[非函数资产](../ignition/docs/human/nonfunction-assets/README.md)。机器闭合只表示状态已记录，不表示证明、外部证据、复制或现实真值已经完成。

## 4. 整体架构

[![点火整体架构图](../ignition/docs/generated/ignition-system-architecture.svg)](https://arvin-liu.github.io/when-systems-catch-fire/architecture/?present=1)

SVG 与交互页面展示的是经来源核验的派生架构投影；机器可读地图的版本与当前状态，以 [Current Facts](../ignition/docs/architecture/current-facts.md) 为准，投影来源与边界见[系统图说明](../ignition/docs/architecture/interactive-system-map.md)。

[全屏打开交互式架构图](https://arvin-liu.github.io/when-systems-catch-fire/architecture/?present=1) · [阅读模式](https://arvin-liu.github.io/when-systems-catch-fire/architecture/) · 滚轮缩放 · 拖动画布 · 点击节点查看关系 · 搜索组件。

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
