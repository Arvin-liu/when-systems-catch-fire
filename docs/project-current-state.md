# 点火项目现状

更新时间：2026-08-02。当前状态包含任务 98—103 的断言/函数治理、证据程序与人类可读知识表面，任务 104 的编辑叙事层与语料关系分析，任务 105 的 Function OS v0.2 有界能力基准，任务 110 的完成状态与 OpenAlex 书目复制，任务 111 的失败案例证据门禁与恢复终态，以及任务 112 的百轮成果出版层。本段描述正式仓库当前接口；出版层的研究结论仍受各自来源、版本和证据上限约束。

## Task 112 current publication layer

任务 112 把既有百轮材料整理为可连续阅读的前台成果，而不是继续扩张模块。入口是[成果书架](../PUBLICATIONS/README.md)，其下可直接到达[一页全景](../PUBLICATIONS/what-pointfire-knows-now.md)、[完整第一卷](../PUBLICATIONS/volumes/001-pointfire-after-one-hundred-iterations.md)、[研究笔记第一辑](../PUBLICATIONS/notes/001-pointfire-research-notes.md)和[百轮成果台账](../PUBLICATIONS/hundred-iteration-achievement-ledger.md)。出版层明确区分研究成果、纠正成果、有限实验、形式化、方法、基础设施、维护和开放问题，不把记录数或文件数当作知识总量。

任务 112 的正式证据与来源包位于 `data/operations/iterations/112/publication/`：其中保存 R0 不可变 intake、覆盖/主张/笔记独立性/读者审计、修订决定、三重出版审查、manifest 和未解决义务。R0 以固定基线保存；任务 111 的正式 `TERMINAL_SUCCESS` recovery-1 状态单独作为项目生命周期事实，不能被写成新的科学发现。仓库 Markdown 仍是持续维护的人类阅读层；本出版层没有复活已退出的独立阅读站。

## 当前形态

点火是一个仓库原生、版本化、证据可追溯、对象有类型、推断可检查、结论可降级的跨领域研究与行动基础设施原型。这个描述只绑定当前提交，不是永久项目身份。

现行组织包括 L0—L6 架构、Foundation registries、Function OS 候选、MCF、PSD、ARN、效果与机制平面、注意力/分布/压缩控制、地图集、迭代与同步系统、生命共同体价值宪章、Charter System R1、之元写作法和现实反馈入口。

## 当前已实现能力

- 保存来源、命题、形式对象、论证、证据、证明义务、反例、验证和迁移历史。
- 对任务 102 排除生成投影回灌后重算的 5,663 个历史函数资产建立 identity card、M/E 双轴、义务、依赖、处置与 quarantine。
- 对同次重算的 17,333 个非函数断言建立类别、来源、证据谱系、十三道门禁、依赖、M/E、处置与公开表述上限。
- 自动发现本轮知识资产变化并生成 Claim Delta、影响分析、证据谱系变化、审计发现和整改计划。
- 检测证明/实证义务、跨域越界、量词膨胀、循环论证、类比冒充同构、单模型失败推出普遍不可能和撤回结论回弹。
- 检查机器记录与人类结果成对存在、README 两次点击可达、重要内容不被默认折叠、当前状态不残留退役阅读面。
- 通过 Git 历史、supersession lineage 与追加式历史记录保留撤回、降级、隔离和修订过程。
- 从统一入口按时间、研究问题、自然语言词、旧称和阅读时长探索知识，不要求读者预知目录或资产编号。
- 为全部恢复的结果/文章来源生成统一卡片和 1 分钟、5 分钟、完整阅读，并为全部函数/断言 registry 建立可回链来源、状态、依赖、反向依赖和历史的分片搜索索引。

## 当前人类阅读面

GitHub 仓库 Markdown 是唯一持续维护的人类阅读层：

