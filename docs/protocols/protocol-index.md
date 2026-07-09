# Protocol 层索引（12 元协议）

> 本索引列出 Protocol 层的 12 个元协议，采用 **Protocol 独立编号**（V/S/E），**不进入 Function 层编号体系**（D/MF/T/A）。
> 底层数据：`data/meta-protocols/meta-protocols.json`（status=`candidate_formalized`，assertion_level=L2）。
> 范围：仅索引，不改变协议状态；状态升级需 GPT 显式授权（红线：不把候选直接变成正式资产）。

## 价值维度（V1–V4）

| Protocol ID | 中文名 | 英文 | 本体定义（摘要） |
|---|---|---|---|
| V1 | 延续性协议 | Continuity Protocol | 选择使系统延续时间最大（或延续概率最高）的行动 |
| V2 | 效率性协议 | Efficiency Protocol | 以资源利用效率最大化为目标的演化规则 |
| V3 | 创新性协议 | Innovation Protocol | 选择使复杂度（熵）增加最大的行动，追求可能性空间扩张 |
| V4 | 可持续性协议 | Sustainability Protocol | 以长期动态平衡为目标，在扩张与收缩间维持循环 |

## 结构维度（S1–S4）

| Protocol ID | 中文名 | 英文 | 本体定义（摘要） |
|---|---|---|---|
| S1 | 封闭边界协议 | Closed-Boundary Protocol | 边界严格封闭，拒绝外部输入与内部输出 |
| S2 | 开放边界协议 | Open-Boundary Protocol | 边界开放，允许外部元素自由流入流出 |
| S3 | 层级边界协议 | Hierarchical-Boundary Protocol | 边界按层级划分，高层可访问低层，反之不行 |
| S4 | 网络边界协议 | Network-Boundary Protocol | 边界为网络形态，节点对等连接，无中心控制 |

## 演化维度（E1–E4）

| Protocol ID | 中文名 | 英文 | 本体定义（摘要） |
|---|---|---|---|
| E1 | 线性演化协议 | Linear-Evolution Protocol | 沿单一轨迹线性推进，状态可预测 |
| E2 | 非线性演化协议 | Non-linear-Evolution Protocol | 路径非线性，小变化引发大结果 |
| E3 | 循环演化协议 | Cyclic-Evolution Protocol | 状态间循环往复，周期性重复 |
| E4 | 收敛演化协议 | Convergent-Evolution Protocol | 向单一状态收敛，复杂度逐渐降低 |

## 组合空间（V×S×E = 64）

12 协议构成生成空间，组合数为 **4 × 4 × 4 = 64**。每个组合（`V{n}-S{n}-E{n}`）是生成空间中的一个理论形态候选，属**组合空间**而非新增函数。详见 `data/meta-protocols/meta-protocol-combinations.json`。

## 与 Ψ₀ / Function / Case 的关系

- **Ψ₀**：12 协议属于 P_meta 展开后的生成空间坐标轴；Ψ₀ 不被替换。
- **Function**：协议单向引用函数 ID，但不获得函数 ID、不计入函数数量。
- **Case**：22 本书候选为 `candidate_only`，不直接变为正式案例。

建立时间：2026-07-09（IGNITION-20260709-012，protocol-index）
