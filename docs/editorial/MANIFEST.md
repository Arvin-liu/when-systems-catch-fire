# 编辑文章清单与编辑大纲（TASK 104 · §5.1 / §5.3 试点）

本清单记录任务 104 试点文章集的规划元数据。每篇文章均先有大纲再起草，正文遵循之元写作法 v0.4.0（不是把本清单字段直接变成文章目录）。源资产以现行 registry 为准；历史/隔离/猜想状态不构成现行知识。

> 文章正文目录：`docs/editorial/articles/`
> 关系分析来源：`analysis/corpus-relation/`（簇候选 C000–C007 为 ARTICLE_CANDIDATE）
> 源资产简报：`analysis/corpus-relation/cluster_source_briefs/`（由 `tools/extract_cluster_source_brief.py` 确定性生成）

---

## 001 — 撤回的引力：一个知识库如何不让强断言悄悄回弹

- **类别**：修正 / 演进（correction-evolution）
- **对应簇**：C000（MATHEMATICS 主导，n=31，含纠正/撤回/回弹主轴）
- **中心问题**：这里发生了什么纠正、撤回或回弹？当前的断言上限是什么？
- **为什么是一篇文章而非索引条目**：名字比内容大是治理问题——被命名为"万有理论"的资产若 claim ceiling 失守，会在下游被当成"已统一四力"；撤回结论若只换标题也会借尸还魂。需要把"纠正—撤回—防回弹"连成一条叙事，而不是清单。
- **源资产集**：`D188`(REJECT)、`D189`/`D190`(CONJECTURE)、`D127`/`D185`/`D186`/`D187`(STRUCTURAL_METAPHOR)、`D182`/`D184`(TOY_MODEL)、`D183`(REWRITE_AND_RETEST)、`D260`(TESTED_INDEX)、`T2`(ESTABLISHED_MATH, M6)；纠正记录 `physics-asset-correction-20260729`、`historical-correction-log`、`strong-claim-gates`、`future-claim-admission-protocol`；边界断言 `NFC-71E297CA6132AAC6`、`NFC-6CA935CA1A4F2A8E`、`NFC-70A1EC2C42864627`、`NFC-51F85A6892787610`、`NFC-61546854AF53780B`、`NFC-00B4BE17FB8DC706`、`NFC-0B7DEFAEF4EFAB24`。
- **内部关系模型**：以"名字—实际身份"张力为轴，串联同簇资产的纠正状态差异，再用强断言门禁/纠偏日志/supersession lineage 解释"为何不回弹"。
- **范围与主张上限**：只修点火自身资产能支持什么，不碰四力统一/量子引力；不新建裁决、证明或实证；与现行 registry 冲突以现行资产为准。
- **当前 / 历史 / 开放区分**：当前=各项纠正后状态与撤回状态；历史=旧表头与 HISTORICAL_ONLY 命题；开放=四力统一、量子引力、大一统仍为开放问题。
- **目标读者与目的**：关心"AI 生成知识如何不被悄悄升级"的研究者/维护者；建立对 claim ceiling 与防回弹纪律的直觉。
- **叙事大纲**：名字许诺 vs 实际身份 → 为何是治理问题 → 2026-07-29 纠偏做了/没做什么 → 簇里唯一稳的 T2 反衬不稳者 → 防回弹三纪律 → 开放而非结束 → 回照开头。

---

## 002 — 两份表面，一个真相：机器注册表与人类可读层如何不漂移

