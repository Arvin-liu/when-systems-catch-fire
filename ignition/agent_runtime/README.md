# Agent Runtime R0 / R1

## R1 当前能力

R1 把 R0 的编排接口接到一个受声明 workspace policy 约束的本地行动层：

`Observe → Frame → Plan → Authorize → Act → Validate → Remember → Continue/Stop`

当前实现包括：

- typed `ExecutionPacket`，文件读写、目录读取、哈希、受 allowlist 约束的 literal argv 命令，以及只读 Git 状态/差异；没有 shell 解析、删除、远端 Git 变更、安装包、sudo、网络开关或系统设置接口。
- path component、symlink、special-file、读写根、可执行文件、argv 前缀、输出上限、超时、动作/写入预算和 bounded preimage 检查。
- execution lease、持久 idempotency key、locked action journal、明确的 `PREPARED → EXECUTING → COMPLETED/RECONCILED` 和 `AMBIGUOUS` 状态。
- typed approval request/decision 与 CLI；批准前不会触碰写目标，authority type 只接受外部 human/operator/CLI 或离线 pilot 类别。
- 本地文件 preimage 回滚；命令、Git 读取和其他未声明可逆动作不伪造回滚能力。
- provider-neutral JSONL-over-stdio Reasoner 接口；R1 不要求某个 provider、模型名、API key、向量服务或 daemon。
- `run-spec` 必须显式声明 profile、goal、workspace policy、capability scope、Reasoner adapter、`local_workspace` Executor adapter 和 Validator；缺字段不会从外部上下文补齐。

## Pack Registry / Bus R1

`agent_runtime.pack_registry` provides a declarative `PackRegistry`,
`PackLoader`, `CapabilityRoute` and `PackBus`. The registry discovers the four
current manifests under `packs/`; the loader validates and loads metadata only,
without importing Pack modules or executing hooks; the Bus returns typed
`ROUTED_PROPOSAL` records and never performs domain actions.

The CLI exposes `agent-runtime packs list`, `show` and `validate`. Pack
manifests request bounded paths/tools and must explicitly prohibit Kernel
authority upgrades. The current registry is offline and provider-neutral; it
does not grant network, Owner, executor, permission, truth, or epistemic
authority.

`agent_runtime.routing.PackAwareRouter` adds the legal connection to planning
and validation: each action provenance names one loaded manifest capability,
object type, validator and optional hook; validator receipts are constrained to
the Pack's declared object types and entrypoints. A scoped router can only see
Profile-allowed loaded Packs. Knowledge validation cannot grant runtime
permission or truth authority, writing quality cannot establish facts, and a
REOS LIGHT workflow cannot create Owner acceptance or epistemic acceptance.

## Operational Memory R1

`agent_runtime.memory.OperationalMemoryStore` is a locked JSON store for typed
episodic, procedural, feedback, failure, rollback, approval, Pack-usage and
unresolved-continuation summaries. Every entry carries its source run,
retention/visibility/sensitivity policy, provenance and owner-feedback refs,
expiry/forget policy, supersession lineage and integrity digest.

The store supports typed query, supersede, redacting forget/expire tombstones,
and bounded context-capsule export. It rejects secret, prompt and hidden
reasoning material; repeated memory is not evidence and memory cannot mutate
Charter or permissions. It is operational recall only, not a Knowledge truth
registry.

## Supervisor R0

`agent_runtime.supervisor.Supervisor` persists an offline, sequential episode
DAG around independent R1 child run directories. It validates dependencies and
the episode-wide capability ceiling, enforces action/time/output budgets,
aggregates approval requests, supports bounded retries and executor-instance
handoff, and records explicit episode roll-ups such as
`EPISODE_COMPLETED_VALIDATED`, `EPISODE_WAITING_FOR_APPROVAL`,
`EPISODE_CHECKPOINTED_RESUMABLE` and `EPISODE_FAILED_FAST`.

The Supervisor can resume a persisted episode after process restart. It never
widens a child `capability_scope`, changes the declared executor adapter,
grants Owner or truth authority, or uses a generic `SUCCESS` terminal state.
The CLI exposes `episode start/status/resume/trace/pending-approval`, plus
typed `episode approve` and `episode handoff` commands.

## Agent Profile R1

`agent_kernel.AgentProfile` now carries allowed Packs, preferred/forbidden
tool classes, typed approval thresholds, bounded budget defaults, update
authority and prohibited authority upgrades. The three checked-in capability
profiles are `repository-maintainer`, `bounded-researcher` and
`human-surface-writer` in `data/agent-runtime/agent-profiles-r1.json`.

