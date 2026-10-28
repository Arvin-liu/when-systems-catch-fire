# Governance License Scope

SPDX-License-Identifier: CC-BY-SA-4.0 OR CC-BY-NC-SA-4.0

The life-community value charter and general governance principle texts are licensed under CC BY-SA 4.0. Governance reports, inventories, and explanatory documents are licensed under CC BY-NC-SA 4.0 unless a file says otherwise. Third-party material and unclear-rights content remain excluded.

## 治理文档索引 / Governance Index

本目录收录点火的治理与宪章文档。下表标记各文档的当前生命周期状态；状态边界遵循 `charter-system-r1.md` 的不变式：任一文档可为 `CURRENT` 而不必 `ACTIVATED`，且 `PUBLISHED_SNAPSHOT != ACCEPTED/CURRENT/ACTIVATED`。

### 当前治理系统（CURRENT）

- **`charter-system-r1.md`** — 宪章系统 R1（元治理层：宪章的提议 / 版本化 / 批准 / 决策—宪章版本绑定 / 跨 Fork 责任谱系）。状态：**CURRENT（Accepted, non-Activated）**；`on_main=true`；`activated=false`；`publication_status=UNPUBLISHED`。机器可读记录见 `charter-system-r1.schema.json`（记录 / 修订 / Fork 谱系 schema 与不变式）与 `charter-system-registry.json`（本系统注册表：状态 / 合并溯源 / 绑定宪章 / Fork 谱系）。合并于 `0e7c032`，提升为 Current 于 `0c5fbcab`（PR #138，2026-07-26）。

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
