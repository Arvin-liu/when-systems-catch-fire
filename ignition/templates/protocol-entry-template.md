# Protocol 条目模板

> 用途：为 12 元协议（V/S/E）或 64 组合中的任一协议条目撰写规范文档。
> 编号体系：Protocol 层独立编号（V1–V4 / S1–S4 / E1–E4），**不进入 Function 层编号（D/MF/T/A）**。
> 本模板为 additive 文档规范，不修改任何现有数据文件。

---

## <protocol_id> <协议中文名>（<name_en>）

- **protocol_id**：`<protocol_id>`（例：V1 / S2 / E3）
- **category**：`value | structure | evolution`（V 类 / S 类 / E 类）
- **mechanism**：<协议的运行机制：它作为"允许做什么"的规则如何约束系统演化>
- **mathematical form**：<形式化表达；若尚未形式化写 `pending`，不强行借用函数编号>
- **relation_to_psi0**：<与 Ψ₀（尤其 P_meta 组件）的关系：属于 P_meta 展开的生成空间坐标轴，约束而非替代 Ψ₀ 判定>
- **related_functions**：<引用的 Function 层 ID 列表，仅引用不计入；例：[T2, D12, T20]（可空）>
- **related_cases**：<关联的 Case 层 ID 或 22 本书候选 BC-xxx（可空）>
- **evidence**：<支撑该协议定义的案例 / 跨域同构 / 现实观察>
- **pending**：<待人类复核项、待形式化项、待补充证据项>

---

### 边界声明（必填）

- 本协议属于 **Protocol 层**，不进入 Function 层编号体系。
- 本协议不修改 Ψ₀ 数学定义，不修改统一函数总表，不新增 D/MF/T/A 编号。
- 本协议不将 22 本书候选案例直接变为正式案例。

建立时间：2026-07-09（IGNITION-20260709-012，protocol-entry-template）