- [统一知识入口](../KNOWLEDGE/README.md)
- [最新变化](../KNOWLEDGE/WHATS-NEW.md)
- [知识地图](../KNOWLEDGE/MAP.md)
- [搜索与交叉引用](../KNOWLEDGE/SEARCH.md)
- [统一资产卡](../KNOWLEDGE/ASSET-CARDS.md)
- [分层阅读](../KNOWLEDGE/READING-LAYERS.md)
- [README](../README.md)
- [人类阅读总入口](../HUMAN-READING.md)
- [RESULTS](../RESULTS/README.md)
- [当前结果](../RESULTS/LATEST.md)
- [纠正与撤回](../RESULTS/CORRECTIONS.md)
- [开放问题](../RESULTS/OPEN-QUESTIONS.md)
- [裁决总结](../RESULTS/ADJUDICATION-SUMMARY.md)
- [研究与文章](../RESULTS/RESEARCH-AND-ARTICLES.md)

此前独立部署的阅读站已退出产品与同步面，独有系统图迁移到 [仓库内 SVG](./generated/ignition-system-map.svg)。历史部署证据仍留在 Git 与旧报告，不再构成当前完成门禁。

## 当前治理结论

- registry closure 表示每项有处置或明确 quarantine，不表示全部命题成立。
- 数学成熟度和外部证据成熟度独立；任何一轴不能替代另一轴。
- 自动提取、分类、依赖计算和 CI 只提供仓库范围证据，不裁决外部现实。
- 当前门控乘积模型没有统一四种基本相互作用；物理统一问题保持开放。
- 点火没有证明“大一统普遍不可能”。模型失败、哥德尔类比、跨域相似或旧编号不能充当普遍 no-go theorem。
- 系统图和传播闭包是导航/仓库关系，不是现实因果、严格同构或项目完备性证明。
- 生命共同体价值宪章是规范边界，不是事实、数学或授权证据。

## 当前限制与开放义务

- 函数资产中 3,887 项仍 quarantine/pending；非函数断言中 5,581 项仍 quarantine/pending。
- 大量资产仍缺精确定义、类型、量纲、证明、反例、外部来源、数据或复现。
- MCF、PSD、ARN、Function OS 与现实使用效用尚需独立证据和失败条件。
- 四力统一、量子引力、暗物质、暗能量、宇宙常数和测量问题没有被本项目解决。
- 自动审计是启发式门禁；它可以发现风险和阻断已知回弹，但不能替代专家裁决、同行评审或实验。
- 主题分类、重要性规则和自动摘要只建立导航；machine-only 不表示资产不重要、错误或已被删除。

## Task 110 current-state addition

任务 110 将 planner 的完成状态与 Evidence Program 生命周期连接起来：任务 109 的
原始 C-01 推荐被保留为历史缺陷，C-01/task 103 与 C-04/task 105 被登记为已完成并从
active queue 排除；同一冻结评分模型的 task-110 projection 保留 C-03 作为已执行的
OpenAlex 独立元数据复制。首轮主分母为 116：101 supported、8 partial、7 null、0
contradicted、0 invalid。

当前结论的上限仍是跨源书目元数据一致性。OpenAlex 结果不验证论文内容、科学真理、
Pointfire 物理、MCF、PSD、ARN、现实因果或任何成熟度/处置提升。生命周期事实由候选
事件、内容合并、终端化投影、annotated tag 和全新克隆 resolver 分层确认；不以旧候选
标签自动生成下一任务。

## Task 111 current-state addition

任务 111 对 `case_failures/` 的三项原始 `IMPLEMENTATION_DEFECT` 分类做证据门禁，而不把
目录存在或“系统可能会输出”当作缺陷复现。苹果案例经 Stukeley、Conduitt 和 Newton
Project 材料复核，外部证据仅为 `EVIDENCE_PARTIAL_OR_DISPUTED`；Function OS v0.1/v0.2
没有该历史因果命题的可执行接口，故 target 为 `EXECUTABLE_TARGET_ABSENT`、形式化为
`FORMALIZATION_UNDERSPECIFIED`、复现为 `NO_REPRODUCTION_POSSIBLE_WITH_CURRENT_TARGET`。

任务 111 新增的 fail-closed gate 只接受绑定完整 repository executable commit、精确
输入/输出、trace、run、重复失败、oracle、claim ceiling、保留首次失败和 regression
guard 的 `REPRODUCED_IMPLEMENTATION_DEFECT`。三项历史案例仍可检索，但不再以已知缺陷
进入 active queue；C-03 则按 task-110 的权威 OpenAlex result 保持 `COMPLETED_PARTIAL`
并排除。该门禁提升记录资格与可复现性，不提升历史故事、点火物理或 Function OS 的外部
真理等级，不创建 task 112。

