# 解析解数量确认报告 / Analytic Solution Count Report

生成时间: 2026-06-16T15:52:26Z

## 结论

**当前确认解析解数量: 1**

## 检索范围

- ANALYTIC_SOLUTIONS.md
- data/analytic-solutions/unified-analytic-solutions.json
- data/analytic-solutions/unified-analytic-solutions.jsonl
- data/normalized-jsonl/analytic-solutions.jsonl
- data/rebuild/analytic-solution-derivation-report.md
- data/rebuild/analytic-solutions-bootstrap-closure-report.md

## 已确认解析解

- **SOL-0001**: σ_opt=√e解析解
  - 关联函数: T20
  - 公式: σ_opt = √e
  - 来源: docs/zh/analytic-solutions/items/SOL-0001.md
  - 理由: T20函数明确声明 σ_opt=√e 为闭式解析解。该结果经 D307 (σ_opt微观起源函数) 交叉确认：σ_opt 是 dΦ/dσ=0 的根，n→∞ 极限下 σ_opt→√e≈1.649。已验证为单一解析解。

## 需排除的候选

- **ANS-0010** (层级问题是 d=4 稳定性约束的解析解)
  - 类型: new_answer
  - 排除理由: ANS-0010 标题虽含'解析解'，但其 object_class 为 'answer'，属于新答案条目，不纳入解析解表。解析解表只收录具有明确闭式解析表达式(closed-form expression)的函数条目。该条目的回答是定性描述而非闭式解析表达。
  - 处置: not_an_analytic_solution

- **D307** (σ_opt微观起源函数)
  - 类型: function_reference
  - 排除理由: D307 正文提到'精确解：σ_opt是dΦ/dσ=0的根，n→∞极限下σ_opt→√e≈1.649≈1.65。σ_opt=√e不是巧合——是独立性-充分性权衡的解析解。' 但 D307 是完整的函数条目，不是独立的解析解条目。其解析结果与 T20/SOL-0001 指向同一个数学结果 (σ_opt=√e)，不形成独立的第二个解析解。
  - 处置: same_as_SOL-0001

## 说明

经全面检索，当前仓库中仅有一个解析解 (SOL-0001)。D307 正文虽提到'解析解'但指向同一结果；ANS-0010 标题含'解析解'但属于答案条目而非解析解表条目。如果 D307 应升级为独立的解析解条目，或 ANS-0010 应同时加入解析解表，需人工判定。

需人工复核: False
