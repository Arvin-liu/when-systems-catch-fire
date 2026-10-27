# Chapter 07 Evidence Binder：牛顿苹果案例与真实系统失败的边界

## 章节核心问题

一个流传已久的故事能否成为真实系统的失败案例或可执行实验？牛顿苹果案例把两种证据放在同一桌上：历史来源可以支持一个有限的关联叙述，但工程实验需要 target、输入、输出、oracle、重复和回归保护。缺任何一个，都不能把故事变成程序结果。

## 可支持的认识

1. `historical/EVIDENCE_DOSSIER.md` 依据 Stukeley、Conduitt 等后来的回忆来源，支持“牛顿被记载为把落苹果与关于重力的思考联系起来”的 bounded memoir association。
2. 相同来源不能充分支持流行版本中的即时完整理论、苹果作为唯一直接触发、当场完成万有引力理论或全部故事细节。
3. `TARGET_AUDIT.md` 对三个案例（apple_fall、cross_domain、technology_growth）都指出：没有 target commit、明确输入/输出、运行 trace、oracle、重复失败和 regression guard。
4. `case-status.json` 把苹果原始 classification 和 narrative hypothesis 与 `EVIDENCE_PARTIAL_OR_DISPUTED`、`EXECUTABLE_TARGET_ABSENT` 分开。
5. 因此“目标缺失”是当前最硬的工程结论；它不是“程序运行后失败”，也不是“历史故事已被证明虚假”。

## 不可支持的强说法

* 不能说苹果案例已经被 Function OS 执行并失败。
* 不能说苹果是牛顿理论的唯一直接因果触发。
* 不能说 memoir provenance 等于同时代实验记录。
* 不能说没有 target 就能构造一个忠实的历史反事实。
* 不能说这个案例已经证明了“真实系统通常无法形式化”。

## 来源与提交

* `data/operations/iterations/111/historical/EVIDENCE_DOSSIER.md`、`SOURCES.jsonl` — 固定基线 `9b15d359c54694d851c38df6ab3c7ae42544a51b`。
* `data/operations/iterations/111/TARGET_AUDIT.md`、`case-status.json` — 固定基线；关键证据来自任务 111 first-stage artifacts。
* `data/operations/iterations/111/historical/case-source-map.json`（如引用）— 只作来源链，不提升生命周期状态。
* `RESULTS/OPEN-QUESTIONS.md`、`ITERATION.md` — 现实案例 target 和 claim ceiling 边界。

## 相互冲突的历史版本

|版本|证据|当前处理|
|---|---|---|
|通俗故事|苹果落下立即引发完整理论|降级为流行叙事，未证|
|回忆来源|苹果与重力思考相关|保留为 bounded memoir association|
|任务分类|可称 implementation defect 的叙事假设|因 target absent 不提升|
|失败案例期待|运行后会有 error/trace|没有 target，不能执行|

## 关键数字

* 苹果相关来源 dossier 记录 6 条历史来源/来源链记录；来源类型和时间距离决定证据上限。
* 任务 111 case-status 有 3 个案例；苹果、cross-domain、technology_growth 都缺 executable target。
* target gate 要求 executable、commit、exact I/O、trace、run、repeated failure、oracle、claim ceiling、first failure、regression guard；苹果当前至少在这些字段上缺失。

## 反例

* 如果没有程序、输入和 oracle，“没有输出”不能叫执行失败。
* 传记中“据说某事启发某人”可以支持关联叙述，却不能自动支持唯一因果。
* 为了让故事进入 benchmark 而临时编写一个模拟器，得到的是模拟器行为，不是历史事件的复现。

## 开放问题

* 怎样设计历史案例的 target，使它验证的是来源/叙事机制而不是虚构历史？
* 如何把回忆来源、同时代记录、传播史和后见之明分别建模？
* 哪些故事适合做工程失败案例，哪些只能作为公共叙事和研究问题？
* 何时一个 target 的 formalization 足够忠实，足以进行反事实比较？

## Claim ceiling

历史部分最高为 `source_recovered`/`memoir_association`；工程部分是 `executable_target_absent`；不能到 `implementation_observed`、`mechanism_discriminated` 或 `causal_identification`。本出版包不把任务 111 写成正式完成。

## 可进入正文的材料

正文可从一句读者熟悉的苹果故事开始，再慢慢拆开两个问题：来源能支持哪一句，程序需要哪些字段。最有力的转折是发现“我们甚至没有可以运行的目标”。这会把读者从英雄神话带回研究实践，同时不粗暴否定历史人物或传记。

## 只能放附录的工程信息

六条来源 URL、source hash、case JSON 全字段、target audit 的缺失字段表、生命周期枚举和后续候选提交放附录。正文只解释门槛为什么必要。

