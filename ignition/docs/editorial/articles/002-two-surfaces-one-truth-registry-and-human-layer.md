---
kind: "editorial-article"
cluster: "C001"
category: "architecture-system"
title: "两份表面，一个真相：机器注册表与人类可读层如何不漂移"
central_question: "知识资产怎样被登记、裁决、修订、隔离并保持机器与人类表面一致？"
source_class: "ignition_increment"
maturity_note: "本文是受治理的叙事层；不提高任何资产或协议的 claim ceiling。"
---

# 两份表面，一个真相：机器注册表与人类可读层如何不漂移

一个读者可以在十分钟里读完点火的"当前结果""纠正与撤回""开放问题"，然后觉得自己懂了这个项目。但同一份语料底下，是 5,663 张 canonical 身份卡和 17,333 条 canonical 断言，每一张都带着成熟度轴、断言上限、依赖图和最终处置。

两份表面之间的缝隙，就是治理真正发生的地方。

## 为什么这不是"文档同步"的小事

如果机器注册表和人类可读层各说各话，读者继承的就不是结论，而是错误上限。一个资产若在人类摘要里被写成"已统一"，而 registry 里仍是"猜想"，那么十分钟阅读 route 就是在分发一个被悄悄升级过的结论。

所以点不是"把机器内容翻译成人话"，而是"让两种表面永远指向同一份真相，且真相的边界清楚可见"。

## 身份、轴与门：登记不是贴标签

任务 102 在纳入新语料、排除知识体验生成投影的回灌后，重算出上述 5,663 张身份卡与 17,333 条断言。但它们的意义不在数字，而在每张卡背后的结构：

- **十二类主身份**与**十门结果**：函数资产从"这是什么"到"它能 claiming 到哪一步"被显式分类。
- **双成熟度轴 M0—M7 与 E0—E7**：数学成熟度与外部证据成熟度分开打分，避免"看起来很数学"被当成"已被外部验证"。
- **十门 claim 治理**：THEOREM、AXIOM、ISOMORPHISM、CAUSAL、PROVED 等受控术语，缺所需定义、理论、双射、结构保持、干预语义或证明工件时，必须降级。
- **全历史确定性 census 与 anti-rebound 纠偏台账**：任务 98 把候选 census 推进为第一项全量、逐项、可重放的注册表闭合。

闭合的严格含义是：每个发现项都有唯一 canonical 卡、一个主身份、M/E 双轴、来源行锚、证明与实证义务、依赖、十门结果、claim ceiling 和一种最终处置。**闭合不等于所有资产已被证明、验证或外部复现**——它只是会计意义上的闭合：缺定义或证据的项进入显式 quarantine（隔离），而不是被悄悄放行。

## 隔离，而不是模糊

quarantine 是关键机制。一个断言若缺乏定型定义或可核验证明，它不进入"现行知识"，也不被删除——它停在隔离区，等待给出类型化定义、量词、反模型搜索或证明工件。这种"未决即显式"的纪律，比任何漂亮摘要都更能保护读者。

## "当前"是个会被误读的词

项目把几种状态严格分开：**实现完成**、**仓库同步完成**、**外部同步完成**、**项目完成**是不同状态；本地验证永远不证明任何未登记的实时外部真相。

迭代方法 1.4.0 是 Current；1.3.0、1.2.0 及系统图 0.2.0/0.3.0/0.1.0 都是 Historical。阶段快照或首页可见性，**绝不隐含** Accepted、Current、Activated、能力可用或候选载荷合并。把 README 最近三项投影当作完整权威，是交接时明确禁止的越界。

## 撤回之后，名字换了也不算翻案

最容易被忽略的漂移，是"换个标题就当新结论"。项目规定：撤回、降级或隔离的结论，即使换标题、换编号、改成"结构性定理"或藏入摘要，仍受原 supersession lineage 与 claim ceiling 约束。CI 自动检查"大一统不可能性、单模型失败推出普遍不可能、类比冒充同构、量词膨胀、内部测试真值升级"这几类模式。

机器对应物落在 `data/governance/human-results/` 与 `data/governance/self-correction/` 两层；CI 同时检查两层，缺任一层即失败。统一函数总表、统一案例总表是**不可变的历史源与兼容视图**，手写表头不能作为当前计数权威。

## 回到缝隙

所谓"两份表面，一个真相"，真相不是某一份文档，而是让两份表面始终对齐的那套机制：身份卡、双轴、十门、确定性 census、隔离、Historical/Current 区分、lineage 绑定。它的代价是——闭合只是会计闭合，不是证明闭合。这恰恰是诚实：机器和人看到的，永远是被边界框住、而非被许诺撑大的同一份事实。

---

## 来源与边界

- 治理与计数：`RESULTS/ADJUDICATION-SUMMARY.md`、`docs/foundation/historical-function-deep-adjudication-20260729.md`、`reports/foundation-architecture/098-claim-governance-implementation.md`、`reports/foundation-architecture/098-dependency-impact.md`。
- 状态纪律：`llms.txt`、`AI-HANDOFF.md`、`docs/project-current-state.md`、`RESULTS/CORRECTIONS.md`、`docs/discipline_kernel_pilot.md`。
- 人类表面与映射：`HUMAN-READING.md`、`docs/governance/knowledge-experience-layer.md`、`RESULTS/README.md`。
- 非函数断言（边界约定）：`NFC-187E985133669A56`、`NFC-2843222A849FE77E`、`NFC-3D9FFB2206406FCC`、`NFC-517A9B6DE3674E2A`、`NFC-2B7304F480DA70C2`、`NFC-390D533E6AA565C0`、`NFC-6122E6F96EFE210E`、`NFC-6CA935CA1A4F2A8E`、`NFC-70A1EC2C42864627`。

**主张上限**：导航与叙事层，不新建裁决或治理结论；与现行 registry 冲突时以现行资产为准。
