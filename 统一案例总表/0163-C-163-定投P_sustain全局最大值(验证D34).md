---
kind: "case"
seq: 163
id: "C-163"
raw_id: "#163"
title: "定投P_sustain全局最大值（验证D34） / 定投P_sustain全局最大值(验证D34)"
source: "点火 | 统一案例总表.675版.2026.06.18.00.18.md"
source_line: 6507
link: "docs/zh/cases/items/C-0163.md"
---

### [#163｜定投P_sustain全局最大值（验证D34） / 定投P_sustain全局最大值(验证D34)](docs/zh/cases/items/C-0163.md)

**案例内容 / Case Content**
中文：案例说明：定投P_sustain全局最大值（验证D34）
English: Rule-based English rendering pending human review.

**它说明了什么 / What It Shows**
中文：定投P_sustain全局最大值（验证D34）
English: Rule-based English rendering pending human review.

<details>
<summary>纯数学函数与推导 / Pure Mathematical Function and Derivation</summary>

- 对象 / Object: `C_{C-0163}`
- 定义域 / Domain: `S_{C-0163}`
- 值域 / Codomain: `[0,1]`
- 数学表达 / Expression: `C_{C-0163}(s_{C-0163}) = (1[F_{D34}(s_{C-0163})=1])/1`
- 有效条件 / Validity: `C_{C-0163}(s_{C-0163})>0 ∧ J_n^+(C_{C-0163})=1 ∧ J_n^-(C_{C-0163})=0`
- 推导类型 / Derivation type: `case_witness_mapping_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D34`
- 推导步骤 / Steps:
  - 1. Encode the event as state s_{C-0163}∈S_{C-0163}.
  - 2. Evaluate each related function on the event state: z_i=1[F_i(s_{C-0163})=1].
  - 3. Aggregate the witness score C_{C-0163}(s_{C-0163})=(Σ_i z_i)/max(|I_{C-0163}|,1).
  - 4. Accept the case mapping iff C_{C-0163}>0 and the reverse channel does not derive ¬C_{C-0163}.
- 证明义务 / Proof obligations:
  - `event_state_defined`
  - `witness_or_related_function_present`
  - `forward_reverse_non_contradiction`
- 正向检查 / Forward check: `J_n^+(C_{C-0163})=1`
- 反向检查 / Reverse check: `J_n^-(C_{C-0163})=0`
- 收敛判据 / Convergence: `Converged(C_{C-0163}) ⇔ ΔC_{C-0163}=∅ ∧ (J_n^+,J_n^-)=(1,0)`

**关联函数 / Related Functions**
- [D34｜充分条件三层函数](docs/zh/functions/items/D34.md)
- [D145｜投资相关函数](docs/zh/functions/items/D145.md)
- [D160｜定投凯利保守性](docs/zh/functions/items/D160.md)
- [D162｜定投凯利保守性验证](docs/zh/functions/items/D162.md)
- [D163｜定投凯利保守性](docs/zh/functions/items/D163.md)
- [D164｜定投凯利保守性](docs/zh/functions/items/D164.md)
- [D165｜定投凯利保守性](docs/zh/functions/items/D165.md)
- [D166｜定投凯利保守性](docs/zh/functions/items/D166.md)
- [D167｜定投凯利保守性](docs/zh/functions/items/D167.md)
- [D168｜定投凯利保守性](docs/zh/functions/items/D168.md)
- [D170｜定投凯利保守性验证](docs/zh/functions/items/D170.md)

</details>

## 原文捞回 / Source Recovery

**注释 / Annotation**
中文：案例说明：定投P_sustain全局最大值（验证D34）
English: Rule-based English rendering pending human review.

**扩展注释 / Extended Annotation**
中文：定投P_sustain全局最大值（验证D34）
English: Rule-based English rendering pending human review.

**发现 / Discovery**
中文：定投P_sustain全局最大值（验证D34） English: Rule-based English rendering pending human…

**推测 / Hypothesis**
从这条案例看，中文：案例说明：定投P_sustain全局最大值（验证D34） English: Rule-based English rendering… 更像是在验证“退出权、认同和函数映射”之间的对应关系。

**验证 / Verification**
- 对象 / Object: `C_{C-0163}`
- 定义域 / Domain: `S_{C-0163}`
- 值域 / Codomain: `[0,1]`
- 数学表达 / Expression: `C_{C-0163}(s_{C-0163}) = (1[F_{D34}(s_{C-0163})=1])/1`
- 有效条件 / Validity: `C_{C-0163}(s_{C-0163})>0 ∧ J_n^+(C_{C-0163})=1 ∧ J_n^-(C_{C-0163})=0`
- 收敛状态 / Convergence status: `converged`
- 正向检查 / Forward check: `J_n^+(C_{C-0163})=1`
- 反向检查 / Reverse check: `J_n^-(C_{C-0163})=0`
- 收敛判据 / Convergence: `Converged(C_{C-0163}) ⇔ ΔC_{C-0163}=∅ ∧ (J_n^+,J_n^-)=(1,0)`

**原文来源 / Source**：`/Users/zhiyuan/我的笔记/统一案例总表/0163-C-163-定投P_sustain全局最大值(验证D34).md`