- **类别**：架构 / 系统（architecture-system）
- **对应簇**：C001（ARCHITECTURE_GOVERNANCE 主导，n=15）
- **中心问题**：知识资产怎样被登记、裁决、修订、隔离并保持机器与人类表面一致？
- **为什么是一篇文章而非索引条目**：5,663 身份卡与 17,333 断言的"底下真相"和十分钟阅读 route 的"表面"之间存在治理缝隙；需要解释两套表面如何始终对齐。
- **源资产集**：`RESULTS/ADJUDICATION-SUMMARY.md`、`historical-function-deep-adjudication-20260729`、`098-claim-governance-implementation`、`098-dependency-impact`；状态纪律 `llms.txt`、`AI-HANDOFF.md`、`docs/project-current-state.md`、`RESULTS/CORRECTIONS.md`、`docs/discipline_kernel_pilot.md`；表面 `HUMAN-READING.md`、`knowledge-experience-layer`、`RESULTS/README.md`；边界断言 `NFC-187E985133669A56`、`NFC-2843222A849FE77E`、`NFC-3D9FFB2206406FCC`、`NFC-517A9B6DE3674E2A`、`NFC-2B7304F480DA70C2`、`NFC-390D533E6AA565C0`、`NFC-6122E6F96EFE210E`、`NFC-6CA935CA1A4F2A8E`、`NFC-70A1EC2C42864627`。
- **内部关系模型**：以"缝隙=治理发生处"为潜题，串联身份/双轴/十门/census/quarantine/Historical-Current/lineage 绑定。
- **范围与主张上限**：解释对齐机制；闭合是会计闭合不是证明闭合；不新建治理结论。
- **当前 / 历史 / 开放区分**：当前=1.4.0 方法与现行 registry；历史=1.2.0/1.3.0 方法与旧系统图；开放=registry 之外未穷尽审查项。
- **目标读者与目的**：接手/审计仓库的人；理解机器与人类表面为何不漂移。
- **叙事大纲**：十分钟表面 vs 底下真相 → 为何非小事 → 身份/轴/门 → 隔离而非模糊 → "当前"易被误读 → 撤回后换名不算翻案 → 回照缝隙。

---

## 003 — 从候选到 Current：一条留下痕迹的证据链

- **类别**：证据 / 验证（evidence-validation）
- **对应簇**：C004（OPERATIONS_EVIDENCE 主导，n=15）
- **中心问题**：候选、验证、合并和 Current 怎样分离并留下可复算证据？
- **为什么是一篇文章而非索引条目**：四态（candidate/validated/merged/Current）极易被压成"done"，这正是本地验证滑向现实断言的入口；需把分离机制写成一条可追溯链。
- **源资产集**：`121Q9-global-validation`、`101-human-readable-surfaces-self-correction-closeout`、`independent-second-angle-audit-056`、`104-dual-088-reconciliation`；门禁 `RESULTS/README.md`、`README.md`、`llms.txt`、`stage-snapshot-publication`；边界断言 `NFC-2F6931FFF5A6554C`、`NFC-A5870D6C2E430817`、`NFC-C349FBD C470B50AB`、`NFC-6122E6F96EFE210E`、`NFC-6CA935CA1A4F2A8E`、`NFC-70A1EC2C42864627`、`NFC-2B7304F480DA70C2`、`NFC-A6B80FCA608C8C8F`、`NFC-996C4E8631D40356`。
- **内部关系模型**：以"四态滑动"为张力，串联候选索引、本地验证、强断言门禁、人类可见性门禁、exact-head 合并、发现表面重生成。
- **范围与主张上限**：解释证据链与 CI；不声称物理理论被验证、不声称 census 穷尽、不声称外部同步完成。
- **当前 / 历史 / 开放区分**：当前=已合并且人类可见对应物齐备；历史=SOURCE_INDEXED 未裁决项；开放=2,033 项未深审与外部同步。
- **目标读者与目的**：做复现/审计的人；理解"通过"到底指哪一环。
- **叙事大纲**："done"的四种含义 → 为何值得写清 → 候选≠结论 → 验证是分开一跳 → 人类可见性门禁 → 合并/当前两环 → 链的价值在留痕。

---

## 004 — 门控模型能走到哪里：一次有边界的物理投影，与未完成的统一

- **类别**：跨域（映射局限为核心）（cross-domain）
- **对应簇**：C005（PHYSICS 主导，n=11）
- **中心问题**：门控模型能支持什么有界物理投影，哪些统一与观测义务仍未完成？
- **为什么是一篇文章而非索引条目**：跨域映射是项目签名动作，其边界恰是过度声称所在；需以物理统一为例，把"有界投影 vs 宣布统一/不可能"的缝画清楚。
- **源资产集**：`physics-asset-correction-20260729`、`docs/physics_boundary.md`、`public-claim-ceiling-guidance.md`、`discipline_kernel_pilot.md`、`README.md`、`project-current-state.md`；函数 `D127`/`D185`/`D186`/`D187`(METAPHOR)、`D182`/`D184`(TOY)、`D188`(REJECT)、`D189`/`D190`(CONJECTURE)、`D183`(REWRITE)、`D260`(INDEX)；边界断言 `NFC-00B4BE17FB8DC706`、`NFC-51F85A6892787610`、`NFC-61546854AF53780B`、`NFC-6CA935CA1A4F2A8E`、`NFC-70A1EC2C42864627`、`NFC-7BA5AE6B5EFE40A7`、`NFC-7F34FF08B3193964`、`NFC-82EBE95DEF5BFAB1`、`NFC-9D5698768267468E`、`NFC-B3044ED3734222FB`、`NFC-777640D03F719F40`(HISTORICAL)、`T33`。
- **内部关系模型**：以"跨域诱惑"为张力，串联有界投影、被撤回的"不可能"、不能充当桥的几类类比、HISTORICAL 残留、显式保留的开放义务。
- **范围与主张上限**：不声称四力统一/量子引力/大一统已解决或已证不可能；结构性隐喻不升级为物理推导。
- **当前 / 历史 / 开放区分**：当前=模型未统一且未证不可能；历史=旧"已证不可能"命题（已撤回）；开放=四力统一、量子引力、观测义务。
- **目标读者与目的**：对跨域同构表达感兴趣者；理解映射边界如何防止 overclaim。
- **叙事大纲**：门控靠近统一的诱惑 → 有界投影+被撤回断言 → 什么不能当桥 → 映射边界=overclaim 所在 → 历史残留不升级 → 诚实地图画到边界为止。

