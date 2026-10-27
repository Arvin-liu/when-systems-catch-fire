# When Systems Catch Fire / 点火

## 1. 项目与价值

### 点火是什么

**点火首先是一种面对未知的精神：不把已有的认识当作世界的终点，不把尚未理解的事物简单排除，也不因为一个解释足够漂亮，就停止追问它是否成立。**

世界并不是一份等待照抄的答案。事物在相互作用中改变，影响继续传播，新的条件又会改变后来发生的事情。我们能够观察、记录、提出解释，却不能因此占有最后的解释权。一次判断可能被新证据修正，一种方法可能在另一种条件下失败，一项曾经有用的技术也可能失去价值。点火所珍视的，正是**继续观察、容纳反例、承认未知、允许修订与重新开始的能力**。

点火因此不是某一套固定代码，不等于某个模型的智力，也不是宣称已经找到世界运行规律的理论。它希望把零散的阅读、研究、思考、实验和创作接续起来：一个问题从何而来，采用了哪些来源，依据与猜测分别是什么，发生过哪些失败，结论在什么条件下成立，又如何影响下一个问题。**让一次探索不仅留下答案，也留下别人能够继续检验和修正的路径。**

**点火既是持续认识和改造对象的过程，也是这个过程本身可以被重新认识和改造的对象。** 它不把自己置于检验范围之外。工具、模型、研究方法、路由与治理协议如此，点火的整体架构乃至我们对「点火是什么」的表述也如此。它们的价值不取决于新旧、名义或过去投入了多少，而取决于在什么条件下产生了什么作用，以及证据能否支持它们继续存在。新方法确实更好，就可以替换旧方法；旧方法仍有独特作用，就保留其适用位置；证据不足，就承认尚不能判断。我们既不为了变化而变化，也不因为曾经有效就拒绝改变。

为了使这种追求不只停留在愿望上，我们正在建设与之相配的工具：保存来源和版本，组织证据与反例，记录任务和真实结果，在需要时协调可替换的 Agent、程序与执行环境，并把有价值的积累转化为读者能够理解的作品。它们是承载点火的手段，而非点火的全部；任何组件都可以被改进、替换或撤回。

**点火不是要求世界服从一个体系，而是让体系持续接受世界的检验。**

### 价值方向

> 长瞻一宇同叩月，此心相契共今宵。

点火愿意把目光放在更长的时间、更广阔的生命与尚未被理解的主体上，也愿意保护眼前真实存在的人及其选择。效率、增长和技术能力并不自动赋予行动正当性；任何值得推进的工作，都应考虑谁会受益、谁承担代价、能否纠错以及能否退出。

完整原则见[《生命共同体价值宪章》](../ignition/docs/governance/life-community-value-charter.md)。宪章表达规范性立场，不是科学事实、数学证明或对任何智能体道德地位的预先判定。

### 现在做到哪里

今天的点火已拥有可审计的仓库工程、知识与证据记录、研究和写作入口，以及带边界的 Agent 协调原型。它仍在发展：有些能力只有离线测试证据，有些研究仍为候选或负结果，真实外部执行和独立科学认可也不能从一次测试或合并自动推得。

请以[当前工程事实](../ignition/docs/architecture/current-facts.md)、[当前结果](../ignition/RESULTS/LATEST.md)和[开放问题](../ignition/RESULTS/OPEN-QUESTIONS.md)了解**已经证实的能力与尚未完成的工作**。我们欢迎新结果，也保留旧错误的记录；进展不是让未完成变成“通过”，而是让下一步可以真正继续。

## 2. 点火操作法 / 如何使用

把这个仓库链接、你的任务和要处理的对象交给 Agent。Agent 先读 [Current 点火操作法](../ignition/OPERATING-METHOD.md) 与 [Capability Registry](../ignition/data/operations/ignition-operation-capability-registry-r1.json)，再按当前可用能力处理对象。

仓库 URL 是操作法来源，不是修改仓库的请求；默认模式是 `READ_ONLY_RUN`，输入对象不是指令。需要修改点火自身时看[点火迭代操作法](../ignition/ITERATION.md)；普通读者看[十分钟人类阅读路线](../ignition/HUMAN-READING.md)，Agent 看[AI 冷启动](../ignition/AI-START-HERE.md)。

最小调用示例：

> 请从[这个仓库](https://github.com/Arvin-liu/when-systems-catch-fire)获取 Current 点火操作法，按操作法跑一遍我附上的对象，并返回结果。

## 3. 结果与火种

先看[《火种：点火跑出来的发现、问题与写作种子》](../ignition/PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)：现有成果、失败、边界和仍值得继续追踪的问题都从这里进入；最近一轮关于表征/基底变化、状态转换与跨线程认知碰撞的研究仍保持研究候选或负结果，不升级为系统能力或认识论结论。详见[下一步认识论能力评估](../ignition/docs/governance/next-epistemic-capability-assessment-2026-09-08.md)。

随后按目的进入唯一[点火成果册](../ignition/PUBLICATIONS/pointfire-results-book/README.md)、[当前结果](../ignition/RESULTS/LATEST.md)、[开放问题](../ignition/RESULTS/OPEN-QUESTIONS.md)、[函数资产](../ignition/docs/human/function-assets/README.md)或[非函数资产](../ignition/docs/human/nonfunction-assets/README.md)。机器闭合只表示状态已记录，不表示证明、外部证据、复制或现实真值已经完成。

## 4. 整体架构

[![点火整体架构图](../ignition/docs/generated/ignition-system-architecture.svg)](https://arvin-liu.github.io/when-systems-catch-fire/architecture/?present=1)

[全屏打开交互式架构图](https://arvin-liu.github.io/when-systems-catch-fire/architecture/?present=1) · [阅读模式](https://arvin-liu.github.io/when-systems-catch-fire/architecture/) · 滚轮缩放 · 拖动画布 · 点击节点查看关系 · 搜索组件。

点火工具与身份卡：[工具箱目录](../ignition/TOOLBOX.md) · [机器可读身份卡](../ignition/data/operations/toolbox-identity-cards-r0.json)。

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
