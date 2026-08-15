# Ignition Generic Kernel R0

这是点火的领域无关内核契约层。它只负责稳定身份、运行状态、来源引用、能力范围、动作授权、审计事件、checkpoint、handoff、resume lineage、结构化记忆事件和不变量判断。

Kernel R0 不读取或导入 Foundation、claims、Evidence、Functions、Non-Functions、Results、Knowledge、REOS 或写作系统；它不拥有知识真值、Owner acceptance、领域结论、执行器选择或模型/provider 选择。`KERNEL_NON_ESCALATION` 阻止生命周期、executor 选择、generic permission、checkpoint/resume、Owner acceptance 和 Kernel definition 的 authority upgrade。未知 capability、越界路径、未声明网络和未获人类批准的动作均 fail closed。

`contracts.py` 是机器可用的最小契约，`profile.py` 是 provider-neutral Agent Profile，`domain_pack.py` 只定义可加载 Pack 的边界。它们不保存隐藏思维过程；只保留可复核的公共摘要和结构化运行事件。

状态：`CURRENT_BOUNDED_R0`。这不是完整自治系统，也不构成 AGI、人格或意识声明。

在 Agent Platform R2 中，Kernel 仍是最小、领域无关的契约层：Pack Registry、
Reasoner Gateway、Operational Memory 和 Supervisor 都消费 Kernel contract，
但不能把 Knowledge、Research、Writing、Owner 或远程仓库 authority 反向写入
Kernel。R2 的扩展仍受 `KERNEL_NON_ESCALATION` 约束；详见
[`Agent Platform R2`](../docs/architecture/agent-platform-r2.md)。
