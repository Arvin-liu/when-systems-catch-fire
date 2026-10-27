# Chapter 05 Evidence Binder：Function OS 的能力边界与真实缺陷

## 章节核心问题

把函数写成声明、解析、执行、验证和回归管线，能不能让研究系统更可靠？Function OS 的价值不在于它终于成为一个无所不能的操作系统，而在于它在一个很小的声明域里暴露了“机器到底做了什么、哪里做错了、修复后能说到哪里”。

## 可支持的认识

1. `function-os-candidate/v0.2/README.md` 将 Function OS 定义为 v0.2.1rc0 候选参考实现，N1–N9 管线服务于符号、确定性、顺序组合的有限域。
2. scope contract 明确 non-goals：神经权重、概率函数、自动发现、分布式执行、生产沙箱和外部真理。
3. benchmark 预注册包含 479 cases：S1 398、S2 62、S3 19，7 个 claim 和独立 oracle；原始版本和修复版本分开。
4. 原始 runner semantic agreement 为 0.9372，25 false reject、0 false accept、0 registry contamination；失败集中暴露了 nested equality split bug。
5. 修复 `split('==',1)` 后，修复目标在该 bounded domain 达到 1.0，并保留 raw failure 和 regression fixture。
6. 外部 Function OS 文献研究只对部分表示/规范化/验证方向提供支持；不能把候选实现写成已有通用范式的完成体。

## 不可支持的强说法

* 不能说 Function OS 已经是完整操作系统或通用函数解释器。
* 不能说 bounded benchmark 代表所有函数、所有领域或现实系统。
* 不能说修复后的 1.0 消除了实现不可靠性。
* 不能说代码通过证明了函数的现实因果意义。
* 不能说外部文献 84/30 张卡片证明了九节点架构。

## 来源与提交

* `function-os-candidate/v0.2/README.md`、`scope-contract.json` — 固定基线 `9b15d359c54694d851c38df6ab3c7ae42544a51b`。
* Function OS benchmark preregistration/run artifacts — 固定基线。
* 原始目标提交 `16f64004`；修复目标 `1314ba80`、`46471183`，只作为 benchmark 版本来源，不改变出版基线。
* `reports/external-research/105-function-os-benchmark.md`、`121-function-paradigm-fulltext-review-report.md`。

## 相互冲突的历史版本

|版本|实际证据|当前处理|
|---|---|---|
|候选 README 的能力叙事|声明了清楚的有限 scope|保留为 candidate contract|
|原始 benchmark|0.9372、25 false reject|保留为真实失败|
|修复 benchmark|bounded semantic agreement 1.0|只支持修复版本/样本/域|
|外部文献回收|表示层较强，规范和验证部分/缺口|不升级为“已有通用系统”|

## 关键数字

* 479 cases / 7 claims / 3 slices。
* 原始：agreement 0.9372；false reject 25；false accept 0；contamination 0。
* 修复：bounded target agreement 1.0；原始失败保留。
* 外部文献第一轮：84 sources、10 families、0 fulltext、17 abstract reviewed；后续全文卡 30 张，claim support 均为 partial。

## 反例

* 一个 parser 把嵌套等式截断，仍可能在简单样本上通过；因此不能只看平均准确率。
* 同一个符号函数换成概率或神经实现后，原有 oracle 可能不再定义。
* 一个函数在声明域内输出正确，不说明它在未声明输入域、并发或外部系统中安全。

## 开放问题

* 如何给概率、连续、神经和分布式函数定义可独立审查的 oracle？
* 如何避免 benchmark 过度贴合实现而失去独立性？
* 如何把外部文献中的 function paradigm 与本候选实现进行严格而非词汇式比较？
* 真实失败案例需要怎样的 target schema 才能进入执行管线？

## Claim ceiling

可以支持“在声明的符号确定性、顺序组合、有限输入域内，Function OS 有一条可运行并能暴露实现缺陷的候选管线；某一 parser 修复在预注册 benchmark 中通过”。不能支持通用 OS、神经/概率扩展、生产安全或现实机制。最高为 `implementation_observed`/`supported_within_bounded_domain`。

## 可进入正文的材料

本章应写一个 nested equality 失败：简单例子都通过，但更深的表达式被错误切分，于是系统“看起来会做”却在边界处拒绝正确答案。修复后 1.0 不是凯旋，而是一个更小、更诚实的句子。通过这一例，读者能理解为什么失败样本、oracle 和 scope 比单一成功率重要。

## 只能放附录的工程信息

N1–N9 节点全表、case ID、runner 命令、hash、fixture 内容、每个 false reject 的日志和外部来源家族表放附录。正文只保留输入/输出形状、缺陷机制和边界。