`agent_runtime.profile.project_profile` intersects a profile with the already
declared R1 scope, may lower action/write/output budgets, and may strengthen a
typed approval requirement. It cannot add a capability, write root,
executable, Pack, network permission, Charter authority or executor adapter.
`Supervisor.start(..., profiles=...)` applies this projection before persisting
the episode; `episode start --profiles` exposes the same boundary on the CLI.

## Reasoner Gateway R1

`agent_runtime.transport.ReasonerGateway` adds the versioned
`reasoner-gateway-r1` request/response contract around the existing R1
Reasoner interface. Requests carry a deterministic SHA-256 digest, bounded
context capsule, and read-only Pack/capability catalog. Responses can only
propose typed packets; the Gateway rejects schema mismatch, digest mismatch,
unknown capabilities, self-approved authority claims, forged completion
claims, malformed/oversized/crashed/timed-out subprocess output and any
generic `SUCCESS` status.

The deterministic `ScriptedGatewayAdapter`, literal-argv
`SubprocessReasonerAdapter` and `AdversarialGatewayAdapter` are all offline.
Provider/model fields are telemetry only; no API key, live provider or
execution authority is stored or inferred. R1 specs may select
`gateway-scripted` or `gateway-jsonl`, and the existing runtime remains the
only executor.

R1 的 terminal state 新增 `FAILED_VALIDATION_ROLLED_BACK`、`ROLLBACK_FAILED` 和 `REQUIRES_RECONCILIATION`。后一个状态表示 durable journal 无法证明“未执行”或“已达到预期 postimage”；运行时不会猜测或自动升级为完成。

真实离线 pilot 位于 `agent_runtime/pilots/r1_real_local.py`：Pilot A 验证批准后真实写入和 allowlisted command validator；Pilot B 验证跨 executor 重启、post-execute crash 的 postimage reconcile、lease/idempotency 记录和失败后的文件回滚。

R2 夜班的真实离线多 Run episode 位于
`agent_runtime/pilots/r2_repository_maintenance.py`：它先建立 disposable
source repository，再用 fresh local clone 驱动 `audit → repair → validate`
依赖 DAG；修复动作在 post-execute/pre-persist 故障点暂停为
`EPISODE_CHECKPOINTED_RESUMABLE`，随后由不同 executor instance 恢复。提交的
receipt 还保留 typed approvals、operational-memory FAILURE/EPISODIC 摘要、
对抗性独立失败和 `network_allowed=false`/`remote_mutation=false` 边界；这
是离线仓库维护观察，不是外部效果或一般智能证明。

## R0 历史边界

Agent Runtime R0 实现最小的通用循环：

`Observe → Frame → Plan → Authorize → Act → Validate → Remember → Continue/Stop`

Runtime 只编排 typed records，不决定领域真值。Reasoner、Executor 和 Validator 是显式接口；运行时不要求模型名称、provider 名称、网络或常驻 daemon。每个动作先经过 Kernel capability scope 授权，再交给 executor；授权失败、能力未知、需要 Owner 批准或预算耗尽都会进入明确 stop state。

R0 的 stop state 至少包括 `COMPLETED_VALIDATED`、`BLOCKED_WITH_EVIDENCE`、`WAITING_FOR_APPROVAL`、`FAILED_VALIDATION`、`ABORTED_BY_OWNER`、`CAPABILITY_UNAVAILABLE` 和 `BUDGET_EXHAUSTED`。不存在泛化的 `SUCCESS` 状态。checkpoint/resume 要求 state digest、run/checkpoint lineage 和完全不同的 executor。

## Memory R0

Memory R0 只记录 run 内可追溯的 `MemoryEvent`、checkpoint、resume capsule 和公开摘要；不使用向量数据库、embedding、人格记忆或隐藏 CoT。它是恢复与审计材料，不是知识真值源，也不自动抬升任何 claim ceiling。

非知识 pilot 位于 `agent_runtime/pilots/non_knowledge_manifest.py`：它只读取声明的 fixture，生成排序后的 SHA-256 manifest，并通过第二 executor 恢复完成。这个 pilot 是隔离证明，不是生产 daemon 或真实外部工具接入。

状态：`EXPERIMENTAL_RUNTIME_WITH_OPEN_OBLIGATIONS`。

R1 仍是实验性安全执行框架，不是常驻服务、自治人格、multi-agent scheduler、长期向量 memory 或现实世界效果证明；正式仓库状态继续保持 `CURRENT_WITH_OPEN_OBLIGATIONS`，且 `EPISTEMICALLY_ACCEPTED=0`。
