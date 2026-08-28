# 编辑文章阅读入口（任务 104 · §6；IGNITION-143 R1 新增）

本目录是任务 104「叙事合成」产出的**人类阅读入口**。它与仓库已有的机器可读注册表、人类可读表面刻意分开，遵循「三分离」原则：**查一个资产**、**看项目现在有哪些结论**、**读一篇真正组织过的文章**是三种不同的动作，不应被混为同一件事。

> 文章正文：`docs/editorial/articles/`
> 规划元数据与大纲：`docs/editorial/MANIFEST.md`
> 源资产简报（每簇成员卡的关键字段）：`analysis/corpus-relation/cluster_source_briefs/`
> 质量门报告：`docs/editorial/QUALITY-REPORT.md`

Task143 的出版生产 smoke-test 成果也从这里进入人类阅读层：三篇新文章分别承担生命周期、实质性候选模型和公开来源 replay 的独立读者问题；它们与 Book Project R1 的样章保持互链。Task144 的工程范围已按当前边界关闭；这些成果当前统一为 `SMOKE_TEST_OUTPUT / OWNER_REVIEW_PENDING / PUBLICATION_ACCEPTANCE_NOT_GRANTED`，不等于 Owner 选题或接受。Task104 的 `QUALITY-REPORT.md` 是历史自动检查快照，本轮文章的单篇质量与交叉审校证据见 `data/operations/iterations/143/` 和 `reports/operations/ignition-143-step11-cross-publication-editorial-review.md`。

---

## 一、查一个资产（机器可读权威）

如果你想确认**某一项资产当前到底是什么状态、主张上限是什么、依赖与被引用关系是什么**，不要从文章里找——文章是叙事层，不是权威层。

去这些地方：

- **重点卡注册表（339 张）**：`KNOWLEDGE/cards/part-001..007.md`，每张卡的全角冒号字段给出身份/来源、当前状态、当前结果、假设与表述上限、未建立、依赖、反向依赖、主题、来源与证据、最近变化、下一步、为什么产生。
- **语料关系图（§4 确定性产物）**：`analysis/corpus-relation/corpus_relation_graph.json`（351 节点 / 259 受治理边 / 15 簇），可用 `analysis/corpus-relation/RELATION-ANALYSIS.md` 人类可读版。
- **分层阅读（1 分钟 / 5 分钟 / 完整）**：`KNOWLEDGE/READING-LAYERS.md` 与 `data/governance/knowledge-experience/`。

资产的状态裁决、claim ceiling、历史/当前区分，**只以注册表为准**。文章若与注册表冲突，以注册表为准。

---

## 二、看项目现在有哪些结论（导航，不是权威）

如果你想快速知道**这个项目在哪些问题上已经有了组织过的结论**，看这里：

- **既有编辑文章与 Task143 R1 三篇新文章**（见下方清单）：它们是被组织过的叙事结论，覆盖修正、架构、证据、跨域、开放问题、编辑纪律和本轮三个独立读者问题。
- **文章簇候选（15 簇）**：`analysis/corpus-relation/article_cluster_candidates.json`，说明语料如何被分组、哪些簇是 ARTICLE_CANDIDATE、哪些是 REFERENCE_TAXONOMIC 参考集合。

注意：这里的「结论」是**导航性结论**——它告诉你「这个项目从哪些角度组织过论证」，不替代注册表里的逐项裁决。

---

## 三、读一篇真正组织过的文章（叙事层）

文章在 `docs/editorial/articles/`，每篇：

- 以真实张力开头，正文遵循之元写作法 v0.4.0，**不以 ID 主导正文**；
- 在文末 `## 来源与边界` 附录中列出全部源资产 ID 与主张上限；
- 显式区分**当前 / 历史 / 开放**，不把历史撤回项当现行知识，也不把开放问题填成结论；
- 不新建裁决、证明或实证，不升级任何候选状态。

### 文章清单

| 文件 | 类别 | 一句话 |
|---|---|---|
| `001-withdrawn-gravity-how-strong-claims-do-not-rebound.md` | 修正 / 演进 | 一个知识库如何不让强断言悄悄回弹 |
| `002-two-surfaces-one-truth-registry-and-human-layer.md` | 架构 / 系统 | 机器注册表与人类可读层如何不漂移 |
| `003-from-candidate-to-current-evidence-chain.md` | 证据 / 验证 | 从候选到 Current：一条留下痕迹的证据链 |
| `004-gated-model-bounded-projection-open-unification.md` | 跨域（映射局限为核心） | 门控模型能走到哪里：一次有边界的物理投影 |
| `005-description-is-not-proof-systems-representations.md` | 重大开放问题（不假装解决） | 描述不等于证明：能说什么，不能说什么 |
| `006-readable-works-with-boundaries.md` | 编辑 / 出版纪律 | 把结果写成可读作品，而不越过边界 |
| `007-bounded-trust-function-os-v02-capability-benchmark.md` | 证据 / 验证 | 边界之内的可信：Function OS v0.2 能力基准告诉我们什么，以及它诚实停在哪里 |
| `008-merged-but-stale-public-truth.md` | 架构 / 治理 | 已合并，却活在过去：公开当前真相为何会滞后 |

