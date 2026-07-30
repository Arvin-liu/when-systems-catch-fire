---
kind: "editorial-article"
cluster: "C004"
category: "evidence-validation"
title: "从候选到 Current：一条留下痕迹的证据链"
central_question: "候选、验证、合并和 Current 怎样分离并留下可复算证据？"
source_class: "ignition_increment"
maturity_note: "本文是受治理的叙事层；不提高任何结果的 claim ceiling。"
---

# 从候选到 Current：一条留下痕迹的证据链

一句话结论很容易说："这个发现通过了。"但在点火里，"通过"至少可能是四种不同的状态——它是**候选（candidate）**、是**本地验证通过**、是**已合并（merged）**，还是**当前（Current）**？把这四个状态压成一个词"done"，正是本地验证悄悄变成"关于现实的断言"的入口。

## 为什么这条链值得被写清楚

一个结果如果在某台机器上跑绿了，就被当成"已经成立"，那么它声称的就不只是"代码正确"，而是"外部真相已被确认"。项目把这几环拆开，正是为了挡住这种滑动：实现完成不等于仓库同步完成，仓库同步完成不等于外部同步完成，本地验证也永远不证明任何未登记的实时外部状态。

## 候选不等于结论

任务 102 把恢复的结果/文章来源生成统一卡片与 1 分钟、5 分钟、完整三档阅读；对全部函数/断言 registry 建立可回链来源、状态、依赖、反向依赖和历史的分片搜索索引。但这些"已恢复"的条目，很多仍是 `SOURCE_INDEXED_WITHOUT_LIFECYCLE_INFERENCE` 或 `CANDIDATE_OR_PENDING_SOURCE`——它们被索引，不代表被裁决。

显式的边界写在好几处：本轮迭代**不**深入审查全部 2,033 个发现项、不证明 census 在受追踪文本 Git 源之外穷尽、不验证物理理论、不解决物理"乌云"、不统一四力、不证明统一可能或不可能。能说"已被发现"，不等于能说"已被证明"。

## 验证是分开的一跳

`121Q9 Global Validation` 的状态是 "PASS locally for cumulative release candidate Step 003"——关键词是 *locally* 与 *candidate*。它通过的是累积发布候选在本地的一致性，不是对外部世界的任何主张。

验证工具的能力也被明确框住：它只判断已声明约束是否满足，**不输出"理论是真的"**。强断言门禁（THEOREM/AXIOM/ISOMORPHISM/CAUSAL/PROVED 等受控术语）保证：缺定义、缺证明、缺结构保持时，必须降级并记录 unresolved blocker。

## 人类可见性门禁：机器结果必须有人的对应物

项目要求每个机器结果都有人类对应物，并且检查：两步可达导航、过期状态、默认隐藏的重要内容、断链。机器对应物落在 `data/governance/human-results/` 与 `data/governance/self-correction/` 两层；CI 同时检查两层，缺任一层即失败。

这条规矩针对的是一种常见故障：机器侧"绿了"，但人类侧没有可发现、可两步到达、未过期的对应物——于是结论存在，却对读者隐形。可见性门禁把"能被人读到"变成硬要求，而不是善意假设。

## 合并与当前：最后的、也是最容易伪造的两环

普通合并（ordinary merge）前要求 **exact-head 审查**：被合并的 head 与审查通过的 head 必须逐字节一致。阶段快照或首页可见性**绝不隐含** Accepted、Current、Activated、能力可用或候选载荷合并——快照只是快照。

更有意思的是"有意义的知识变更必须重生成"这条：任务 102 的 What's New、主题地图、资产卡、阅读层、别名/取代、全量搜索、双向依赖投影，都要随变更重算。但这些发现表面**永远不覆盖** canonical registry 或证据成熟度。它们是导航与保真摘要，不是新的裁决。

## 这条链的价值在于留下痕迹

回到开头那四个状态。链的意义不是把"done"推得更快，而是让每一步都留下可复算的证据：候选有索引、验证有本地一致性记录、合并有 exact-head、当前有人类可见对应物。哪一步断了，CI 就红，而不是让一个被截断的结论流入读者。

"done"是这条链的最后一环，不是第一环。把链拉直、把环补齐，比任何一次"通过"都更接近诚实。

---

## 来源与边界

- 验证与发布：`reports/release/121Q9-global-validation.md`、`reports/foundation-architecture/101-human-readable-surfaces-self-correction-closeout.md`、`outputs/collisions/20260711-disobedience-subjectivity/independent-second-angle-audit-056.md`、`reports/external-research/104-dual-088-reconciliation.md`。
- 门禁与机器对应物：`RESULTS/README.md`、`README.md`、`llms.txt`、`docs/operations/stage-snapshot-publication.md`、`data/operations/stage-snapshots.json`。
- 非函数断言（边界约定）：`NFC-2F6931FFF5A6554C`（人类可见性门禁）、`NFC-A5870D6C2E430817`（机器对应物位置 + CI 双检）、`NFC-C349FBD C470B50AB`（有意义变更必须重生成发现表面）、`NFC-6122E6F96EFE210E`（快照/可见性不隐含 Current）、`NFC-6CA935CA1A4F2A8E`、`NFC-70A1EC2C42864627`、`NFC-2B7304F480DA70C2`、`NFC-A6B80FCA608C8C8F`、`NFC-996C4E8631D40356`。

**主张上限**：导航与叙事层；不声称任何物理理论被验证、不声称 census 穷尽、不声称外部同步完成。
