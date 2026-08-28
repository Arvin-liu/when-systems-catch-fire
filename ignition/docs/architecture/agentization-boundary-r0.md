# 点火从知识治理系统向智能体运行时抽层

任务 `IGNITION-20260815-119` 的 R0 完成了领域切割和依赖解耦；任务 121 的 R2
在这个 generic boundary 上接入 Pack、Memory、Supervisor、Gateway、Profile 和
真实离线维护 pilot，仍不做全仓物理大搬家。完整总架构图 SVG 继续由 registry、
typed topology 和 layout 确定性生成；SVG 源码可以保留指向 canonical 目标的 link metadata，
但不承诺 GitHub 渲染页面提供交互热点；本页是 R0 基础边界的 Human Surface，机器边界以
[`agentization-boundary-r0.json`](../../data/architecture/agentization-boundary-r0.json)
和其 schema 为准，R2 总说明见 [`agent-platform-r2.md`](./agent-platform-r2.md)。

## 边界结论

- `Generic Kernel` 只提供身份、状态、能力、授权、审计、checkpoint、handoff、resume lineage、记忆事件和不变量契约。
- `Agent Runtime R0` 只编排 `Observe → Frame → Plan → Authorize → Act → Validate → Remember → Continue/Stop`，并把领域工作交给可加载的 Domain Pack。
- `Knowledge Domain Pack` 是第一个 Domain Pack：它承载 Foundation、claims、formal/evidence/proof/scope/provenance、M/E、functions/non-functions、Knowledge Experience、Results 和 epistemic correction 等知识对象与验证入口。
- REOS vNext LIGHT 仅作为边界清楚的 `research` Pack；之元写作法与出版面仅作为 `writing`/publication Pack。R0 不把课程内容或旧知识树物理搬入 Kernel。
- Owner/Human 与 Value Charter 位于 escalation 之上；Agent Profile 只能声明运行角色、允许 capability 类别和受 Owner 约束的偏好，不能自行修改授权或提升结论。

R2 的当前工程闭环是：`Profile narrowing → Reasoner proposal → Pack-aware
routing → Supervisor child Run → Kernel-authorized local action → typed
validation → bounded operational memory`。Reasoner 没有执行权，Pack 没有通用
permission/truth/Owner authority，Supervisor 不改变 child scope；主 episode 和
对抗 episode 的仓库范围观察见 [R2 pilot receipt](../../data/agent-runtime/pilots/r2-offline-repository-maintenance/pilot-receipt.json)。

因此：`Kernel ≠ Knowledge`，`Runtime ≠ Research`。Pack 可以被加载，Pack 不拥有通用生命周期、executor 选择、generic permission、checkpoint/resume、Owner acceptance 或 Kernel 定义权。

## 依赖方向与处置

边界 manifest 从 live `data/operations/project-components.json` 投影出 76 个组件，记录每个组件的当前路径、canonical ref、主/次角色、domain binding、Kernel 依赖方向和 move disposition。R0 的 `physical_migration.performed=false`：既有 Foundation、Evidence、REOS、写作、出版树保持原路径；新增的契约、适配层和 pilot 单独落位。当前可见系统图为 64 个节点、70 条 typed edges；隐藏组件由代表节点承载。

`ADD_R0_COMPONENT` 表示本轮新增边界资产，`REF_ONLY_NO_MOVE` 表示只登记 Pack 入口或引用适配，不移动既有领域树，`KEEP_CURRENT_PATH_R0` 与 `HISTORICAL_NO_MOVE` 保留现有组件处置。生成和校验命令为：

```bash
python3 tools/generate_agentization_boundary.py --check
python3 tools/validate_agentization_boundary.py
```

## Task 115 prior-art boundary

Task 115 的 Draft PR 只作为 prior art 审计，不是当前实现的合并来源。R0 采纳 capability token、显式读写/网络/批准权限、typed execution packet、checkpoint/resume、不同 executor、provider/model-neutral telemetry 和 fail-closed stop 的概念；将旧 research-specific stack 重写为当前 Kernel/Runtime 契约。完整处置见 [`task115-runtime-prior-art-adoption-r0.md`](../../reports/architecture/task115-runtime-prior-art-adoption-r0.md)。

## 已证明与未证明

非知识 pilot 在无 Foundation、claims、M/E、Evidence、Knowledge 或 Research 路径输入下，完成读取 fixture、排序 SHA-256 manifest、checkpoint、不同 executor resume、最终验证和结构化回执。它证明的是当前仓库范围内的依赖隔离与可恢复闭环，不证明通用智能、现实世界因果、长期自主运行或任何知识结论。

状态：`CURRENT_BOUNDED_R0_BASE_WITH_R2_PROJECTION_AND_OPEN_OBLIGATIONS`。这仍不构成通用智能、长期自主性、现实因果、生产安全或 `EPISTEMICALLY_ACCEPTED`。
