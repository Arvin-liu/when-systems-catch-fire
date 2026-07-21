# Protocol 与两张表关系说明

> 配套 [README.md](./README.md) 与 [protocol-index.md](./protocol-index.md)。
> 核心主张：**Protocol → Function → Case**，而非 **Protocol = Function**。

## 1. 三层关系（再次强调）

```
Ψ₀ (根判定与收敛框架)
 └─ P_meta (六组件之一：元协议投影算子)
     └─ 12 元协议 (Protocol 层：V/S/E 坐标轴，生成空间)
         └─ 64 组合 (V×S×E 生成点)
             └─ Function 层 (D/MF/T/A：计算工具，由协议空间实例化)
                 └─ Case 层 (C 编号：已验证实例)
```

## 2. Protocol 层 ↔ 函数表（统一函数总表）

| 关系维度 | 说明 |
|---|---|
| 本体 | Protocol = 运行规则（"允许做什么"）；Function = 计算工具（"怎么做"） |
| 编号 | Protocol 用 V/S/E 独立体系；Function 用 D/MF/T/A |
| 引用 | Protocol 条目可引用 Function ID（见 `entries/*.md` 的 `related_functions`），但**引用不计入函数数量** |
| 实例化 | Function 可由 Protocol 空间实例化（如门控函数族 T27/T28/T31 为开放边界 S2 的数学实现），但 Function 不反向"拥有" Protocol |
| 计数隔离 | 12 协议 0 计入函数数量；617 函数 0 计入协议数量 |

## 3. Protocol 层 ↔ 案例表（统一案例总表）

| 关系维度 | 说明 |
|---|---|
| 本体 | Case = 已验证实例（C 编号）；Protocol 条目仅引用，不新增案例 |
| 22 本书候选 | BC-xxx 当前为 `candidate_only`，不进入案例表；Protocol 条目引用仅为分析关联 |
| 验证流向 | Protocol（规则）→ Function（工具）→ Case（实例）；Case 验证函数与框架，而非把 Protocol 直接采纳为资产 |

## 4. 映射位置

- `related_function_ids` 草案见 [related-function-ids.md](./related-function-ids.md)（分析用，不新增编号、不改函数表）。
- 12 协议条目见 [entries/](./entries/)（V1–V4 / S1–S4 / E1–E4）。

## 5. 红线重申

- Protocol ≠ Function；不进入 D/MF/T/A；不计入函数数量。
- 22 本书候选不进案例表。
- 本文件为关系说明，不修改 Ψ₀ / 函数表 / 案例表 / data schema。

建立时间：2026-07-09（IGNITION-20260709-015，protocol-table-relation）
