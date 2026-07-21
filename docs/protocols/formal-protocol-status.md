# formal_protocol 状态规范

> 用途：定义 Protocol 层资产的状态分级，区分候选/正式/待定。
> 红线：本文件为**规范文档**，不修改 `data/meta-protocols/meta-protocols.json` 的现有 `status` 字段（当前 12 协议均为 `candidate_formalized`）。

## 状态分级

| 状态 | 含义 | 当前使用 |
|---|---|---|
| `candidate_protocol` | 候选协议：提出但未形式化，或仅存在于生成空间 | 建议用于早期未形式化的协议草稿 |
| `candidate_formalized` | 候选已形式化：已写入 meta-protocols.json，有 definition/formal_expression，但**未获 GPT 授权升为正式资产** | **当前 12 协议均在此状态**（assertion_level=L2）|
| `formal_protocol` | 正式协议：经 GPT 显式授权，纳入正式 Protocol 层资产 | 当前 0 个（待授权）|
| `pending_protocol` | 待定协议：形式化有缺口、待人类复核（对应条目 `pending` 字段非空）| 12 协议条目均含 pending 项，可标记 |

## 升级路径（需 GPT 授权）

```
candidate_protocol
   → candidate_formalized  (当前状态，由 PR #4 合并落地)
   → formal_protocol       (需 GPT 显式授权；本回合不自动升级)
pending_protocol 可与上述任一并存（pending 项未清前不升 formal）
```

## 与 Ψ₀ 红线的一致性

- 状态升级**不修改 Ψ₀ 数学定义**、**不新增 D/MF/T/A**、**不修改函数表/案例表**。
- 22 本书候选（BC-xxx）状态独立于 Protocol 状态，不随 Protocol 升级而进入案例表。

建立时间：2026-07-09（IGNITION-20260709-015，formal-protocol-status spec）