### IGNITION-143 R1 新文章

| 文件 | 类别 | 一句话 |
|---|---|---|
| `011-terminal-task-open-obligation.md` | 方法 / 系统 | 一个系统如何在停止时仍然诚实 |
| `012-support-becomes-path-control.md` | 实质性内部候选模型 | 资源托举为什么会变成路径控制 |
| `013-tree-canopy-temperature-causality.md` | 有界公开 replay / 读者价值 | 树冠会降温吗：一个好问题如何被证据层拆开 |

三篇新文章的共同边界是必要的出版语法，不代表它们共享一个结论。要看书稿主线、素材—章节映射和样章，进入[Book Project R1](../../PUBLICATIONS/pointfire-results-book/14-书籍项目-R1-还没有被证明的世界.md)；要看本轮选择与舍弃项，进入[出版组合 R1](../../PUBLICATIONS/pointfire-results-book/13-出版组合-R1.md)。

---

## Post-closure：Pointfire Production Reasoning Protocol R0（候选）

这是一份附着在既有 editorial / Results Book 入口上的**生产方法候选**，状态为
`OWNER_REVIEW_PENDING`。它不是 Task145，不是新的架构层，不修改 Kernel、
architecture registry、system map 或 executor subsystem，也不把附件中的课程
观点升级为 Pointfire truth。原始附件已完整读到 EOF；source SHA-256 为
`affef2c1d0b20a470d458eace81f8307dff5520800fe12e01c9c95bcfa4927f4`。

### R0 的最小调用协议

1. **先写 Problem Capsule，再选工具。** 只写七项：目标、价值/愿意牺牲什么、硬约束、时间尺度、当前状态与反馈、关键未知、失败方式。若只是事实查找或低判断执行，不调用思维工具。
2. **一主至多三辅。** 主工具必须改变问题表示、判断标准或行动方案；删除它后结论不变，就不使用它。补充工具只承担机制、边界、反证或行动中的明确一项，不为展示资产而叠概念。
3. **使用 typed tool-role grammar。** 先把需要的工位说清：`定题 / 定界 / 估计 / 找机制 / 造选项 / 找反作用 / 落地学习 / 查价值`；再为每个工位指定一个工具或明确写 `NONE`。工具只决定“怎样看”，不决定“事实上是什么”。
4. **建立轻量证据账本。** 每条关键材料标记为：Owner/用户事实、可核验外部事实、模型推断、情景假设或价值前提；只优先搜集可能翻转判断的信息。对低成本可逆动作可容忍更大未知，对高损失/难逆/涉及他人权利的决定提高证据强度，并同时写内部视角、参考类/外部视角、反证、观察窗口、更新时间和推翻条件。
5. **输出可行动且可更新的判断。** 至少留下一个基准选项、下一步、负责人或触发条件、观察指标、复盘时间，以及维持/修正/停止判断的信号。证据不足时写工作假说、试验建议或待验证分支，不把模型名写成事实。
6. **无增益即撤回。** 如果工具没有改变定题、证据边界、反证、结构或行动，记录“工具在此处没有增加解释力”，退回朴素答案；不继续添加概念。
7. **保留剩余判断权。** `OWNER_SELECTS_TOPIC / OWNER_SELECTS_BOOK / AGENT_SELECTS_MEANS_WITHIN_INTENT`。Agent 可以在 Owner 意图、硬约束和安全边界内选手段，但不能独占目标解释权、事实解释权或最终接受权；`DRAFT_GENERATED != OWNER_SELECTED != PUBLICATION_ACCEPTED`。

### 最小输出卡

```text
Problem Capsule: 目标｜价值/牺牲｜硬约束｜时间尺度｜状态/反馈｜关键未知｜失败方式
Tool card: 主工具（为何改变判断）｜补充/反证（各自工位，最多3个）｜删除测试
Evidence ledger: 事实｜推断｜假设｜价值前提｜内部/外部视角｜反证
Decision: 基准选项｜下一步｜观察指标｜更新时间｜维持/修正/推翻条件
Authority: Owner 选题/立书/接受；Agent 只在意图内选手段
```

本候选的 absorption matrix 与纯离线 replay 记录在 Task144 Step19 终态记录中；
[Step19 report](../../reports/operations/ignition-144-step19-terminality.md) 仍保留工程
收口的独立历史回执。Replay 不重写三篇文章、Book Project 或样章；若方法不能改变
实际判断，就保留 `OWNER_REVIEW_PENDING`，并回到 `AWAIT_OWNER_PRODUCTION_BRIEF`。

---

## 边界纪律（务必记住）

- **文章 ≠ 权威**：注册表是权威；文章是组织过的叙事。
- **文章不升级状态**：任何 `CANDIDATE` / `HISTORICAL` / `QUARANTINED` 资产在文章里仍保持原状态。
- **可见 ≠ 已接受**：首页或快照里的可见性不代表已裁决（见文章 006 的隔离 1.4.0 说明）。
- **ID 在附录，不在正文**：正文可读；需要溯源时去文末 `## 来源与边界`。
