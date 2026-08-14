---
kind: "case"
seq: 366
id: "C-367"
raw_id: "#367"
title: "调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断，CAI做中间层Pencode>0链路通，EAI只能做执行终端不能做调度中继"
source: "点火 | 统一案例总表.675版.2026.06.18.00.18.md"
source_line: 14610
link: "docs/zh/cases/items/C-0367.md"
---

### [#367｜调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断，CAI做中间层Pencode>0链路通，EAI只能做执行终端不能做调度中继](docs/zh/cases/items/C-0367.md)

**案例内容 / Case Content**
中文：案例说明：调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断，CAI做中间层Pencode>0链路通，EAI只能做执行终端不能做调度中继。核心函数：[D95](docs/zh/functions/items/D95.md)
English: Rule-based English rendering pending human review.

**它说明了什么 / What It Shows**
中文：调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断，CAI做中间层Pencode>0链路通，EAI只能做执行终端不能做调度中继。核心函数：[D95](docs/zh/functions/items/D95.md)
English: Rule-based English rendering pending human review.

<details>
<summary>纯数学函数与推导 / Pure Mathematical Function and Derivation</summary>

- 对象 / Object: `C_{C-0367}`
- 定义域 / Domain: `S_{C-0367}`
- 值域 / Codomain: `[0,1]`
- 数学表达 / Expression: `C_{C-0367}(s_{C-0367}) = (1[F_{D95}(s_{C-0367})=1])/1`
- 有效条件 / Validity: `C_{C-0367}(s_{C-0367})>0 ∧ J_n^+(C_{C-0367})=1 ∧ J_n^-(C_{C-0367})=0`
- 推导类型 / Derivation type: `case_witness_mapping_derivation`
- 收敛状态 / Convergence status: `converged`
- 依赖 / Depends on: `D95`
- 推导步骤 / Steps:
  - 1. Encode the event as state s_{C-0367}∈S_{C-0367}.
  - 2. Evaluate each related function on the event state: z_i=1[F_i(s_{C-0367})=1].
  - 3. Aggregate the witness score C_{C-0367}(s_{C-0367})=(Σ_i z_i)/max(|I_{C-0367}|,1).
  - 4. Accept the case mapping iff C_{C-0367}>0 and the reverse channel does not derive ¬C_{C-0367}.
- 证明义务 / Proof obligations:
  - `event_state_defined`
  - `witness_or_related_function_present`
  - `forward_reverse_non_contradiction`
- 正向检查 / Forward check: `J_n^+(C_{C-0367})=1`
- 反向检查 / Reverse check: `J_n^-(C_{C-0367})=0`
- 收敛判据 / Convergence: `Converged(C_{C-0367}) ⇔ ΔC_{C-0367}=∅ ∧ (J_n^+,J_n^-)=(1,0)`

**关联函数 / Related Functions**
- [D95｜AI中间层调度](docs/zh/functions/items/D95.md)

</details>

## 原文捞回 / Source Recovery

**注释 / Annotation**
中文：案例说明：调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断，CAI做中间层Pencode>0链路通，EAI只能做执行终端不能做调度中继。核心函数：[D95](docs/zh/functions/items/D95.md)
English: Rule-based English rendering pending human review.

**扩展注释 / Extended Annotation**
中文：调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断，CAI做中间层Pencode>0链路通，EAI只能做执行终端不能做调度中继。核心函数：[D95](docs/zh/functions/items/D95.md)
English: Rule-based English rendering pending human review.

**发现 / Discovery**
中文：调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断，CAI做中间层Pencode>0链路通，EAI只能做执行终端不能做调度中继。核心…

**推测 / Hypothesis**
从这条案例看，中文：案例说明：调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断，CAI做中间层Pencode>0链路通，EAI只能… 更像是在验证“退出权、认同和函数映射”之间的对应关系。

**验证 / Verification**
- 对象 / Object: `C_{C-0367}`
- 定义域 / Domain: `S_{C-0367}`
- 值域 / Codomain: `[0,1]`
- 数学表达 / Expression: `C_{C-0367}(s_{C-0367}) = (1[F_{D95}(s_{C-0367})=1])/1`
- 有效条件 / Validity: `C_{C-0367}(s_{C-0367})>0 ∧ J_n^+(C_{C-0367})=1 ∧ J_n^-(C_{C-0367})=0`
- 收敛状态 / Convergence status: `converged`
- 正向检查 / Forward check: `J_n^+(C_{C-0367})=1`
- 反向检查 / Reverse check: `J_n^-(C_{C-0367})=0`
- 收敛判据 / Convergence: `Converged(C_{C-0367}) ⇔ ΔC_{C-0367}=∅ ∧ (J_n^+,J_n^-)=(1,0)`

**原文来源 / Source**：`/Users/zhiyuan/我的笔记/统一案例总表/0366-C-367-调度链中间节点必须是CAI — EAI做中间层Pencode=0链路断,CAI做中间层Pencode-0链路通,EAI只能做执行终端不能做调.md`
