# Knowledge Domain Pack R0 / R2 boundary

这是第一个 Domain Pack，不是 Generic Kernel 的内容。它把现有知识治理系统的 Foundation、claims、formal/evidence/proof/scope/provenance、M/E、function/non-function、Knowledge Experience、Results 和 epistemic correction 作为可加载的领域对象与验证入口。

Pack 不拥有 Agent lifecycle、executor 选择、generic permission、checkpoint/resume、Owner acceptance 或 Kernel definition。知识 Pack 的 claim ceiling、K13 assertion non-escalation、provenance 和结果状态继续由原有知识治理资产约束；Runtime 只负责调用已声明 capability 并保存结构化运行结果。

在 Agent Platform R2 中，Knowledge Pack 通过 `manifest.json` 声明能力、对象
类型、validator 和 source admission 边界；Runtime/Pack Bus 只调用声明的
capability 并保留 declared-scope receipt。Knowledge 仍是第一个大型 Domain
Pack，但不是 Kernel、Supervisor 或 Memory 的所有者。

机器入口见 [`manifest.json`](./manifest.json) 与
[`Knowledge Corpus Admission Policy`](../../data/foundation/knowledge-corpus-admission-policy.json)。
R0/R2 都不移动既有知识目录；平台代码、测试、schema、tooling 和 pilot trace
默认是 platform provenance，不会因为存在于仓库而自动成为 Knowledge 资产。
External Agent Federation 的 adapter、session、vendor telemetry、prompt、token
和 receipt 也保持 platform/operational provenance；它们不会自动进入 Knowledge
admission、Experience、Fire Seeds 或 claim registry。