---

## 005 — 描述不等于证明：跨尺度、概率与关系网络能说什么，不能说什么

- **类别**：重大开放问题（不假装解决）（open-problem）
- **对应簇**：C006（SYSTEMS 主导，n=18）
- **中心问题**：跨尺度表示、概率动力学和关系网络能描述什么，不能证明什么？
- **为什么是一篇文章而非索引条目**：MCF/PSD/ARN/Atlas 让"描述"很完整，易滑动为"解释/证明"；需把"能描述"与"能证明"的缝显式保留为开放问题，而非收尾成结论。
- **源资产集**：`multiscale-causal-fabric`、`121Q22-probabilistic-system-dynamics-validation`、`mechanism-adjudication-plane`、`map-epistemic-architecture`、`121Q23-network-theory-source-map`、`121Q25D-current-closeout`、`121Q31-...system-map...audit`；规范性 `V4.md`、`S4.md`；索引验证 `d598-...`、`teacher-competition-...`、`nf-004-...`、`nf-002-...`、`codespace-rescue-two-tables-...`；边界断言 `NFC-1E10227F1B51E4D0`、`NFC-2B7304F480DA70C2`、`NFC-B424983D09C9A88D`、`NFC-B3044ED3734222FB`。
- **内部关系模型**：以"表示 vs 证明"为潜题，串联候选派生表示、Atlas 派生投影、机制裁决平面、规范性协议的价值—条件—伤害边界。
- **范围与主张上限**：不解决任何开放问题；只把它显式保留为开放；表示能力不构成为因果或经验证明。
- **当前 / 历史 / 开放区分**：当前=表示工具为候选派生；历史=旧系统图/方法版本；开放=哪些性质可捕获、哪些须回形式证明或外部实证。
- **目标读者与目的**：系统/复杂科学读者；理解表示与证明的界限为何必须保留。
- **叙事大纲**：漂亮表示机器 → 描述滑向证明的诱惑 → 表示≠因果证明 → Atlas 是派生非第二真相 → 规范性协议是边界非定律 → 开放问题不该被填。

---

## 006 — 把结果写成可读作品，而不越过来源、证据与许可边界

