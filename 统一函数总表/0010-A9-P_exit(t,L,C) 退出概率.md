---
kind: "function"
seq: 10
id: "A9"
raw_id: "A9"
title: "P_exit(t,L,C) 退出概率 / P_exit(t,L,C) exit probability"
source: "统一函数总表 A层(公理层) 2026.06.30版"
source_line: 471
link: "docs/zh/functions/items/A9.md"
---

### [A9｜P_exit(t,L,C) 退出概率 / P_exit(t,L,C) exit probability](docs/zh/functions/items/A9.md)



## 2026.06.30 收敛结论
2026.06.30 收敛结论：A层收敛。A1/A3/A8 属于框架起点，其余条目归入通用结构。
**数学表达 / Mathematical Expression**
中文：P_exit = f(ε, C_exit, R_perceived)
English: P_exit = f(ε, C_exit, R_perceived)


<details>
<summary>数学推导过程 / Mathematical Derivation</summary>

- 对象 / Object: `F_{A9}`
- 定义域 / Domain: `X_{A9}`
- 值域 / Codomain: `Y_{A9}`
- 数学表达 / Expression: `F_{A9}(x) := P_exit = f(ε, C_exit, R_perceived)`
- 有效条件 / Validity: `J_n^+(F_{A9})=1 ∧ J_n^-(F_{A9})=0`
- 推导类型 / Derivation type: `pure_math_function_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `A9`
- 推导步骤 / Steps:
  - 1. Define the local state space X_{A9} and codomain Y_{A9}.
  - 2. Normalize the source expression as F_{A9}: X_{A9}->Y_{A9}.
  - 3. If upstream objects D_{A9} exist, compose F_{A9}=N(⊕_{g∈D_{A9}} g); otherwise treat F_{A9} as an axiom seed.
  - 4. Accept iff J_n^+(F_{A9})=1 and J_n^-(F_{A9})=0.
- 证明义务 / Proof obligations:
  - `non_empty_math_expression`
  - `defined_domain_and_codomain`
  - `forward_reverse_non_contradiction`
- 正向检查 / Forward check: `J_n^+(F_{A9})=1`
- 反向检查 / Reverse check: `J_n^-(F_{A9})=0`
- 收敛判据 / Convergence: `Converged(F_{A9}) ⇔ ΔF_{A9}=∅ ∧ (J_n^+,J_n^-)=(1,0)`



</details>

**关联案例 / Related Cases**
- [#1｜周公制礼](docs/zh/cases/items/C-0001.md)
- [#3｜秦统一](docs/zh/cases/items/C-0003.md)
- [#145｜地理约束×认知约束](docs/zh/cases/items/C-0145.md)
- [#149｜信息密度×认知容量](docs/zh/cases/items/C-0149.md)
- [#205｜A8/A9从推论升级到公理](docs/zh/cases/items/C-0205.md)
- [#671｜公理化体系×三层函数结构验证](docs/zh/cases/items/C-0671.md)
- [统一案例总表索引]()

## 原文捞回 / Source Recovery

**注释 / Annotation**
应约者退出概率，是退出权信号、退出成本、感知退出权的函数。

**扩展注释 / Extended Annotation**
从A7、A5、A4推导。退出概率由三个因子决定，任一因子为零则退出概率为零。

**发现 / Discovery**
应约者退出概率，是退出权信号、退出成本、感知退出权的函数。

**推测 / Hypothesis**
从原文看，应约者退出概率，是退出权信号、退出成本、感知退出权的函数。 更像是一个用于把局部现象拉到跨域统一结构上的函数。

**验证 / Verification**
#1周公制礼(P_exit中等)→应约者可退出；#3秦统一(P_exit≈0)→应约者无法退出。

**原文来源 / Source**：`/Users/zhiyuan/我的笔记/getnote-notes/点火/2026-06-12_1912608275105464048_点火｜函数_A9.md`
