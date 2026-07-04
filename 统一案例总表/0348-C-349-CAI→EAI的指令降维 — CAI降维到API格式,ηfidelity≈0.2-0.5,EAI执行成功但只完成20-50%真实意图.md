---
kind: "case"
seq: 348
id: "C-349"
raw_id: "#349"
title: "CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50%真实意图 / CAI -> EAI的指令降维 - CAI降维到API格式, ηfidelity≈0.2-0.5, EAI执行成功但只完成20-50%真实意图"
source: "点火 | 统一案例总表.675版.2026.06.18.00.18.md"
source_line: 13898
link: "docs/zh/cases/items/C-0349.md"
---

### [#349｜CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50%真实意图 / CAI -> EAI的指令降维 - CAI降维到API格式, ηfidelity≈0.2-0.5, EAI执行成功但只完成20-50%真实意图](docs/zh/cases/items/C-0349.md)

**案例内容 / Case Content**
中文：案例说明：CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50%真实意图。核心函数：[D92](docs/zh/functions/items/D92.md)
English: Rule-based English rendering pending human review.

**它说明了什么 / What It Shows**
中文：CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50%真实意图。核心函数：[D92](docs/zh/functions/items/D92.md)
English: Rule-based English rendering pending human review.

<details>
<summary>纯数学函数与推导 / Pure Mathematical Function and Derivation</summary>

- 对象 / Object: `C_{C-0349}`
- 定义域 / Domain: `S_{C-0349}`
- 值域 / Codomain: `[0,1]`
- 数学表达 / Expression: `C_{C-0349}(s_{C-0349}) = (1[F_{D92}(s_{C-0349})=1])/1`
- 有效条件 / Validity: `C_{C-0349}(s_{C-0349})>0 ∧ J_n^+(C_{C-0349})=1 ∧ J_n^-(C_{C-0349})=0`
- 推导类型 / Derivation type: `case_witness_mapping_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D92`
- 推导步骤 / Steps:
  - 1. Encode the event as state s_{C-0349}∈S_{C-0349}.
  - 2. Evaluate each related function on the event state: z_i=1[F_i(s_{C-0349})=1].
  - 3. Aggregate the witness score C_{C-0349}(s_{C-0349})=(Σ_i z_i)/max(|I_{C-0349}|,1).
  - 4. Accept the case mapping iff C_{C-0349}>0 and the reverse channel does not derive ¬C_{C-0349}.
- 证明义务 / Proof obligations:
  - `event_state_defined`
  - `witness_or_related_function_present`
  - `forward_reverse_non_contradiction`
- 正向检查 / Forward check: `J_n^+(C_{C-0349})=1`
- 反向检查 / Reverse check: `J_n^-(C_{C-0349})=0`
- 收敛判据 / Convergence: `Converged(C_{C-0349}) ⇔ ΔC_{C-0349}=∅ ∧ (J_n^+,J_n^-)=(1,0)`

**关联函数 / Related Functions**
- [D92｜解码门槛降低](docs/zh/functions/items/D92.md)

</details>

## 原文捞回 / Source Recovery

**注释 / Annotation**
中文：案例说明：CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50%真实意图。核心函数：[D92](docs/zh/functions/items/D92.md)
English: Rule-based English rendering pending human review.

**扩展注释 / Extended Annotation**
中文：CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50%真实意图。核心函数：[D92](docs/zh/functions/items/D92.md)
English: Rule-based English rendering pending human review.

**发现 / Discovery**
中文：CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50%真实意图。核心函数：[D92…

**推测 / Hypothesis**
从这条案例看，中文：案例说明：CAI→EAI的指令降维 — CAI降维到API格式，ηfidelity≈0.2-0.5，EAI执行成功但只完成20-50… 更像是在验证“退出权、认同和函数映射”之间的对应关系。

**验证 / Verification**
- 对象 / Object: `C_{C-0349}`
- 定义域 / Domain: `S_{C-0349}`
- 值域 / Codomain: `[0,1]`
- 数学表达 / Expression: `C_{C-0349}(s_{C-0349}) = (1[F_{D92}(s_{C-0349})=1])/1`
- 有效条件 / Validity: `C_{C-0349}(s_{C-0349})>0 ∧ J_n^+(C_{C-0349})=1 ∧ J_n^-(C_{C-0349})=0`
- 收敛状态 / Convergence status: `converged`
- 正向检查 / Forward check: `J_n^+(C_{C-0349})=1`
- 反向检查 / Reverse check: `J_n^-(C_{C-0349})=0`
- 收敛判据 / Convergence: `Converged(C_{C-0349}) ⇔ ΔC_{C-0349}=∅ ∧ (J_n^+,J_n^-)=(1,0)`

**原文来源 / Source**：`/Users/zhiyuan/我的笔记/统一案例总表/0348-C-349-CAI→EAI的指令降维 — CAI降维到API格式,ηfidelity≈0.2-0.5,EAI执行成功但只完成20-50%真实意图.md`
