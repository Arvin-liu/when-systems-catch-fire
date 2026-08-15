# Agent Runtime R0

Agent Runtime R0 实现最小的通用循环：

`Observe → Frame → Plan → Authorize → Act → Validate → Remember → Continue/Stop`

Runtime 只编排 typed records，不决定领域真值。Reasoner、Executor 和 Validator 是显式接口；运行时不要求模型名称、provider 名称、网络或常驻 daemon。每个动作先经过 Kernel capability scope 授权，再交给 executor；授权失败、能力未知、需要 Owner 批准或预算耗尽都会进入明确 stop state。

R0 的 stop state 至少包括 `COMPLETED_VALIDATED`、`BLOCKED_WITH_EVIDENCE`、`WAITING_FOR_APPROVAL`、`FAILED_VALIDATION`、`ABORTED_BY_OWNER`、`CAPABILITY_UNAVAILABLE` 和 `BUDGET_EXHAUSTED`。不存在泛化的 `SUCCESS` 状态。checkpoint/resume 要求 state digest、run/checkpoint lineage 和完全不同的 executor。

## Memory R0

Memory R0 只记录 run 内可追溯的 `MemoryEvent`、checkpoint、resume capsule 和公开摘要；不使用向量数据库、embedding、人格记忆或隐藏 CoT。它是恢复与审计材料，不是知识真值源，也不自动抬升任何 claim ceiling。

非知识 pilot 位于 `agent_runtime/pilots/non_knowledge_manifest.py`：它只读取声明的 fixture，生成排序后的 SHA-256 manifest，并通过第二 executor 恢复完成。这个 pilot 是隔离证明，不是生产 daemon 或真实外部工具接入。

状态：`EXPERIMENTAL_RUNTIME_WITH_OPEN_OBLIGATIONS`。
