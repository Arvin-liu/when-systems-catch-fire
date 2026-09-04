# Governance License Scope

SPDX-License-Identifier: CC-BY-SA-4.0 OR CC-BY-NC-SA-4.0

The life-community value charter and general governance principle texts are licensed under CC BY-SA 4.0. Governance reports, inventories, and explanatory documents are licensed under CC BY-NC-SA 4.0 unless a file says otherwise. Third-party material and unclear-rights content remain excluded.

## 治理文档索引 / Governance Index

本目录收录点火的治理与宪章文档。下表标记各文档的当前生命周期状态；状态边界遵循 `charter-system-r1.md` 的不变式：任一文档可为 `CURRENT` 而不必 `ACTIVATED`，且 `PUBLISHED_SNAPSHOT != ACCEPTED/CURRENT/ACTIVATED`。

### 当前治理系统（CURRENT）

- **`charter-system-r1.md`** — 宪章系统 R1（元治理层：宪章的提议 / 版本化 / 批准 / 决策—宪章版本绑定 / 跨 Fork 责任谱系）。状态：**CURRENT（Accepted, non-Activated）**；`on_main=true`；`activated=false`；`publication_status=UNPUBLISHED`。机器可读记录见 `charter-system-r1.schema.json`（记录 / 修订 / Fork 谱系 schema 与不变式）与 `charter-system-registry.json`（本系统注册表：状态 / 合并溯源 / 绑定宪章 / Fork 谱系）。合并于 `0e7c032`，提升为 Current 于 `0c5fbcab`（PR #138，2026-07-26）。

### 本轮研究记录（CANDIDATE / NON_CANONICAL）

Task `IGNITION-20260904-153` 对价值—认识论推导与 Human–Agent–System 的可追责认知边界进行了两条独立审计，随后才做综合。以下文件只是可反驳的研究记录，不改变 V/S/E、Charter、Kernel、Owner / Executor、Current identity 或运行时权限：

- [`value-epistemology-derivation-audit-2026-09-04.md`](./value-epistemology-derivation-audit-2026-09-04.md) — 六类治理语汇的推导矩阵、七个压力场景与候选 `P/O/N/A` 基础；结论为部分可解释、没有足够依据新增 canonical layer。
- [`accountable-cognition-boundary-map-2026-09-04.md`](./accountable-cognition-boundary-map-2026-09-04.md) — 中性的角色拓扑、13 个能力/权限/实践/规范轴与十个协作压力场景；不把 Agent、CI、artifact 或日志描述为责任主体。
- [`more-meta-foundations-synthesis-2026-09-04.md`](./more-meta-foundations-synthesis-2026-09-04.md) — 两条独立审计的 synthesis gate；选择 `ORTHOGONAL_DUAL_FOUNDATION / NO_NEW_CANONICAL_LAYER`，保留候选诊断但不制度化。
- 任务报告见 [`reports/governance/task-IGNITION-20260904-153.md`](../../reports/governance/task-IGNITION-20260904-153.md)。

Task `IGNITION-20260904-154` 是对上述综合的反证轮，仍为 `CANDIDATE / NON_CANONICAL`：

- [`more-meta-foundations-adversarial-audit-2026-09-04.md`](./more-meta-foundations-adversarial-audit-2026-09-04.md) — P/O/N/A 消融、A 的五种归属假设、四象限正交性反例、五个诊断的承载力与冲突仲裁残余；主判定为 `FALSIFIED`（仅否定强双基础命题）。
- [`more-meta-foundations-minimal-model-2026-09-04.md`](./more-meta-foundations-minimal-model-2026-09-04.md) — 比较 `M4`、`M3a`、`M3b`、`M2+T` 与 `Existing-only`，保留“现有联邦合同 + 交叉复核视图”作为最小研究表示，不新增 canonical layer。
- 任务报告见 [`reports/governance/task-IGNITION-20260904-154.md`](../../reports/governance/task-IGNITION-20260904-154.md)，结果见 [`agent-results/IGNITION-20260904-154-result.md`](../../agent-results/IGNITION-20260904-154-result.md)。

### 治理与宪章文档目录

| 文档 | 角色 |
|------|------|
| `life-community-value-charter.md` | 生命共同体价值宪章（第 1 层权威底线） |
| `charter-system-r1.md` | 宪章系统 R1（元治理层，CURRENT / non-Activated） |
| `charter-system-r1.schema.json` | 宪章记录 / 修订记录 / Fork 谱系 schema 与不变式 |
| `charter-system-registry.json` | 宪章系统注册表（本系统注册表） |
| `external-input-non-republication-principle.md` | 外部输入不重发原则 |
| `licensing-model-candidate.md` | 许可模型候选 |
| `licensing-rights-inventory.md` | 许可权利清单 |
| `non-sycophancy-output-protocol.md` | 非谄媚输出协议 |
| `meta-protocol-reviews/` | 元协议规范评审 |

> 边界：Charter System R1 为 `CURRENT` 但 `non-Activated`——其元治理权威仅约束"宪章如何被治理"，不激活任何能力 / 运行时 / 执行器；其 `publication_status=UNPUBLISHED`，不构成任何已发布快照（`HOMEPAGE_VISIBLE != CAPABILITY_AVAILABLE`）。
