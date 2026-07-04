---
kind: "function"
seq: 9
id: "A8"
raw_id: "A8"
title: "dim(t,L) 决策维度 / dim(t,L) decision dimension"
source: "统一函数总表 A层(公理层) 2026.06.30版"
source_line: 429
link: "docs/zh/functions/items/A8.md"
---

### [A8｜dim(t,L) 决策维度 / dim(t,L) decision dimension](docs/zh/functions/items/A8.md)



## 2026.06.30 收敛结论
2026.06.30 收敛结论：A层收敛。A1/A3/A8 属于框架起点，其余条目归入通用结构。
**数学表达 / Mathematical Expression**
中文：dim = 2(无犹豫域) 或 3(有犹豫域)
English: Rule-based English rendering pending human review.


<details>
<summary>数学推导过程 / Mathematical Derivation</summary>

- 对象 / Object: `F_{A8}`
- 定义域 / Domain: `X_{A8}`
- 值域 / Codomain: `Y_{A8}`
- 数学表达 / Expression: `F_{A8}(x) := dim = 2(无犹豫域) 或 3(有犹豫域)`
- 有效条件 / Validity: `J_n^+(F_{A8})=1 ∧ J_n^-(F_{A8})=0`
- 推导类型 / Derivation type: `pure_math_function_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A8`
- 推导步骤 / Steps:
  - 1. Define the local state space X_{A8} and codomain Y_{A8}.
  - 2. Normalize the source expression as F_{A8}: X_{A8}->Y_{A8}.
  - 3. If upstream objects D_{A8} exist, compose F_{A8}=N(⊕_{g∈D_{A8}} g); otherwise treat F_{A8} as an axiom seed.
  - 4. Accept iff J_n^+(F_{A8})=1 and J_n^-(F_{A8})=0.
- 证明义务 / Proof obligations:
  - `non_empty_math_expression`
  - `defined_domain_and_codomain`
  - `forward_reverse_non_contradiction`
- 正向检查 / Forward check: `J_n^+(F_{A8})=1`
- 反向检查 / Reverse check: `J_n^-(F_{A8})=0`
- 收敛判据 / Convergence: `Converged(F_{A8}) ⇔ ΔF_{A8}=∅ ∧ (J_n^+,J_n^-)=(1,0)`



</details>

**关联案例 / Related Cases**
- [#1｜周公制礼](docs/zh/cases/items/C-0001.md)
- [#3｜秦统一](docs/zh/cases/items/C-0003.md)
- [#150｜现场调研的乘数效应](docs/zh/cases/items/C-0150.md)
- [#162｜定投指数基金](docs/zh/cases/items/C-0162.md)
- [#205｜A8/A9从推论升级到公理](docs/zh/cases/items/C-0205.md)
- [#248｜博弈策略空间=可选集](docs/zh/cases/items/C-0248.md)
- [#662｜四方向联合碰撞验证](docs/zh/cases/items/C-0662.md)
- [统一案例总表索引]()

## 原文捞回 / Source Recovery

**注释 / Annotation**
决策维度，二值变量。不可推导，作为框架起点。

**扩展注释 / Extended Annotation**
公理级函数，不可推导。从历史案例归纳：有犹豫域(dim=3)系统更脆弱，无犹豫域(dim=2)系统更稳定。

**发现 / Discovery**
决策维度，二值变量。不可推导，作为框架起点。

**推测 / Hypothesis**
从原文看，决策维度，二值变量。不可推导，作为框架起点。 更像是一个用于把局部现象拉到跨域统一结构上的函数。

**验证 / Verification**
#1周公制礼(dim=2)→八百年；#3秦统一(dim=2)→15年亡(但通过H压制犹豫域)。

**原文来源 / Source**：`/Users/zhiyuan/我的笔记/getnote-notes/点火/2026-06-12_1912608271883714288_点火｜函数_A8.md`
