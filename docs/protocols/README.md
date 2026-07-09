# Protocol 层（元协议生成层）

> 本目录是点火项目 **Protocol 层** 的正式入口与导航。
> 本层是 `Ψ₀ → P_meta → Protocol → Function → Case` 分层架构中的 **生成规则层**，与 Function 层、Case 层平行，互不计入。

## 本层定位

点火框架分层结构：

```
L0  Ψ₀ 元判定与收敛框架（总入口）
      │  组件之一：P_meta（元协议投影算子）
L1  Protocol 层 —— 12 元协议（V1–V4 / S1–S4 / E1–E4）+ V×S×E=64 组合空间
      │  实例化
L2  Function 层 —— 统一函数总表（D / MF / T / A 编号）
      │  实例化
L3  Case 层 —— 统一案例总表（C 编号）+ 22 本书候选（candidate_only）
```

## 入口与索引

- 架构说明：[protocol-architecture.md](./protocol-architecture.md)
- 12 元协议索引：[protocol-index.md](./protocol-index.md)
- 条目模板：[../templates/protocol-entry-template.md](../templates/protocol-entry-template.md)
- **12 协议独立条目**：[entries/](./entries/)（V1–V4 / S1–S4 / E1–E4）
- **Protocol 与两张表关系**：[protocol-table-relation.md](./protocol-table-relation.md)
- **related_function_ids 映射草案**：[related-function-ids.md](./related-function-ids.md)
（分析用，不新增编号、不改函数表）
- **formal_protocol 状态规范**：[formal-protocol-status.md](./formal-protocol-status.md)
- 底层数据：`data/meta-protocols/meta-protocols.json`（12 协议 schema）、`data/meta-protocols/meta-protocol-combinations.json`（64 组合）

## 编号体系

| 层 | 编号体系 | 是否计入其他层 |
|---|---|---|
| Meta（Ψ₀） | Ψ₀ + 六组件记号（C / M / I_iso / L_meta / G_δ / P_meta，属记号非 ID） | 否 |
| **Protocol** | **V1–V4 / S1–S4 / E1–E4**（生成空间坐标轴）+ V-S-E 组合（64） | **否，独立命名空间** |
| Function | D / MF / T / A | 否 |
| Case | C-1…C-809 | 否 |

Protocol 层编号（`V/S/E`）与 Function 层编号（`D/MF/T/A`）**命名空间隔离**，互不计入、互不替换。

## 红线（本层不可越界）

- 不修改 Ψ₀ 数学定义；
- 不修改统一函数总表；
- 不新增 D/MF/T/A 编号；
- 不把 Protocol 写入函数数量；
- 不把 22 本书候选案例直接变成正式案例；
- 不删除旧文档。

## 验证

本层基础设施为文档/模板，不引入新数据文件结构；以下校验器仍须通过（见仓库 `tools/`）：

- `python3 tools/validate_data.py` → `ALL_P1_DATA_VALID`
- `python3 tools/validate_meta_protocols.py` → `ALL_META_PROTOCOL_DATA_VALID`

建立时间：2026-07-09（IGNITION-20260709-012，015 增补 entries/ 与关系/映射/状态文档）
