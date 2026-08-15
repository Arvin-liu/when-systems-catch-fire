# Agent Runtime R0：环境、工具与 Pack 接口

Runtime R0 是一个离线可测试的编排器。EnvironmentObservation 描述本次运行可见的环境；ActionRequest 声明所需 capability、读取、写入、命令、网络和批准；Kernel 在 Act 之前做 fail-closed 授权；Executor 只返回带 run/action/executor lineage 的 ActionObservation；Validator 只返回带 lineage 的 ValidationResult。

Runtime 不选择模型或 provider，不建立真实 API、Telegram、OpenClaw、向量数据库或常驻 daemon。外部工具接入必须通过显式 capability scope、declared output schema 和独立 validator；没有声明的读取、写入、命令、网络或预算不能因 executor 的意图而获得。

可加载的 Domain Pack 由 `DomainPackManifest` 描述。Pack 提供领域 capability、object type、validator、human/machine entry 和可选 hooks，但必须声明所需 Kernel capabilities，并禁止 lifecycle、executor selection、generic permission、checkpoint/resume、Owner acceptance 和 Kernel definition 等 authority upgrade。

R0 的 `runtime_environment` 和 `runtime_memory_loop` 是边界组件，不是知识系统的隐形入口。Memory R0 只落结构化 run event、checkpoint、capsule 与 public summary；跨 run 的领域记忆仍由 Pack 自己按其 provenance/validation 规则管理。

状态：`EXPERIMENTAL_RUNTIME_WITH_OPEN_OBLIGATIONS`。
