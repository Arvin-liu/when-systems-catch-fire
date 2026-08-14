---
kind: "case"
seq: 315
id: "C-315"
raw_id: "#315"
title: "异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了"
source: "点火 | 统一案例总表.675版.2026.06.18.00.18.md"
source_line: 12552
link: "docs/zh/cases/items/C-0315.md"
---

### [#315｜异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了](docs/zh/cases/items/C-0315.md)

**案例内容 / Case Content**
中文：案例说明：异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了。核心函数：[D77](docs/zh/functions/items/D77.md)-D78
English: Rule-based English rendering pending human review.

**它说明了什么 / What It Shows**
中文：异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了。核心函数：[D77](docs/zh/functions/items/D77.md)-D78
English: Rule-based English rendering pending human review.

<details>
<summary>纯数学函数与推导 / Pure Mathematical Function and Derivation</summary>

- 对象 / Object: `C_{C-0315}`
- 定义域 / Domain: `S_{C-0315}`
- 值域 / Codomain: `[0,1]`
- 数学表达 / Expression: `C_{C-0315}(s_{C-0315}) = (1[F_{D77}(s_{C-0315})=1] + 1[F_{D78}(s_{C-0315})=1])/2`
- 有效条件 / Validity: `C_{C-0315}(s_{C-0315})>0 ∧ J_n^+(C_{C-0315})=1 ∧ J_n^-(C_{C-0315})=0`
- 推导类型 / Derivation type: `case_witness_mapping_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D77`, `D78`
- 推导步骤 / Steps:
  - 1. Encode the event as state s_{C-0315}∈S_{C-0315}.
  - 2. Evaluate each related function on the event state: z_i=1[F_i(s_{C-0315})=1].
  - 3. Aggregate the witness score C_{C-0315}(s_{C-0315})=(Σ_i z_i)/max(|I_{C-0315}|,1).
  - 4. Accept the case mapping iff C_{C-0315}>0 and the reverse channel does not derive ¬C_{C-0315}.
- 证明义务 / Proof obligations:
  - `event_state_defined`
  - `witness_or_related_function_present`
  - `forward_reverse_non_contradiction`
- 正向检查 / Forward check: `J_n^+(C_{C-0315})=1`
- 反向检查 / Reverse check: `J_n^-(C_{C-0315})=0`
- 收敛判据 / Convergence: `Converged(C_{C-0315}) ⇔ ΔC_{C-0315}=∅ ∧ (J_n^+,J_n^-)=(1,0)`

**关联函数 / Related Functions**
- [D77｜犹豫域退化函数](docs/zh/functions/items/D77.md)

</details>

## 原文捞回 / Source Recovery

**注释 / Annotation**
中文：案例说明：异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了。核心函数：[D77](docs/zh/functions/items/D77.md)-D78
English: Rule-based English rendering pending human review.

**扩展注释 / Extended Annotation**
中文：异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了。核心函数：[D77](docs/zh/functions/items/D77.md)-D78
English: Rule-based English rendering pending human review.

**发现 / Discovery**
中文：异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了。核心函数：[D77](docs/zh/functio…

**推测 / Hypothesis**
从这条案例看，中文：案例说明：异地恋断裂 — μ翻转导致dcritical从2000km缩到50km，不是距离变了是临界距离变了。核心函数：[D77](… 更像是在验证“退出权、认同和函数映射”之间的对应关系。

**验证 / Verification**
- 对象 / Object: `C_{C-0315}`
- 定义域 / Domain: `S_{C-0315}`
- 值域 / Codomain: `[0,1]`
- 数学表达 / Expression: `C_{C-0315}(s_{C-0315}) = (1[F_{D77}(s_{C-0315})=1] + 1[F_{D78}(s_{C-0315})=1])/2`
- 有效条件 / Validity: `C_{C-0315}(s_{C-0315})>0 ∧ J_n^+(C_{C-0315})=1 ∧ J_n^-(C_{C-0315})=0`
- 收敛状态 / Convergence status: `converged`
- 正向检查 / Forward check: `J_n^+(C_{C-0315})=1`
- 反向检查 / Reverse check: `J_n^-(C_{C-0315})=0`
- 收敛判据 / Convergence: `Converged(C_{C-0315}) ⇔ ΔC_{C-0315}=∅ ∧ (J_n^+,J_n^-)=(1,0)`

**原文来源 / Source**：`/Users/zhiyuan/我的笔记/统一案例总表/0315-C-315-异地恋断裂 — μ翻转导致dcritical从2000km缩到50km,不是距离变了是临界距离变了.md`