- **类别**：编辑 / 出版纪律（editorial-publication，规模化首篇）
- **对应簇**：C007（WRITING_PUBLICATION 主导，n=16）
- **中心问题**：研究结果如何形成可阅读作品，同时不越过来源、证据与许可边界？
- **为什么是一篇文章而非索引条目**：本任务本身就在生产这类作品，"我们怎样写而不撒谎"是读者最该理解的方法论；它不是某个断言的索引，而是把双来源素材池、非重发原则、1/5/完整阅读分层、五类职责收口与一项隔离警示连成一条编辑纪律叙事。
- **源资产集**：`nfc-97dbfc72d7ef8b40`（之元写作法 0.4.0 双来源素材池，RETAINED_AS_STRUCTURAL_METAPHOR）、`nfc-517a9b6de3674e2a`（五类职责收口，ACCEPTED_AS_DEFINITION）、`nfc-3d9ffb2206406fcc`（统一卡片与 1/5/完整阅读分层，ACCEPTED_AS_DEFINITION）、`nfc-6122e6f96efe210e`（iteration method 1.4.0 持续阶段快照发布，**QUARANTINED_AMBIGUOUS**）、`hr-43bf10109af2485e`（External Input Non-Republication Principle，CURRENT_REPOSITORY_DOCUMENT）、`hr-3b5e72d7f1cdfb5b`（之元写作法内部范例与反例 v0.3.0，CURRENT_SCOPED_SOURCE）、`hr-25ccad6cef81cbea`（已发布作品《当一支军队开始相信自己的背影》，作为人类可读成品样例）、`hr-3069e59a51d869c3`/`hr-44a1c398c470bbf4`/`hr-3d02f20fb6692a0c`/`hr-4419fea9529c829c`（121Q28/121Q28S/121Q31/121Q31T 写作法与系统图收口审计，CANDIDATE_OR_PENDING_SOURCE，仅作流程史，不升级为结论）。
- **内部关系模型**：以"可读 ≠ 可声称"为潜题，串联双来源池（external_input 与 ignition_increment 的边界）、非重发原则、阅读分层、五类职责、0.4.0 与 0.3.0 的当前/历史区分，最后以 QUARANTINED 的 1.4.0 为例收束"快照可见性 ≠ 已接受/已 Current/已激活"。
- **范围与主张上限**：描述项目既有编辑方法与边界；不声称方法普遍有效（nfc-517a9b 明示不得从一项接受作品推出普遍有效）；不升级任何 CANDIDATE 审计为结论；隔离项不进入"当前知识"。
- **当前 / 历史 / 开放区分**：当前=0.4.0 双来源池与五类职责收口；历史=0.3.0 已合并版本与旧同步契约 121Q25B（HISTORICAL_OR_SUPERSEDED）；开放=外部同步与受限原始材料公开边界仍待界定。
- **目标读者与目的**：阅读本任务产出的任何人；理解这些文章为何能读、又为何刻意不把"通过/快照/registry 存在"写成"已被证明"。
- **叙事大纲**：可读作品的诱惑 → 双来源池把"外部输入"与"点火增量"分开 → 非重发原则守住许可边界 → 1/5/完整三层让不同读者各取所需 → 五类职责防止 README 投影被当权威 → 隔离的 1.4.0 提醒"可见 ≠ 已接受" → 回照开头：我们写，但写有边界。

---

## 试点覆盖对照（§5.3 五类）

| §5.3 要求 | 对应文章 |
|---|---|
| one architecture/system article | 002 |
| one correction/evolution article | 001 |
| one evidence or validation article | 003 |
| one cross-domain article whose mapping limits are central | 004 |
| one article explaining a major open problem without pretending to solve it | 005 |
| （规模化）编辑/出版纪律（直接服务本任务可读性与 §6 阅读架构） | 006 |

> 试点集（001–005）已覆盖 §5.3 五类；006 为规模化首篇，价值高、与五篇重叠低、源资产多为 ACCEPTED_AS_DEFINITION / CURRENT 文档，属"最大可辩护首版"范围内。

## 待规模化与编辑 backlog（高价值簇优先，#426）

- **已纳入首版（规模化）：** `C007`（WRITING_PUBLICATION, n=16）→ 文章 006。理由：直接关于项目自身编辑纪律（之元写作法 0.4.0 双来源池、非重发原则、阅读分层、五类职责），与 001–005 重叠低，源资产以 ACCEPTED_AS_DEFINITION / CURRENT_REPOSITORY_DOCUMENT 为主，可辩护；且天然支撑 §6 人类阅读架构。
- **暂置 backlog（已评估，显式不纳入首版）：**
  - `C002`（COGNITION, n=17）：其已裁决核心（V1 延续性协议、V2 效率协议、12 元协议、Attention/Attractor 控制面）与 C001 共用同一批 CURRENT 治理文档，重叠高；其真正独特内容（违抗/主体性原语 D595–D604、121Q13 注意力/压缩）多为 `CANDIDATE_OR_PENDING_SOURCE`（`READYFORGPTVERIFICATIONCANDIDATEONLY`），104 不得升级，且 §12 禁止把语义相似当实质关系。待 104 之后、由 GPT 验证或编辑先界定连贯问题再决定是否成篇。
  - `C003`（MATHEMATICS 精确对象, n=4）：规模过小，可并入后续数学主题文章，不单独成篇。
- 参考集合（仅按主题/研究问题聚合，需编辑先界定连贯问题，暂不成本文）：`C008`(46)、`C009`(2)、`C010`(61)、`C011`(73)、`C012`(4)、`C013`(38)、`C014`(11)。
- 原则：剩余簇进入显式 backlog，不以低质生成散文填满；每篇新文章须先有 §5.1 大纲与 §5.2 写作法应用记录。
