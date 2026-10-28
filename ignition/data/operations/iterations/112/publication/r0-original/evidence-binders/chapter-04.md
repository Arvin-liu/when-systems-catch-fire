# Chapter 04 Evidence Binder：函数与断言治理发现了什么

## 章节核心问题

当一个跨域研究系统积累了几千个函数和断言时，真正的问题不是“怎样再加更多”，而是“一个对象究竟是什么、证据在哪里、现在能不能说、被纠正后如何不回流”。本章解释 Foundation 的注册表、身份、处置和谱系是怎样把知识资产从一堆名字变成可审计对象的。

## 可支持的认识

1. Foundation 将函数、关系、约束、评分、启发式、结构隐喻、候选和未决身份分开，而不是把所有带等号的内容当函数。
2. `data/foundation/function-assets/closure-summary.json` 在固定基线记录 7,051 canonical identity cards、4,978 explicit quarantine/pending；分布中有 4,364 unresolved identity、2,147 algorithm/workflow、122 conjecture/research candidate 等多种身份。
3. `data/foundation/nonfunction-claims/closure-summary.json` 记录 17,626 canonical claims、5,801 explicit quarantine/pending，且把 theorem、mechanism/causal、empirical、metaphysical、normative 等类别分开。
4. E0/E1、math maturity、disposition 和 public surface records 提供了“从哪里来、现在如何处置、能否公开”的不同维度。
5. `reports/foundation-architecture/100-nonfunction-claim-evidence-lineage-closure.md` 明确指出，注册表闭合不代表真理、新颖性、同行评议或复制。
6. 发现覆盖报告让来源文件、候选片段、卡片和未能处理的公式图片限制可见。

## 不可支持的强说法

* 不能说 7,051 个身份卡就是 7,051 个有效函数。
* 不能说 17,626 个 canonical claims 就是 17,626 个新知识。
* 不能说明确分类意味着人类专家已经完成语义裁决。
* 不能说 public violations 为 0 就意味着所有断言都正确。
* 不能说 quarantine 数量越小，研究就越成熟。

## 来源与提交

* `FOUNDATION.md` — 固定基线 `9b15d359c54694d851c38df6ab3c7ae42544a51b`。
* `docs/foundation/historical-function-deep-adjudication-20260729.md` — 任务 099 深度裁决。
* `reports/foundation-architecture/100-nonfunction-claim-evidence-lineage-closure.md` — 任务 100。
* `data/foundation/function-assets/closure-summary.json`、`discovery-coverage.json`。
* `data/foundation/nonfunction-claims/closure-summary.json`、`discovery-coverage.json`。
* `data/foundation/migration-summary.json` — 迁移口径和 tracked files。

## 相互冲突的历史版本

|表面|版本 A|版本 B/纠正|
|---|---|---|
|函数规模|README 的 5,663 canonical identity cards|机器闭合 7,051 cards；统计范围尚未统一|
|断言规模|README 的 17,333 canonical claims|机器闭合 17,626 claims；统计范围尚未统一|
|旧表|617/约 624 个历史文件|7,051 canonical cards；对象层不同|
|closure|“所有对象都已闭合”|按 disposition 闭合，仍有 unresolved/quarantine/pending|

## 关键数字

函数闭合分布包含：`UNRESOLVED_IDENTITY` 4,364、`ALGORITHM_OR_WORKFLOW` 2,147、`CONJECTURE_OR_RESEARCH_CANDIDATE` 122、`RELATION_OR_CONSTRAINT` 227、`QUARANTINE_UNTIL_DEFINED` 4,856；这些是重叠/不同维度的机器分布，不能相加解释为知识等级。非函数断言中 `UNRESOLVED_CLAIM` 5,300、`PENDING_EMPIRICAL_TEST` 985、`HISTORICAL_ONLY` 6,495、`QUARANTINED_AMBIGUOUS` 2,424 等都说明注册表保留了未知。

## 反例

* 一个有规范名字但没有输入/输出/语义的“函数”，应被标成 unresolved 或 quarantine，而不是用名字完成定义。
* 一个被分类为 theorem 的对象若没有 proof artifact，不能因类别名而变成定理。
* 一个 relation card 记录了 A 与 B 的边，不说明 A 对 B 有现实因果。
* 一个撤回断言若只从当前表删除，旧文章仍可使它回流；因此必须保留 correction lineage。

## 开放问题

* 怎样让领域专家快速审阅大规模 unresolved identity，而不是只依赖生成器？
* 怎样为公开数字增加 scope、生成提交、去重规则和快照 ID？
* 如何识别跨文件同名异义和同义重复？
* 何种最低证据才能把一个 candidate 从 quarantine 移到可公开的 research hypothesis？

## Claim ceiling

本章支持的是“点火建立了较细的对象会计和撤回防线”，以及“资产的可见状态被拆成多个维度”。它只到 registry/lineage closure 和局部 schema/coverage 级别，不到函数语义普遍正确、断言真实或研究新颖性。

## 可进入正文的材料

正文不必解释所有字段，而应讲一个对象如何经历“被命名—发现不清楚—进入 quarantine—补来源或改身份—保留未决”的过程。最好同时展示函数和断言的两套数字冲突，让读者明白可见性问题不是小数点，而是科学诚实的一部分。

## 只能放附录的工程信息

完整 disposition/identity/maturity distribution、JSON schema、迁移计数、文件发现规则、公式图片限制、脚本版本和每张卡片 ID 放附录。正文只保留两三个对象的生命线。

