---
kind: "function"
seq: 85
id: "D36"
raw_id: "D36"
title: "逆Weibull寿命验证函数"
source: "统一函数总表 D层(推论层) 第1批 D1-D90 2026.06.30版"
source_line: 3422
link: "docs/zh/functions/items/D36.md"
---

### [D36｜逆Weibull寿命验证函数](docs/zh/functions/items/D36.md)



## 2026.06.30 收敛结论
2026.06.30 收敛结论：D层第1批收敛。归入通用结构约 70 条，独立但收敛约 20 条，缺失约 10 条。
**数学表达 / Mathematical Expression**
中文：F(t) = exp(-(θ/t)^β), β_system = β₀ + γ × n_lock_avg
English: F(t) = exp(-(θ/t)^β), β_system = β₀ + γ x n_lock_avg


<details>
<summary>数学推导过程 / Mathematical Derivation</summary>

- 对象 / Object: `F_{D36}`
- 定义域 / Domain: `X_{D36}`
- 值域 / Codomain: `Y_{D36}`
- 数学表达 / Expression: `F_{D36}(x) := F(t) = exp(-(θ/t)^β), β_system = β₀ + γ × n_lock_avg`
- 有效条件 / Validity: `J_n^+(F_{D36})=1 ∧ J_n^-(F_{D36})=0`
- 推导类型 / Derivation type: `pure_math_function_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D36`
- 推导步骤 / Steps:
  - 1. Define the local state space X_{D36} and codomain Y_{D36}.
  - 2. Normalize the source expression as F_{D36}: X_{D36}->Y_{D36}.
  - 3. If upstream objects D_{D36} exist, compose F_{D36}=N(⊕_{g∈D_{D36}} g); otherwise treat F_{D36} as an axiom seed.
  - 4. Accept iff J_n^+(F_{D36})=1 and J_n^-(F_{D36})=0.
- 证明义务 / Proof obligations:
  - `non_empty_math_expression`
  - `defined_domain_and_codomain`
  - `forward_reverse_non_contradiction`
- 正向检查 / Forward check: `J_n^+(F_{D36})=1`
- 反向检查 / Reverse check: `J_n^-(F_{D36})=0`
- 收敛判据 / Convergence: `Converged(F_{D36}) ⇔ ΔF_{D36}=∅ ∧ (J_n^+,J_n^-)=(1,0)`



</details>

**关联案例 / Related Cases**
- [#3｜秦统一](docs/zh/cases/items/C-0003.md)
- [#118｜倒U型驱动力](docs/zh/cases/items/C-0118.md)
- [#277｜D123与D36倒U型同构](docs/zh/cases/items/C-0277.md)
- [统一案例总表索引]()

## 原文捞回 / Source Recovery

**注释 / Annotation**
逆Weibull寿命验证，系统β值由基础β和锁定强度决定。

**扩展注释 / Extended Annotation**
从Weibull分布、D1推导。

**发现 / Discovery**
逆Weibull寿命验证，系统β值由基础β和锁定强度决定。

**推测 / Hypothesis**
从原文看，逆Weibull寿命验证，系统β值由基础β和锁定强度决定。 更像是一个用于把局部现象拉到跨域统一结构上的函数。

**验证 / Verification**
#3秦统一(β跳变→突然崩溃)。

**原文来源 / Source**：`/Users/zhiyuan/我的笔记/getnote-notes/点火/2026-06-12_1912611034619854576_点火｜函数_D36.md`
