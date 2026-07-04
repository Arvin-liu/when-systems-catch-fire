---
kind: "function"
seq: 5
id: "A4"
raw_id: "A4"
title: "R_perceived(t,L,C) 应约者感知退出权 / R_perceived(t,L,C) perceived responder exit right"
source: "统一函数总表 A层(公理层) 2026.06.30版"
source_line: 268
link: "docs/zh/functions/items/A4.md"
---

### [A4｜R_perceived(t,L,C) 应约者感知退出权 / R_perceived(t,L,C) perceived responder exit right](docs/zh/functions/items/A4.md)



## 2026.06.30 收敛结论
2026.06.30 收敛结论：A层收敛。A1/A3/A8 属于框架起点，其余条目归入通用结构。
**数学表达 / Mathematical Expression**
中文：R_perceived = R × f(ε_aware, 信息可及性, C_exit_eff)
English: Rule-based English rendering pending human review.


<details>
<summary>数学推导过程 / Mathematical Derivation</summary>

- 对象 / Object: `F_{A4}`
- 定义域 / Domain: `X_{A4}`
- 值域 / Codomain: `Y_{A4}`
- 数学表达 / Expression: `F_{A4}(x) := R_perceived = R × f(ε_aware, 信息可及性, C_exit_eff)`
- 有效条件 / Validity: `J_n^+(F_{A4})=1 ∧ J_n^-(F_{A4})=0`
- 推导类型 / Derivation type: `pure_math_function_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A4`
- 推导步骤 / Steps:
  - 1. Define the local state space X_{A4} and codomain Y_{A4}.
  - 2. Normalize the source expression as F_{A4}: X_{A4}->Y_{A4}.
  - 3. If upstream objects D_{A4} exist, compose F_{A4}=N(⊕_{g∈D_{A4}} g); otherwise treat F_{A4} as an axiom seed.
  - 4. Accept iff J_n^+(F_{A4})=1 and J_n^-(F_{A4})=0.
- 证明义务 / Proof obligations:
  - `non_empty_math_expression`
  - `defined_domain_and_codomain`
  - `forward_reverse_non_contradiction`
- 正向检查 / Forward check: `J_n^+(F_{A4})=1`
- 反向检查 / Reverse check: `J_n^-(F_{A4})=0`
- 收敛判据 / Convergence: `Converged(F_{A4}) ⇔ ΔF_{A4}=∅ ∧ (J_n^+,J_n^-)=(1,0)`



</details>

**关联案例 / Related Cases**
- [#1｜周公制礼](docs/zh/cases/items/C-0001.md)
- [#3｜秦统一](docs/zh/cases/items/C-0003.md)
- [#660｜AI医疗 × 点火框架碰撞验证](docs/zh/cases/items/C-0660.md)
- [#662｜四方向联合碰撞验证](docs/zh/cases/items/C-0662.md)

## 原文捞回 / Source Recovery

**注释 / Annotation**
应约者感知到的退出权，是真实退出权经过感知函数过滤后的结果。相变四路径。

**扩展注释 / Extended Annotation**
从A3推导。应约者只能感知到他们意识到的退出权，受遮蔽H、信息可及性、有效退出成本影响。

**发现 / Discovery**
应约者感知到的退出权，是真实退出权经过感知函数过滤后的结果。相变四路径。

**推测 / Hypothesis**
从原文看，应约者感知到的退出权，是真实退出权经过感知函数过滤后的结果。相变四路径。 更像是一个用于把局部现象拉到跨域统一结构上的函数。

**验证 / Verification**
#1周公制礼(R_perceived≈R)→应约者有真实感知；#3秦统一(R_perceived≈0)→应约者感知不到退出权。

**原文来源 / Source**：`/Users/zhiyuan/我的笔记/getnote-notes/点火/2026-06-12_1912608245038595824_点火｜函数_A4.md`
