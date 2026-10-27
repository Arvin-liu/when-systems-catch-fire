# Chapter 08 Evidence Binder：点火目前仍不知道什么

## 章节核心问题

一个系统如果能记录很多结构、纠正很多强说法、跑很多本地测试，它还不知道什么？本章拒绝用“未知”做谦虚的装饰，而是把未知拆成真实缺失：没有外部数据、没有全文、没有 target、没有干预、没有领域专家、没有独立复制、没有统一快照。

## 可支持的认识

1. `RESULTS/OPEN-QUESTIONS.md` 保留四种相互作用、量子引力、暗物质/暗能量、宇宙学常数、测量问题等物理开放问题；点火没有给出新物理解答。
2. Function OS 的神经、概率、连续、自动发现、分布式和生产安全能力被 scope contract 明确列为 non-goals 或开放问题。
3. MCF/PSD/ARN 没有提供现实因果识别；它们的验证报告主要落在 deterministic representation、projection、schema、validator 和 bounded workflow。
4. Crossref/OpenAlex 没有全文/claim support；外部文献的部分全文卡仍是 partial。
5. 苹果没有 executable target；这意味着某些“真实案例失败”尚未进入实验层。
6. Foundation 的公开与机器计数未统一，说明连内部知识资产的快照谱系仍有缺口。
7. Q24/Q25/Q32 解决了仓库同步和传播的局部问题，却没有解决现实机制、领域证据或外部复制。

## 不可支持的强说法

* 不能说“点火不知道”意味着这些问题不重要或永远不能解决。
* 不能把候选架构的缺口写成对真实世界的否定。
* 不能用“未来可以研究”替代当前缺失的证据。
* 不能把未知问题数量统计成研究深度。
* 不能说修正了旧结论就已经得到新结论。

## 来源与提交

* `RESULTS/OPEN-QUESTIONS.md` — 基线 `9b15d359c54694d851c38df6ab3c7ae42544a51b`。
* `ITERATION.md` — 当前方法、Q32I、Q33/Q34–Q40 的未启动/边界说明。
* `docs/architecture/*` 及 `reports/architecture/121Q21R`、`121Q22`、`121Q23`。
* `function-os-candidate/v0.2/scope-contract.json`。
* `reports/external-research/104*`、`110*`、`120*`、`121*`。
* `data/operations/iterations/111/TARGET_AUDIT.md`、`data/foundation/*/closure-summary.json`。

## 相互冲突的历史版本

|看起来像答案|证据实际留下的未知|
|---|---|
|候选架构解释了跨域因果|只提供表示、路径、投影和 validator 边界|
|大量来源说明文献支持|metadata、abstract、fulltext、claim support 层级不同|
|任务闭合说明问题已解决|若是工程/治理闭合，现实问题仍 open|
|苹果有一个清楚的故事|target、反事实和同时代证据仍不足|
|计数完整说明知识资产完整|两组公共/机器快照未统一|

## 关键数字

* OpenAlex 7 null、8 partial；Crossref 0 fulltext、0 claim support。
* Function OS 外部文献：30 张 fulltext cards 的 claim support 仍为 partial；10 个家族和 5 个能力缺口没有被完全填补。
* Foundation machine closure 与 public surface 的函数/断言数字各有两组。
* Q32 的 48 seeds、2 iterations、zero residue 仅定义了某次局部传播运行的覆盖范围。

## 反例

* 一个系统能列出所有未知问题，不代表它已经拥有解决这些问题的方法。
* 一张地图没有孤立节点，不代表现实世界没有未知依赖。
* 一个模型可以在内部自洽，但替代模型也能解释同一历史叙事。

## 开放问题

本章本身的开放问题至少包括：真实干预如何设计；严格跨域映射如何定义；Function OS 如何扩展到非符号函数；外部全文和领域专家如何进入；真实失败案例如何获得 target；公共数字如何统一；读者反馈如何避免循环证明；候选机制如何与替代机制竞争。

## Claim ceiling

本章可支持的是“未知已被具体化并可定位”，达到 `open_question`、`causal_identification_pending`、`insufficient_evidence` 和部分 `visibility_gap_audited`。它不支持“未知已被解释”或“开放问题已经被系统解决”。

## 可进入正文的材料

正文可以把“仍不知道”写成一条下降的阶梯：不知道世界机制；不知道外部来源内容；不知道一个案例能否执行；甚至不知道公开数字为什么不一致。让读者看到，诚实的未知会阻止系统把自己的内部秩序误认为世界秩序。

## 只能放附录的工程信息

完整 open question ID、未启动 Q 编号、源文件统计、coverage matrix、字段缺失表和每个 API null 的技术分类放附录。正文只保留会改变研究判断的缺口。