## 当前操作法

Iteration Method `1.4.0` 仍是当前仓库操作法。任务 101 增加机器/人类双输出；任务 102 进一步要求有意义的知识变化声明人类目的地、What's New、主题、资产卡、分层阅读（适用时）、别名/supersession、来源和双向依赖。缺失、断链、断锚、过期、隐藏、无来源摘要或回弹时，CI 失败。

候选、Ready、Accepted、Merged、Current 和 Closed 仍是不同状态。普通合并、main 验证、远端 CI 与全新克隆复验都必须分别记录；仓库没有需要继续维护的独立阅读站生产门。

## 证据程序（Task 103）

任务 103 建立了最小可用 Evidence Program 并完成首个预注册、可证伪验证试点，使重要断言开始接受外部现实检验：

- **最小基建：** `evidence-program/`（候选组合 schema、预注册 schema、来源溯源 manifest、运行 manifest、结果裁定 schema、偏差日志 schema、E 轴转移 schema + 确定性校验器 + CI 门）。每个字段/校验器都被真实试点或回归固件触发。
- **首个试点：** 用公共 Crossref REST API 独立复验 `data/external-research/104-source-registry.jsonl` 中 117 条 `crossref_verified: true` 来源的 DOI。结果 **SUPPORTED_WITHIN_SCOPE**（117/117 解析、117/117 标题匹配、117/117 年份匹配、0 撤稿；1 条注册表内部重复 DOI 判定为有意跨 gap 引用，已保留并移交 104 数据负责人）。
- **预注册先于结果：** 协议提交于 `a4d13a69…`，早于任何 Crossref 查询；校验器强制“预注册提交是结果提交的祖先、无事后阈值替换、来源溯源完整、无未登记指标”。
- **处置：** 确认 `evidence_tier_104 = METADATA_VERIFIED` 不变；RUN-1 发现的 5 条 `crossref_year` 缺口已回填/修正并复跑验证（year_match=117/117），重复 DOI 判定为有意跨 gap 引用已保留（移交 104 数据负责人）——均为同层级数据修正，非降级。备用试点（OpenAlex 跨源、案例表历史锚点）与下一试点（Function OS v0.2 正确性）已排入开放问题。

## 任务 104—105（编辑叙事层与 Function OS 有界基准）

任务 104（PR #160，已合并）建立编辑文章层与语料关系分析；任务 105（PR #161，已合并，精确 head `9d7d5ab512ffe3fd109a60ebd3d9d246b3a42d19`，普通合并 `9b5b4b9bfb243fe4cc52f7b163a9613ee6628321`）执行 Function OS v0.2 核心能力基准、对抗验证与传播。二者均已合并且人类可读对应物齐备，本段描述其 Current 接口。

- 任务 104：六篇编辑文章 + 语料关系图，作为叙事层刻意与机器注册表、人类结果层分离；本身对首页系统图为 **NO_MAP_IMPACT**（未改动 `project-components.json` / `change-propagation-topology.json` / `interactive-system-map-layout.json` 与生成器）。
- 任务 105：Function OS v0.2 基准——**原始目标** `PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES`（25 个 false_reject，源自 N2 嵌套相等提取缺陷），**修复后目标** `SUPPORTED_WITHIN_BOUNDED_DOMAIN`；有界 N2 缺陷已修复并复跑通过。
- 证据上限：有界域内可信；**不声称**完整沙箱化、生产就绪或普遍正确。原始与修复判定保持区分，不合并为单一结论。
- 任务 106（本迭代）建立了合并后真相传播基础设施：规范化 merged-iteration ledger、9 维 impact 引擎、确定性 current-truth 投影、fail-closed 验证器、编辑文章 stale/review 生命周期与系统图 impact 审计，使后续合并的当前真相可确定性传播并在矛盾时 fail closed。

## 更新规则

未来工作只要改变能力、状态、结论、纠正、开放问题、证据或公开表述，就必须同步 README、`HUMAN-READING.md`、`KNOWLEDGE/`、相应 `RESULTS/` 页面、机器 Delta/impact/lineage、知识体验 manifest 和历史记录。历史证据不删除，Git 历史不改写。
