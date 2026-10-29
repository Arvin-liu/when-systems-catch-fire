# Task 115 Runtime Prior-Art Adoption Review R0

审计对象是 Task 115 的公开 Draft prior art，不是当前实现的 merge source。PR #195 `Round 1: executor-neutral action/observation boundary schemas (Draft)` 仍是 OPEN/Draft，基于旧 main；本轮没有 merge、rebase、cherry-pick 或关闭它。

| 决定 | 采纳内容 | 当前处理 |
| --- | --- | --- |
| `ADOPT_AS_IS` | capability token 不绑定 provider 品牌；显式 execution packet 的权限字段；executor 观察不能自行 approve、complete、改变 claim ceiling 或 Owner acceptance | 语义直接进入当前 Kernel `CapabilityScope`、`AuthorizationRequest` 和 typed records |
| `ADOPT_AS_IS` | provider/model-neutral 的可选 telemetry 概念 | R0 只保留公开运行摘要和 provenance refs，不引入具体 provider |
| `ADAPT_TO_CURRENT_KERNEL` | checkpoint、resume capsule、state digest、不同 executor | 重写为 `Checkpoint`/`ResumeCapsule`/`validate_resume_lineage`，并要求新 executor 不在旧 lineage 中 |
| `ADAPT_TO_CURRENT_KERNEL` | typed action observation 与 validation result | 重写为通用 `ActionRequest`、`ActionObservation`、`ValidationResult`，不携带 research truth authority |
| `ADAPT_TO_CURRENT_KERNEL` | Research OS 的 bounded state loop 和 scheduler 思路 | 只保留 Observe—Continue/Stop 的状态机；不把 research queue、obligation graph 或旧 scheduler 作为 Kernel |
| `REJECT` | research-specific claim/evidence schema、deep-research queue、旧 obligation graph 和整套旧 runtime stack | 它们属于 Domain Pack 或历史 prior art，不能成为通用边界 |
| `REJECT` | executor 自行决定 stop/completion、Owner acceptance 或权限升级 | 当前 Kernel fail closed；只有 validator 可提供最终动作验证，Owner 边界不下放 |
| `DEFER` | 多 agent queue、长期 campaign scheduler、真实 provider/API adapters | 需要另行授权、外部状态和更高风险验证；R0 不实现 |
| `DEFER` | daemon、Telegram、OpenClaw、向量 DB/embedding memory | 明确不属于本轮最小可运行时 |

结论：Task 115 提供可复用的边界概念，但当前实现是围绕 118 基线重新建模的领域无关 Kernel/Runtime；它不是旧 Draft 的隐式合并。
