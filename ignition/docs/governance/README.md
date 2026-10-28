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

Task `IGNITION-20260905-155` 是对交叉合同复核图的历史盲测，仍为 `CANDIDATE / NON_CANONICAL`：

- [`cross-contract-historical-blind-test-2026-09-05.md`](./cross-contract-historical-blind-test-2026-09-05.md) — 27 个 Task153 之前的真实历史 case，含 discovery/holdout 冻结、existing-contract-only 与 cross-contract 两套审查、逐案解盲、误报/漏报/不可判定与五类诊断裁决；结果为 `PARTIAL_INCREMENT`，仅保留研究 lens，不新增 canonical failure class、layer、gate、schema、registry 或 authority。
- [`cross-contract-failure-casebook-2026-09-05.md`](./cross-contract-failure-casebook-2026-09-05.md) — 逐案 pre-outcome 与 unblinded evidence cards；机器冻结与结果数据位于 `data/research/cross-contract-blind-test-2026-09-05/`。
- 任务报告见 [`reports/governance/task-IGNITION-20260905-155.md`](../../reports/governance/task-IGNITION-20260905-155.md)，结果见 [`agent-results/IGNITION-20260905-155-result.md`](../../agent-results/IGNITION-20260905-155-result.md)。

Task `IGNITION-20260905-156` 是对交叉合同 junction invariant 的前瞻性、answer-key-separated fixture 复现，仍为 `RESEARCH_ONLY / NON_CANONICAL / NON_CURRENT`：

- [`cross-contract-prospective-fixture-experiment-2026-09-05.md`](./cross-contract-prospective-fixture-experiment-2026-09-05.md) — 48 对 / 96 instances、F1–F6 六类、M0/M3/M3R/M4B 冻结模型、双次 clean-state blind scoring、holdout metrics、metamorphic 与 counterfactual minimality 结果；M4B 仅保留为 bounded research invariant candidate。
- [`junction-invariant-candidate-assessment-2026-09-05.md`](./junction-invariant-candidate-assessment-2026-09-05.md) — M3R 与现有字段 binding challenger 的阈值比较；不新增 canonical layer、authority、truth state、validator、gate 或 runtime。
- [`cross-contract-prospective-casebook-2026-09-05.md`](./cross-contract-prospective-casebook-2026-09-05.md) — 每个 prospective paired fixture 的 primary/control、family genealogy、四模型结果与稳定 flip；机器冻结、盲评分、解盲和 minimality 记录位于 `data/research/cross-contract-prospective-fixtures-2026-09-05/`。
- 任务报告见 [`reports/governance/task-IGNITION-20260905-156.md`](../../reports/governance/task-IGNITION-20260905-156.md)，结果见 [`agent-results/IGNITION-20260905-156-result.md`](../../agent-results/IGNITION-20260905-156-result.md)。

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
