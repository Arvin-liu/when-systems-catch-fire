# 百轮成果台账

> 出版层状态：`PUBLISHED_WITH_EXPLICIT_LIMITATIONS`。本台账的 80 条是可恢复记录，不是 80 个独立实验或 80 项外部接受的发现。
>
本台账回答的不是“仓库有多少文件”，而是“每个可恢复成果记录改变了什么判断、当前还能说到哪里”。它保留 R0 的 80 个唯一记录，并为每条记录补上 112 的输出类别、当前有效性、可读作品状态、章节去向和结论天花板。

## 读法

“百轮”是混合的长期迭代史，不是一百个独立实验。`RESEARCH_RESULT`、`CORRECTION_RESULT`、`EMPIRICAL_OR_REPLICATION_RESULT`、`THEORY_OR_FORMALIZATION_RESULT`、`METHOD_RESULT`、`INFRASTRUCTURE_ONLY`、`MAINTENANCE_ONLY`、`MIXED` 和 `NO_RECOVERABLE_KNOWLEDGE_INCREMENT` 不是荣誉等级；它们说明记录承担的责任不同。分类基于问题、证据、当前状态和输出，而不是只看任务标题或文件名。

R0 记录来自固定基线前置材料；任务 111 的生命周期事实已在任务 112 审计起点 `main=302362f66dad4e8a9c9e72400f4267c12b0b0d00` 复核。来源路径和提交用于定位，目录/集合不等于逐项全文阅读；任何 `CURRENT_WITH_EXPLICIT_LIMITS` 都不意味着外部共同体已经接受。

## 统计摘要

| 输出类别 | 记录数 |
| --- | ---: |
| `CORRECTION_RESULT` | 21 |
| `EMPIRICAL_OR_REPLICATION_RESULT` | 7 |
| `INFRASTRUCTURE_ONLY` | 14 |
| `MAINTENANCE_ONLY` | 3 |
| `METHOD_RESULT` | 5 |
| `MIXED` | 10 |
| `NO_RECOVERABLE_KNOWLEDGE_INCREMENT` | 7 |
| `RESEARCH_RESULT` | 11 |
| `THEORY_OR_FORMALIZATION_RESULT` | 2 |

类别之间按记录可能是混合关系；表中的数量只用于检索和审计，不相加为研究成果总数。完整来源文件级哈希见 `R0_FILE_MANIFEST.json`，逐项主张证据见 `R0_CLAIM_AUDIT.jsonl`。

## 逐项记录

### R0-001｜作者动机与边界

- 原始问题：为什么不同领域会出现相似的转折、锁定、反馈和理解改变？
- 新增认识：跨域观察可以成为结构化研究的起点，但好奇心驱动不等于建立总理论。
- 证据类型：作者说明、问题谱系
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：点火首先是一个把直觉变成可检查对象的研究尝试。
- 当前边界：不承担物理、历史、社会学统一模型或专业决策。
- 纠正/撤回/取代：none
- 已有人类作品：完整问题说明
- 正文目的地：chapter-01、chapter-02
- 来源路径：docs/author_motivation_and_boundary_note.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-002｜跨域结构比较

- 原始问题：怎样把诗歌、历史、组织、AI 与日常观察放到可比较表面？
- 新增认识：对象、关系、转折、反馈的共同词汇可以帮助发现候选结构。
- 证据类型：早期函数卡、案例卡、叙事分析
- 112 输出类别：`METHOD_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：结构比较是候选生成器。
- 当前边界：候选相似不等于严格同构、机制或因果。
- 纠正/撤回/取代：早期把相似写成同构的表述已降级
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-01、chapter-04、chapter-07
- 来源路径：统一函数总表/INDEX.md；统一案例总表/INDEX.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-003｜v0.1 结构生成阶段

- 原始问题：系统能否从跨域材料中生成结构化推断、函数表达和案例？
- 新增认识：可生成一组函数、案例、候选同构和结构化语言。
- 证据类型：历史总结、函数/案例资产
- 112 输出类别：`MIXED`
- 当前有效性：`HISTORICAL_NOT_CURRENT`
- 当前结论：v0.1 的贡献是发现和表达能力。
- 当前边界：生成的结构缺少足够的证据制度、失败分类和 claim ceiling。
- 纠正/撤回/取代：被 v0.2 的自我限制方向取代
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-01、chapter-02
- 来源路径：docs/v0.2_summary.md；RESULTS/CHRONOLOGY.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-004｜v0.2 自我限制转向

- 原始问题：系统怎样从能生成结构变成能限制自己？
- 新增认识：边界、证据制度、失败分类、benchmark、pending、L0-L5 和机器可读状态成为一等对象。
- 证据类型：版本总结、证据制度、状态字段
- 112 输出类别：`METHOD_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：研究基础设施的主要转折是把不确定性保存下来。
- 当前边界：方法上的自我限制不会替各领域完成验证。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：完整报告
- 正文目的地：chapter-02、chapter-03
- 来源路径：docs/v0.2_summary.md；docs/evidence_regime_library.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-005｜Evidence Regime Library

- 原始问题：数学、物理、历史、医学、法律、工程和艺术能否使用同一证据标准？
- 新增认识：不同领域有不同证据制度，点火必须把内部表示、外部来源、实验、证明和叙事分开。
- 证据类型：证据分类、领域边界
- 112 输出类别：`METHOD_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：证据强度是领域化和对象化的。
- 当前边界：点火通常不能直接到达 L4/L5 的外部真理或共识。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：完整说明
- 正文目的地：chapter-02、chapter-03、chapter-06
- 来源路径：docs/evidence_regime_library.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-006｜旧函数总表

- 原始问题：如何从跨域直觉中积累可比较的函数和关系素材？
- 新增认识：形成了高密度的候选函数、结构关系和命名素材池。
- 证据类型：历史索引、函数卡片、人工整理
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：旧表是研究材料池和反例池。
- 当前边界：约 624 个文件和历史索引中的 617 个函数不是 617 个已证实成果。
- 纠正/撤回/取代：强物理/普适函数表述进入 Foundation 审计
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-04、chapter-05
- 来源路径：统一函数总表/INDEX.md；统一函数总表
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-007｜旧案例总表

- 原始问题：如何把不同领域的转折故事保存成可复查的案例？
- 新增认识：形成了约 804 个历史索引案例和继续扩展的叙事素材池。
- 证据类型：历史索引、案例文件、来源链
- 112 输出类别：`MIXED`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：案例可以生成问题、反例和验证队列。
- 当前边界：案例规模不代表独立证据，叙事材料不能直接推出机制。
- 纠正/撤回/取代：部分英雄叙事和单因果叙述降级
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-01、chapter-07
- 来源路径：统一案例总表/INDEX.md；统一案例总表
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-008｜早期跨域叙事作品

- 原始问题：怎样让结构比较对普通读者可读？
- 新增认识：用具体人物、物件和转折讲抽象结构，比直接堆术语更能暴露推断的跳跃。
- 证据类型：文章、故事素材、读者表面
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：叙事是研究材料的可读入口。
- 当前边界：可读性不是证据强度，读者共鸣不是验证。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-01、chapter-07、chapter-09
- 来源路径：docs/editorial/articles；outputs/stories
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-009｜双层书/代理/研究结构

- 原始问题：如何同时容纳人的阅读和机器的审计？
- 新增认识：人类作品、机器注册、形式化对象和来源链可以分层，而不是互相伪装。
- 证据类型：仓库结构、公共页面、来源链
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：双层结构提高可追溯性。
- 当前边界：分层完成不等于各层内容已经正确或完整。
- 纠正/撤回/取代：none
- 已有人类作品：结构性
- 正文目的地：chapter-08、chapter-09
- 来源路径：README.md；RESULTS/RESEARCH-AND-ARTICLES.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-010｜RESULTS Chronology

- 原始问题：百轮历史如何在不逐个翻阅任务的情况下被恢复？
- 新增认识：可从约 287 个既有研究、文章、架构、Foundation 和迭代记录恢复源忠实时间线。
- 证据类型：人类时间线、Git 历史、报告索引
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：时间线是出版层的导航，不是成果总数。
- 当前边界：摘要可能折叠冲突版本，必须回到原始路径和提交。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：完整导航
- 正文目的地：chapter-01、chapter-08
- 来源路径：RESULTS/CHRONOLOGY.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-011｜退回与降级语法

- 原始问题：强断言错误出现后，系统如何阻止它们继续作为当前结论？
- 新增认识：withdrawn、downgraded、pending、quarantine、rewrite_and_retest 等状态可以保留错误的历史并改变当前可见结论。
- 证据类型：纠正清单、状态机、迁移记录
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：纠正不是删掉历史，而是改变可发布的 claim ceiling。
- 当前边界：状态字段需要人类正确解释，自动注册不等于语义判定。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-04
- 来源路径：RESULTS/CORRECTIONS.md；FOUNDATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-012｜claim ceiling

- 原始问题：如何在写作时明确一句话最多能说到哪里？
- 新增认识：artifact_created、schema_validated、workflow_passed、implementation_observed、mechanism_plausible、mechanism_discriminated、causal_identification_pending、insufficient_evidence 可区分不同结论高度。
- 证据类型：迭代方法、状态枚举、审计报告
- 112 输出类别：`METHOD_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：claim ceiling 把证据和语言绑定起来。
- 当前边界：它是诚实表达工具，不是外部科学等级的替代物。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：方法说明
- 正文目的地：chapter-02、chapter-03、chapter-08
- 来源路径：ITERATION.md；reports/operations
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-013｜Foundation 迁移

- 原始问题：怎样把历史函数和断言移入具有类型、证据、数学成熟度和处置的系统？
- 新增认识：身份、类型、证据、authority 和 disposition 可以独立记录。
- 证据类型：迁移摘要、schema、注册表
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：Foundation 建立了对象会计和证据谱系。
- 当前边界：对象会计不等于对象真实或有价值。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-03、chapter-04
- 来源路径：FOUNDATION.md；data/foundation/migration-summary.json
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-014｜有限商结构边界

- 原始问题：有限模型中的零除法和商映射能否支撑四种相互作用不可能统一？
- 新增认识：当前模型至多支持声明载体内的有限反例或零除法/商映射结论，不能推出物理统一或物理不可能性。
- 证据类型：形式化资产、反例、Foundation 审计
- 112 输出类别：`THEORY_OR_FORMALIZATION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：强物理总断言撤回，保留 carrier-scoped 结果。
- 当前边界：真实物理的统一问题仍开放。
- 纠正/撤回/取代：old grand-unification impossibility withdrawn
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-08
- 来源路径：docs/foundation/physics-asset-correction-20260729.md；RESULTS/CORRECTIONS.md
- 来源提交：23f4702a0、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明对象、假设和形式系统内的结果；不能越界到现实本体

### R0-015｜T2 与 D127 身份修正

- 原始问题：历史上把乘法零法则和认知路径积分写成同一个对象是否准确？
- 新增认识：形式化 T2 与历史 D127 必须分开；D127 保留为认知/叙事路径积分，不能伪装成物理定理。
- 证据类型：Foundation 形式化、历史条目、纠正报告
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：同名或同形不能替代身份和语义。
- 当前边界：有限形式化对象不扩大到现实过程。
- 纠正/撤回/取代：D127 no longer carries T2 theorem status
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-04
- 来源路径：FOUNDATION.md；RESULTS/CORRECTIONS.md
- 来源提交：23f4702a0、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-016｜D260 语义修订

- 原始问题：旧的物理绑定描述是否超出了现在的对象？
- 新增认识：D260 更合适的身份是 p/(1-p) bias sensitivity score，而不是旧物理绑定。
- 证据类型：形式化说明、纠正表、对象迁移
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：改名和改语义降低了伪物理确定性。
- 当前边界：分数的解释和外部应用需要另外验证。
- 纠正/撤回/取代：old physical binding withdrawn
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-04
- 来源路径：FOUNDATION.md；RESULTS/CORRECTIONS.md
- 来源提交：23f4702a0、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-017｜Lean/SymPy/Z3 bounded assets

- 原始问题：形式化工具能否把候选函数、反例和不可满足性写得可重放？
- 新增认识：对明确对象和有限模型，可以得到 Lean/Z3 有界结果、SymPy 反例或形式化简化。
- 证据类型：Lean、SymPy、Z3、形式化卡片
- 112 输出类别：`THEORY_OR_FORMALIZATION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：形式化提高模型内的清楚度和反例能力。
- 当前边界：有限模型、样本和符号化简不证明普遍命题；T23 等仍未证明。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-03、chapter-04
- 来源路径：formal；data/foundation
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明对象、假设和形式系统内的结果；不能越界到现实本体

### R0-018｜历史函数深度裁决

- 原始问题：7,000 级别的函数候选能否获得统一身份和处置？
- 新增认识：7,051 个 canonical identity cards、12 类身份、六层裁决、E0/E1 和显式 quarantine 可以机器追踪。
- 证据类型：closure summary、discovery coverage、人工裁决
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：形成了函数资产的注册表会计。
- 当前边界：大量对象仍是 unresolved identity 或 quarantine；这不是 7,051 个已证函数。
- 纠正/撤回/取代：public count surface mismatch remains
- 已有人类作品：已有可读材料：完整报告
- 正文目的地：chapter-04、chapter-08
- 来源路径：docs/foundation/historical-function-deep-adjudication-20260729.md；data/foundation/function-assets/closure-summary.json；data/foundation/function-assets/discovery-coverage.json
- 来源提交：ebe723fbf、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-019｜非函数断言闭合

- 原始问题：如何阻止描述、类比、经验和伪定理混在函数注册表里？
- 新增认识：17,626 个 canonical claims 可按 13 类、处置、外部证据和数学成熟度追踪；撤回不应反弹。
- 证据类型：closure summary、lineage report、审计 gates
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：断言会计让“我说过什么”和“我能支持什么”分离。
- 当前边界：不能从注册表推出新颖性、同行评议、复制或现实真理；公共计数不一致。
- 纠正/撤回/取代：public count surface mismatch remains
- 已有人类作品：已有可读材料：完整报告
- 正文目的地：chapter-03、chapter-04
- 来源路径：reports/foundation-architecture/100-nonfunction-claim-evidence-lineage-closure.md；data/foundation/nonfunction-claims/closure-summary.json
- 来源提交：ebe723fbf、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-020｜任务 102 Foundation 公共闭合

- 原始问题：Foundation 的机器对象如何让读者看见？
- 新增认识：公共表面、迁移摘要、注册表和状态可以提供可查入口。
- 证据类型：README、public surface、migration
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：公共可见性是研究基础设施的一部分。
- 当前边界：README 的 5,663/17,333 计数与机器 7,051/17,626 闭合计数未被一页解释。
- 纠正/撤回/取代：needs publication-layer reconciliation
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-04、chapter-08
- 来源路径：README.md；data/foundation/migration-summary.json；RESULTS/LATEST.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-021｜MCF 多尺度因果织构

- 原始问题：跨尺度的对象、关系、路径和反馈怎样被保存？
- 新增认识：MCF 可以把尺度、边界、reachability、反馈、残差和因果候选作为表示层组件。
- 证据类型：架构规范、validator、报告
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：MCF 是可审计的表示候选。
- 当前边界：路径、网络、cone 和 map 不是因果证明；桥接和概率语义必须显式。
- 纠正/撤回/取代：none
- 已有人类作品：候选架构说明
- 正文目的地：chapter-05、chapter-08
- 来源路径：docs/architecture/multiscale-causal-fabric.md；reports/architecture/121Q21R-mcf-validation-coverage.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-022｜PSD 概率系统动力学

- 原始问题：如何在系统表示中区分观察相关与干预因果？
- 新增认识：P(Y|X)、P(Y|do(X))、系统边界、时间和熵语义可以分别声明。
- 证据类型：架构规范、validator、bounded examples
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：PSD 提供了防止相关性偷换干预的表示护栏。
- 当前边界：不是现实动力学或统一概率理论；未声明假设不自动成立。
- 纠正/撤回/取代：none
- 已有人类作品：候选架构说明
- 正文目的地：chapter-05、chapter-08
- 来源路径：docs/architecture/probabilistic-system-dynamics.md；reports/architecture/121Q22-psd-validation-coverage.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-023｜ARN 自适应关系网络

- 原始问题：关系网络能否表达跨域结构的变化和时间路径？
- 新增认识：时间尊重路径、高阶关系、拓扑变化和投影校验可被表示和验证。
- 证据类型：架构规范、真实历史投影、path counterexamples
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：ARN 是关系表示和验证候选。
- 当前边界：邻接、相似度、中心性和社区不是因果、本体或真理。
- 纠正/撤回/取代：none
- 已有人类作品：候选架构说明
- 正文目的地：chapter-05、chapter-07
- 来源路径：docs/architecture/adaptive-relational-network.md；reports/architecture/121Q23-arn-validation-coverage.md；reports/architecture/121Q23C-arn-real-history-proof.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-024｜Q12 action/mechanism planes

- 原始问题：行动建议与机制判定如何分开？
- 新增认识：effectual action plane 和 mechanism adjudication plane 可以分层，历史 pilot 只在声明 ceiling 内记录。
- 证据类型：schema、workflow、historical pilot
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：行动可行性不应冒充机制真理。
- 当前边界：现实行为结果、机制判定和因果识别仍待外部证据。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-05、chapter-09
- 来源路径：reports/research/121Q12-effectual-action-and-mechanism-plane.md；docs/architecture
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-025｜Q13 注意力/分布/压缩

- 原始问题：注意力集中、输出分布和压缩完整性怎样成为可审计对象？
- 新增认识：可以用 schema 表达 attention/attractor、decision collapse、compression integrity 和 warning。
- 证据类型：schema、AI sample、validator
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY`
- 当前结论：这些概念可先作为检测与描述工具。
- 当前边界：AI 重复输出不是独立证据，CI 成功不是理论成功，样本不是事实。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：报告
- 正文目的地：chapter-05、chapter-08
- 来源路径：reports/research/121Q13-attention-distribution-compression.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明的 schema、工作流和运行范围；不能写成科学正确

### R0-026｜Q14 Ignition Atlas

- 原始问题：如何让跨域资产在图谱中可导航而不把位置当成真理？
- 新增认识：版本化地图、节点、边、分组和导航视图可以提供可追踪入口。
- 证据类型：JSON spec、generated map、schema validation
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY`
- 当前结论：Atlas 是导航和压缩层。
- 当前边界：位置、视觉相近、中心性和边不证明因果或相似性。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-05、chapter-09
- 来源路径：reports/research/121Q14-ignition-atlas.md；KNOWLEDGE
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明的 schema、工作流和运行范围；不能写成科学正确

### R0-027｜Function OS v0.2 candidate

- 原始问题：函数能否从声明、解析、执行、验证到回归形成候选管线？
- 新增认识：在符号确定性、顺序组合、有限输入域内，N1–N9 管线可以执行和验证。
- 证据类型：candidate reference implementation、scope contract、tests
- 112 输出类别：`MIXED`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：Function OS 是有边界的候选参考实现。
- 当前边界：不是完整 OS、通用解释器、sandbox、生产系统或外部真理。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：README 与报告
- 正文目的地：chapter-05、chapter-08
- 来源路径：function-os-candidate/v0.2/README.md；function-os-candidate/v0.2/scope-contract.json
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-028｜Function OS 原始 benchmark

- 原始问题：原始函数管线是否在独立 oracle 上正确？
- 新增认识：479 cases 中出现 25 false reject，false accept 为 0，污染为 0；嵌套 equality split 缺陷是真实实现失败。
- 证据类型：benchmark、independent oracle、failure trace
- 112 输出类别：`EMPIRICAL_OR_REPLICATION_RESULT`
- 当前有效性：`FAILED_RETAINED_FOR_HISTORY`
- 当前结论：候选实现曾有可复现的局部缺陷，失败被保留下来。
- 当前边界：该失败不代表 Function OS 整体无效，也不说明其他函数域。
- 纠正/撤回/取代：superseded by repaired runner but not erased
- 已有人类作品：已有可读材料：benchmark report
- 正文目的地：chapter-05、chapter-08
- 来源路径：function-os-candidate/v0.2/benchmark；reports/external-research/105-function-os-benchmark.md
- 来源提交：16f64004、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明版本、输入和失败现场；不能外推为全路线失败

### R0-029｜Function OS 修复后重放

- 原始问题：修复 split 等式解析缺陷后，有限 benchmark 能否重放？
- 新增认识：修复目标在声明的 bounded symbolic deterministic domain 内达到 semantic agreement 1.0，并保留原始失败。
- 证据类型：repaired runner、benchmark、regression target
- 112 输出类别：`EMPIRICAL_OR_REPLICATION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：可支持“该修复版本在该 benchmark/域内通过”。
- 当前边界：不能外推为所有函数、神经网络、概率函数或生产安全保证。
- 纠正/撤回/取代：replaces raw runner verdict only within bounded scope
- 已有人类作品：已有可读材料：报告
- 正文目的地：chapter-05、chapter-08
- 来源路径：function-os-candidate/v0.2/benchmark/CLAIM_VERDICTS.json；reports/external-research/121-function-paradigm-fulltext-review-report.md
- 来源提交：1314ba80、46471183、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明样本、版本、环境和 oracle 内的观察；不替代外部复制

### R0-030｜任务 103 Crossref

- 原始问题：117 个 DOI 的题名和年份能否以固定协议从外部元数据源回收？
- 新增认识：117/117 解析题名/年份，5 个年份修正，保留 1 个有意重复，未见 retraction signal。
- 证据类型：pre-registration、Crossref response、rerun artifacts
- 112 输出类别：`EMPIRICAL_OR_REPLICATION_RESULT`
- 当前有效性：`SUPPORTED_METADATA_ONLY`
- 当前结论：Crossref 元数据回收在协议范围内成功。
- 当前边界：只支持元数据字段和响应，不支持全文、内容或物理主张。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-06
- 来源路径：evidence-program/preregistration/crossref-protocol.md；evidence-program/reports/103-crossref-result.md
- 来源提交：1b999a221、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：书目元数据和匹配规则；不能写成正文或机制支持

### R0-031｜任务 104 来源质量审计

- 原始问题：来源已验证的说法是否超过了真实来源证据？
- 新增认识：117 条被降到 metadata-only；0 fulltext、0 claim support，14 个缺口显式化。
- 证据类型：source audit、Crossref reconciliation、status downgrade
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：元数据成功不能升级来源内容。
- 当前边界：未执行的 088-A/C 和全文核验仍是开放缺口。
- 纠正/撤回/取代：INJECTED_VERIFIED downgraded to METADATA_VERIFIED
- 已有人类作品：已有可读材料：完整审计
- 正文目的地：chapter-03、chapter-06
- 来源路径：reports/external-research/104-source-quality-audit.md；reports/external-research/104-dual-088-reconciliation.md
- 来源提交：16f640045、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-032｜任务 105 Function OS benchmark declaration

- 原始问题：Function OS 的 benchmark 是否有独立 oracle、样本边界和预注册？
- 新增认识：479 cases 分成 S1 398、S2 62、S3 19，7 个声明和独立 oracle 被明确。
- 证据类型：pre-registration、benchmark、oracle
- 112 输出类别：`EMPIRICAL_OR_REPLICATION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：有限 benchmark 的可重复性和范围被声明清楚。
- 当前边界：样本不是函数领域全集，原始/修复状态必须分开。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-05
- 来源路径：evidence-program/preregistration/function-os-benchmark.md；function-os-candidate/v0.2/benchmark
- 来源提交：9b5b4b9bf、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明样本、版本、环境和 oracle 内的观察；不替代外部复制

### R0-033｜任务 106 coverage correction

- 原始问题：18/18 的证据覆盖是否真实？
- 新增认识：修正了 false coverage；来源从 25 增至 31，14/14 validator，全文支持 7/18，2 个降级。
- 证据类型：coverage audit、fulltext cards、validator
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：覆盖率声明必须分解为来源、全文、主张和 validator。
- 当前边界：剩余来源/主张仍不能自动升级，Option C 为 provisional。
- 纠正/撤回/取代：18/18 full support claim corrected
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-05、chapter-06
- 来源路径：reports/external-research/106-105-evidence-correction-report.md；reports/external-research/121A-night-recovery-report.md
- 来源提交：af9884220、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-034｜Function paradigm atlas

- 原始问题：外部文献是否支持 Function OS 的九节点能力？
- 新增认识：84 个来源、10 个家族；仅 17 个摘要、0 fulltext 在第一轮，后续 30 张全文卡均为 partial；表示层相对强，神经/规范/验证弱。
- 证据类型：Crossref/OpenAlex-like metadata、abstract review、fulltext cards
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：外部文献为若干表示节点提供部分支持。
- 当前边界：没有严格等价、没有完整 OS 支持，GAP-015–020 仍开放。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：完整报告
- 正文目的地：chapter-05、chapter-06
- 来源路径：reports/external-research/120-function-paradigm-atlas-report.md；reports/external-research/121-function-paradigm-fulltext-review-report.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-035｜任务 110 OpenAlex

- 原始问题：第二个元数据源能否与 DOI 主键进行交叉核验？
- 新增认识：116 unique primary DOI 中 101 supported、8 partial、7 null、0 contradicted；null 和 online/print 歧义被保留。
- 证据类型：pre-registered metadata query、OpenAlex response、null analysis
- 112 输出类别：`EMPIRICAL_OR_REPLICATION_RESULT`
- 当前有效性：`SUPPORTED_METADATA_ONLY`
- 当前结论：OpenAlex 试验支持了 metadata-level 的交叉核验和 null 暴露。
- 当前边界：没有全文或内容事实验证，没有 corrected rerun，不能支持论文主张。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-06、chapter-08
- 来源路径：reports/external-research/110-openalex-result.md；RESULTS/OPEN-QUESTIONS.md
- 来源提交：37c880c33、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：书目元数据和匹配规则；不能写成正文或机制支持

### R0-036｜Q120/Q121 Function OS 文献回收

- 原始问题：Function OS 的能力边界能否被外部计算/函数范式文献校准？
- 新增认识：外部来源更支持表示、规范化和部分验证的方向，而非一个已经存在的通用系统。
- 证据类型：source families、fulltext cards、gap map
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：文献回收产生了边界校准和缺口清单。
- 当前边界：全文数量、学科分布和模型偏差使结论只能是 partial。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-05、chapter-06
- 来源路径：reports/external-research/120-function-paradigm-atlas-report.md；reports/external-research/121A-night-recovery-report.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-037｜苹果案例历史 dossier

- 原始问题：牛顿苹果故事的历史来源能支持哪些句子？
- 新增认识：Stukeley/Conduitt 等后来的回忆来源支持“牛顿把观察落苹果与关于重力的思考联系起来”的有限表述。
- 证据类型：historical memoir sources、source dossier、provenance
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：苹果—思考重力的关联在来源层面有 bounded provenance。
- 当前边界：流行的即时顿悟、完整理论当场产生、唯一直接触发和整个故事真伪都没有达到同一证据上限。
- 纠正/撤回/取代：strong popular-impact and sole-trigger claims downgraded
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-07
- 来源路径：data/operations/iterations/111/historical/EVIDENCE_DOSSIER.md；data/operations/iterations/111/historical/SOURCES.jsonl
- 来源提交：bbed7e29d、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-038｜苹果 target audit

- 原始问题：一个真实故事是否能被 Function OS 作为可执行案例重放？
- 新增认识：案例文件没有 target commit、输入输出、trace、oracle、重复运行或 regression guard；可执行目标缺失本身是审计结果。
- 证据类型：target audit、case status、fail-closed gate
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`TARGET_ABSENT`
- 当前结论：当前只能谈历史来源边界，不能谈执行失败或机制重现。
- 当前边界：没有目标就没有可重复的实现缺陷；任务 111 的正式状态不在本包中升级。
- 纠正/撤回/取代：narrative hypothesis not promoted to implementation defect
- 已有人类作品：已有可读材料：审计报告
- 正文目的地：chapter-07、chapter-08
- 来源路径：data/operations/iterations/111/TARGET_AUDIT.md；data/operations/iterations/111/case-status.json
- 来源提交：bbed7e29d、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：案例/实验目标审计；不能写成历史复原或程序运行失败

### R0-039｜任务 111 基线状态

- 原始问题：如何在引用 task111 研究时不把恢复或第一阶段状态写成正式终态？
- 新增认识：基线含实质研究与第一阶段终端化/证据门控内容；仓库生命周期数据仍把 111 列为 non-terminal/awaiting terminalization。
- 证据类型：baseline commit、lifecycle view、task111 artifacts
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_STATE_BOUNDARY_111_TERMINAL_RECOVERY_VERIFIED`
- 当前结论：本出版包只引用 bounded evidence，不作 task111 formal completion claim。
- 当前边界：后续恢复提交可供结构阅读，不提升为基线正式结论。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：状态说明
- 正文目的地：chapter-07、chapter-08
- 来源路径：data/operations/derived-lifecycle-view.json；RESULTS/LATEST.md；ITERATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-040｜Q24 current-state reconciliation

- 原始问题：多轮运行后如何知道哪个结论是 current、哪个只是 candidate？
- 新增认识：冷启动、远端事实、最小 gap、claim ceiling、candidate/current/merged 和传播链可以纳入一个操作方法。
- 证据类型：operation report、state reconciliation、checklist
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY`
- 当前结论：状态同步是可靠工作的前提。
- 当前边界：同步仓库不等于同步现实，也不等于因果识别。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：报告
- 正文目的地：chapter-08、chapter-09
- 来源路径：reports/operations/121Q24-current-state-reconciliation.md；ITERATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明的 schema、工作流和运行范围；不能写成科学正确

### R0-041｜Q25B 全项目同步契约

- 原始问题：跨文件依赖和发布表面如何被同步而不把同步误写成事实？
- 新增认识：仓库依赖、同步义务和现实机制候选可以类型化分开，validator defect 也可被发现。
- 证据类型：sync contract、validator、propagation audit
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY`
- 当前结论：传播契约减少了陈旧链接和状态不一致。
- 当前边界：不证明公共页面或现实世界断言为真。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：报告
- 正文目的地：chapter-08、chapter-09
- 来源路径：reports/operations/121Q25B-project-sync-contract.md；ITERATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明的 schema、工作流和运行范围；不能写成科学正确

### R0-042｜之元写作法 0.4.0

- 原始问题：如何让研究材料在可读、可感和可追溯之间移动？
- 新增认识：embodied anchor、vertical/horizontal movement、retro-illumination、材料池和反馈可形成写作工作法。
- 证据类型：writing method、editorial examples、dual-source pool
- 112 输出类别：`METHOD_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：写作法帮助把证据边界嵌入读者经验。
- 当前边界：它不是科学真理层，读者反应不是验证，术语不能机械翻译。
- 纠正/撤回/取代：0.3 integrated into 0.4.0
- 已有人类作品：方法文档
- 正文目的地：chapter-01、chapter-09、chapter-10
- 来源路径：docs/publication/zhiyuan-writing-method.md；reports/operations/121Q28-writing-method.md；reports/operations/121Q31-material-pool.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-043｜Q30 出版展示层

- 原始问题：人类作品、机器索引、形式化对象和来源链如何同时可读？
- 新增认识：研究展示可以把 human index、machine registry、formal work、source chain 和 analysis 分开并互相指向。
- 证据类型：publication showcase、provenance hash、public surface
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：出版层应同时服务阅读和追溯。
- 当前边界：展示完成不证明历史因果或写作法普适。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-09、chapter-10
- 来源路径：reports/operations/121Q30-publication-showcase.md；docs/publication
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-044｜Q31 system map

- 原始问题：如何把点火的研究、证据、写作和操作层画成一个不夸大的全局？
- 新增认识：双源材料池、9 groups、41 nodes 的 map spec 可以生成系统导航。
- 证据类型：JSON spec、generated system map、source typing
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY`
- 当前结论：地图能帮助读者定位层次和依赖。
- 当前边界：没有 L7；节点和边不证明跨域机制。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-08、chapter-09
- 来源路径：reports/operations/121Q31-system-map.md；data/operations
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明的 schema、工作流和运行范围；不能写成科学正确

### R0-045｜Q32 typed propagation

- 原始问题：一次研究变化怎样影响函数、断言、地图、文章和发布表面？
- 新增认识：实质因果候选、仓库依赖和同步义务可以分为不同 edge type；48 seeds、2 iterations、19 components、15 paths 等是局部运行证据。
- 证据类型：typed graph、propagation run、impact ledger
- 112 输出类别：`EMPIRICAL_OR_REPLICATION_RESULT`
- 当前有效性：`WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY`
- 当前结论：传播的可见性和回滚可以被工程化。
- 当前边界：零 residue 不证明注册表完整、未知依赖为零或机制成立。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：报告
- 正文目的地：chapter-08、chapter-09
- 来源路径：reports/operations/121Q32-typed-propagation.md；ITERATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明的 schema、工作流和运行范围；不能写成科学正确

### R0-046｜Q32I selective materialization

- 原始问题：传播结果如何选择性写入、缓存并回滚？
- 新增认识：116/116 aggregate local tests 等局部运行证据说明某次操作链可重放，且能隔离 materialization。
- 证据类型：local test suite、cache/rollback、phase report
- 112 输出类别：`EMPIRICAL_OR_REPLICATION_RESULT`
- 当前有效性：`WORKFLOW_OR_SCHEMA_EVIDENCE_ONLY`
- 当前结论：局部操作链的回滚与验证可以被审计。
- 当前边界：不等于真实机制、全仓完备或正式生命周期完成。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：报告
- 正文目的地：chapter-08
- 来源路径：reports/operations/121Q32I-selective-materialization.md；ITERATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：声明的 schema、工作流和运行范围；不能写成科学正确

### R0-047｜Pages/公共链接修补

- 原始问题：读者打开公共入口时如何避免陈旧链接和错误权威感？
- 新增认识：链接、首页、公开状态和来源指向可被逐项检查。
- 证据类型：link audits、public surface、CI
- 112 输出类别：`MAINTENANCE_ONLY`
- 当前有效性：`CURRENT_ASSET_WITHOUT_NEW_EXTERNAL_RESULT`
- 当前结论：公共链接真相是可维护的工程对象。
- 当前边界：Pages 不是权威事实层，页面可达不等于内容成立。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-08、chapter-09
- 来源路径：README.md；docs/project-current-state.md；outputs/audit
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-048｜Jin-rise pointfire analysis

- 原始问题：一个公共故事是否能被拆解成多机制、可反驳而不是单因果？
- 新增认识：S0–S4、L0–L6、替代机制、MCF/PSD/ARN 边界、Q12 action 和 ordered verification queue 可构成来源驱动的候选分析。
- 证据类型：source record、long analysis、countermodels
- 112 输出类别：`RESEARCH_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：叙事可以成为候选机制和验证队列的入口。
- 当前边界：部分数字、阈值和历史因果证据弱；不能把故事总结成已证机制。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：完整长文
- 正文目的地：chapter-01、chapter-07、chapter-10
- 来源路径：reports/publication/jin-rise-point-fire-analysis.md；docs/publication/cases/jin-rise-case-source.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-049｜when-an-army-believes-its-own-back

- 原始问题：如何把反馈、信念和自我强化写成普通读者可读的公共文章？
- 新增认识：以具体文本和来源链承载结构比直接输出术语更容易暴露类比边界。
- 证据类型：editorial article、source chain、boundary notes
- 112 输出类别：`MIXED`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：这是一篇可读的人类作品。
- 当前边界：不主张具体历史因果，也不证明写作法普适。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：完整作品
- 正文目的地：chapter-09、chapter-10
- 来源路径：docs/publication/works/when-an-army-believes-its-own-back.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-050｜Editorial articles 001–010

- 原始问题：怎样把研究/案例/写作实验逐步积累成公共作品？
- 新增认识：十篇文章形成了不同主题、叙事锚点和来源链的试验集。
- 证据类型：human-readable articles、editorial metadata、source links
- 112 输出类别：`MIXED`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：文章是知识成果的可读载体，但需单独审查其主张上限。
- 当前边界：文件数量不等于研究成果数量，文章中的类比不能自动变成机制。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-01、chapter-07、chapter-09、chapter-10
- 来源路径：docs/editorial/articles
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-051｜Jin rise case source

- 原始问题：第三方故事如何在不重发未授权内容的情况下进入研究？
- 新增认识：来源记录、内容哈希、出处和不复述第三方全文的边界可以单独保存。
- 证据类型：source record、SHA provenance、rights boundary
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：来源链是作品可审计性的必要基础。
- 当前边界：来源记录不等于来源事实被全面核验，也不等于历史因果。
- 纠正/撤回/取代：none
- 已有人类作品：来源卡
- 正文目的地：chapter-07、chapter-09
- 来源路径：docs/publication/cases/jin-rise-case-source.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-052｜统一理论不可能性撤回

- 原始问题：点火能否用单一系统证明四种相互作用不可能统一？
- 新增认识：现有点火模型没有构成“不可能统一”的总证明；其他统一路径仍开放。
- 证据类型：physics correction、Foundation gate、counterexamples
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：旧的强物理 no-go 结论撤回。
- 当前边界：撤回旧结论不等于证明统一可行。
- 纠正/撤回/取代：old claim withdrawn
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-08
- 来源路径：RESULTS/CORRECTIONS.md；docs/foundation/physics-asset-correction-20260729.md
- 来源提交：23f4702a0、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-053｜零门/零乘积语义收紧

- 原始问题：一个零结果是否意味着所有状态和信息都消失？
- 新增认识：应改写为 carrier-scoped product readout；零结果不自动消除其他载体、路径或历史信息。
- 证据类型：semantic correction、counterexample、Foundation
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：零门是声明载体内的读出结果。
- 当前边界：不能外推为所有系统的信息消失律。
- 纠正/撤回/取代：universal zero-gate claim corrected
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-04
- 来源路径：RESULTS/CORRECTIONS.md；FOUNDATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-054｜Gödel/Hodge/类比 no-go

- 原始问题：能否借数学定理或跨域类比直接封锁现实命题？
- 新增认识：Gödel、Hodge 或类比只能在其原始对象和证明边界内使用，不能自动推出跨域 no-go。
- 证据类型：claim audit、math boundary、correction list
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：数学词汇不能替代对象、假设和证明。
- 当前边界：相似结构仍可作为候选，但需要独立定义和证据。
- 纠正/撤回/取代：old no-go analogies blocked
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-02、chapter-03、chapter-04
- 来源路径：RESULTS/CORRECTIONS.md；FOUNDATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-055｜映射/图边不等于因果

- 原始问题：如果两个对象有边、路径或相似度，是否就能说一个导致另一个？
- 新增认识：map edges、network paths 和 correspondence 只能表示候选关系；因果需要干预、识别和领域证据。
- 证据类型：correction list、MCF/PSD/ARN boundaries、causal gate
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：关系表示和因果主张必须分层。
- 当前边界：没有真实干预或反事实识别就不能升级。
- 纠正/撤回/取代：old causal readings corrected
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-02、chapter-05、chapter-07
- 来源路径：RESULTS/CORRECTIONS.md；docs/architecture/multiscale-causal-fabric.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-056｜测试通过不等于外部真理

- 原始问题：CI、validator 或 benchmark 通过是否能证明理论和现实都成立？
- 新增认识：通过只在声明环境、输入、oracle 和版本内支持 workflow/implementation 层结论。
- 证据类型：correction list、benchmark、claim ceiling
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：工程绿灯和科学证据必须分开。
- 当前边界：不能从 CI 绿灯推出现实因果、普遍定律或价值结论。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-02、chapter-05、chapter-08
- 来源路径：RESULTS/CORRECTIONS.md；ITERATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-057｜registry closure 不等于全真

- 原始问题：注册表完整列出对象，是否意味着所有对象都正确？
- 新增认识：closure 只代表对象被登记、分类和处置；大量对象仍 pending、quarantine、heuristic 或 hypothesis。
- 证据类型：Foundation closure、disposition distribution、audit gates
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：会计闭合和科学闭合是两件事。
- 当前边界：注册表仍可能有语义错误和快照差异，需要人类审查。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-04
- 来源路径：reports/foundation-architecture/100-nonfunction-claim-evidence-lineage-closure.md；data/foundation
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-058｜Pages 不是 authority

- 原始问题：公共页面可访问是否意味着页面内容已经是正式事实？
- 新增认识：Pages 是展示和链接表面，权威需要回到提交、来源、运行产物和状态。
- 证据类型：link audit、public surface correction、repository state
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：页面可达性和事实权威必须分开。
- 当前边界：本地或远端页面可能陈旧，仍需取证。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-08、chapter-09
- 来源路径：RESULTS/CORRECTIONS.md；README.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-059｜OpenAlex coverage wording

- 原始问题：101/116 supported 是否能写成外部文献内容被验证？
- 新增认识：只能写成 DOI 元数据被匹配为 supported；8 partial 和 7 null 是结果的一部分。
- 证据类型：OpenAlex run、null analysis、claim ceiling
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：外部元数据交叉核验的成功与未知并存。
- 当前边界：没有论文内容、观点或机制核验。
- 纠正/撤回/取代：none
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-06
- 来源路径：reports/external-research/110-openalex-result.md；RESULTS/CORRECTIONS.md
- 来源提交：37c880c33、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-060｜Crossref 117/117 wording

- 原始问题：117/117 DOI 元数据响应是否能支持 117 篇研究的结论？
- 新增认识：117/117 只说明协议范围内字段可解析，1 个重复和 5 个年份修正增加了数据质量认识。
- 证据类型：Crossref run、pre-registration、audit
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：Crossref 结果是元数据工程结果。
- 当前边界：没有全文、内容和主张支持。
- 纠正/撤回/取代：INJECTED_VERIFIED wording corrected
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-03、chapter-06
- 来源路径：reports/external-research/104-source-quality-audit.md；evidence-program
- 来源提交：16f640045、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-061｜Apple sole-trigger claim

- 原始问题：苹果是否是牛顿发现重力的唯一直接触发？
- 新增认识：后来的回忆来源支持关联叙述，但不支持唯一直接触发、瞬间完整理论或流行影响细节。
- 证据类型：historical dossier、target audit、source conflict
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：历史 claim ceiling 只能到 memoir association。
- 当前边界：没有可执行目标、counterfactual 或足够 contemporaneous evidence。
- 纠正/撤回/取代：strong narrative claim downgraded
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-07
- 来源路径：data/operations/iterations/111/historical/EVIDENCE_DOSSIER.md；data/operations/iterations/111/TARGET_AUDIT.md
- 来源提交：bbed7e29d、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-062｜Function OS false-reject repair

- 原始问题：修复后的 1.0 是否允许删除原始失败？
- 新增认识：修复后的 bounded pass 和原始 false reject 必须并存，前者回答修复效果，后者回答真实缺陷。
- 证据类型：before/after benchmark、failure fixture、regression guard
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CORRECTED_OR_DOWNGRADED`
- 当前结论：修复不应清除失败史。
- 当前边界：没有跨域或生产环境覆盖。
- 纠正/撤回/取代：raw result superseded only by scoped repair
- 已有人类作品：已有可读材料：有
- 正文目的地：chapter-05、chapter-08
- 来源路径：function-os-candidate/v0.2/benchmark；reports/external-research/105-function-os-benchmark.md
- 来源提交：16f64004、1314ba80、9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-063｜Foundation count mismatch

- 原始问题：读者怎样理解公开页面与机器闭合产物的不同数字？
- 新增认识：同一研究层出现 5,663/7,051 函数与 17,333/17,626 断言两组快照，需要 source scope、生成提交和口径说明。
- 证据类型：README、closure summaries、migration summary
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：这是出版可见性和谱系缺口。
- 当前边界：在没有正式维护决策前不判定一组数字为权威。
- 纠正/撤回/取代：none
- 已有人类作品：审计记录
- 正文目的地：chapter-04、chapter-08、chapter-09
- 来源路径：README.md；data/foundation/function-assets/closure-summary.json；data/foundation/nonfunction-claims/closure-summary.json；data/foundation/migration-summary.json
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-064｜四种相互作用与量子引力

- 原始问题：跨域结构系统能否对真实物理统一、暗物质、暗能量和测量问题提供新证据？
- 新增认识：现有资产只能标记未解决问题和有限模型边界，不能给出物理新解。
- 证据类型：open questions、physics correction、literature gap
- 112 输出类别：`NO_RECOVERABLE_KNOWLEDGE_INCREMENT`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：物理统一仍是外部学科开放问题。
- 当前边界：点火不能把候选表示或有限代数结果写成物理答案。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：问题清单；需由本卷或附录明确承接
- 正文目的地：chapter-08、chapter-10
- 来源路径：RESULTS/OPEN-QUESTIONS.md；docs/foundation/physics-asset-correction-20260729.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-065｜跨域映射的独立验证

- 原始问题：何时可以把两个领域的结构候选说成严格 correspondence 或同构？
- 新增认识：需要对象本体、映射、结构保持、反例和领域专家/外部证据，而不是只靠图边或词汇。
- 证据类型：claim audit、architecture boundary、open question
- 112 输出类别：`NO_RECOVERABLE_KNOWLEDGE_INCREMENT`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：严格跨域映射仍未解决。
- 当前边界：现有 MCF/PSD/ARN 只提供表示候选和验证接口。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：问题清单；需由本卷或附录明确承接
- 正文目的地：chapter-08、chapter-10
- 来源路径：RESULTS/OPEN-QUESTIONS.md；docs/architecture
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-066｜真实世界反馈验证

- 原始问题：点火的反馈、压缩和锁定候选是否在真实系统中有可区分的干预预测？
- 新增认识：现有资产主要在内部模型、历史叙事和工程同步层，缺乏真实干预和可复制外部实验。
- 证据类型：open questions、claim ceiling、case gaps
- 112 输出类别：`NO_RECOVERABLE_KNOWLEDGE_INCREMENT`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：机制识别仍待外部研究。
- 当前边界：不能把内部一致性或叙事解释升级为 causal identification。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：问题清单；需由本卷或附录明确承接
- 正文目的地：chapter-07、chapter-08、chapter-10
- 来源路径：RESULTS/OPEN-QUESTIONS.md；ITERATION.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-067｜Function OS 神经/概率扩展

- 原始问题：有限符号函数执行器是否能涵盖神经、概率、连续或分布式函数？
- 新增认识：当前 scope contract 明确把这些列为 non-goals，外部文献也只给出部分支撑。
- 证据类型：scope contract、literature review、gap map
- 112 输出类别：`NO_RECOVERABLE_KNOWLEDGE_INCREMENT`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：Function OS 的能力边界本身是目前较清楚的否定性认识。
- 当前边界：扩展设计、语义和验证方案均未解决。
- 纠正/撤回/取代：none
- 已有人类作品：问题报告
- 正文目的地：chapter-05、chapter-10
- 来源路径：function-os-candidate/v0.2/scope-contract.json；reports/external-research/121-function-paradigm-fulltext-review-report.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-068｜出版单文件入口

- 原始问题：读者怎样不点击链接和 JSON 就看到全局？
- 新增认识：需要把当前支持、已纠正和未解决分别写成句子，并把边界紧邻每项结论。
- 证据类型：publication gap audit、human reading requirement、source map
- 112 输出类别：`MIXED`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：一页全景是知识成果而不是导航页。
- 当前边界：它不能消除历史冲突，只能把冲突显式化并给出来源。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：待本工程生成；需由本卷或附录明确承接
- 正文目的地：chapter-09、chapter-10
- 来源路径：01-百轮成果总台账.md；02-成果缺口与不可见性审计.md
- 来源提交：51e737667e9a39d943c80d428d1c424a218c84c5
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-069｜第一卷连续叙事

- 原始问题：如何让不了解仓库的读者从问题走到发现、纠正和未知？
- 新增认识：现有材料足够组成问题—证据—转折—未知的骨架，但尚无一卷连续正文。
- 证据类型：chronology、articles、reports、source ledger
- 112 输出类别：`MIXED`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：出版前置工程需要重新组织，而不是复制报告。
- 当前边界：字数和叙事完整不允许超过每章 evidence binder 的 claim ceiling。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：待本工程生成；需由本卷或附录明确承接
- 正文目的地：chapter-01、chapter-10
- 来源路径：RESULTS/CHRONOLOGY.md；docs/publication/zhiyuan-writing-method.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-070｜独立研究笔记体系

- 原始问题：如何把真正独立的问题和认识提供给读者，而不把总卷机械切碎？
- 新增认识：笔记应按问题主题组织，每条保留证据、边界和未决问题。
- 证据类型：publication design、ledger、open questions
- 112 输出类别：`MIXED`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：独立笔记可以作为读者的局部入口和审查索引。
- 当前边界：不能用相似段落改写来制造数量。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：待本工程生成；需由本卷或附录明确承接
- 正文目的地：chapter-08、chapter-09、chapter-10
- 来源路径：01-百轮成果总台账.md；RESULTS/OPEN-QUESTIONS.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-071｜事实/反方/编辑三重审查

- 原始问题：初稿如何在事实、过度主张和读者体验上被独立检查？
- 新增认识：三种角色需要不同问题和具体章节定位，不能用一句“整体不错”代替审稿。
- 证据类型：editorial protocol、claim ledger、review design
- 112 输出类别：`MIXED`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：审查是成果出版的一部分。
- 当前边界：本阶段尚未对未来第二稿完成审查；审查本身也可能遗漏问题。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：待本工程生成；需由本卷或附录明确承接
- 正文目的地：chapter-09、chapter-10
- 来源路径：docs/publication/zhiyuan-writing-method.md；02-成果缺口与不可见性审计.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-072｜真正的跨域机制识别

- 原始问题：如何从漂亮的对应关系走到可区分的机制和干预预测？
- 新增认识：需要预先声明对象、干预、反事实、替代机制、数据和失败标准。
- 证据类型：open question、claim ceiling、architecture candidates
- 112 输出类别：`NO_RECOVERABLE_KNOWLEDGE_INCREMENT`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：这是最重要的研究升级方向之一。
- 当前边界：当前仓库只提供部分表示和操作护栏。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：待研究；需由本卷或附录明确承接
- 正文目的地：chapter-08、chapter-10
- 来源路径：RESULTS/OPEN-QUESTIONS.md；docs/architecture/probabilistic-system-dynamics.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-073｜证据桥接与领域合作

- 原始问题：如何让历史、物理、工程、文学等领域的证据制度真正进入同一研究流程？
- 新增认识：统一的是接口和边界，不是把各领域的证据压成同一数值。
- 证据类型：evidence regime、external research gaps、open questions
- 112 输出类别：`NO_RECOVERABLE_KNOWLEDGE_INCREMENT`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：点火更接近研究协作基础设施，而不是独立学科的替代。
- 当前边界：需要真实领域专家、来源、数据和复制工作。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：待研究；需由本卷或附录明确承接
- 正文目的地：chapter-08、chapter-10
- 来源路径：docs/evidence_regime_library.md；RESULTS/OPEN-QUESTIONS.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-074｜计数与快照统一

- 原始问题：怎样让公开页面、机器闭合产物和历史快照说清楚它们各自统计什么？
- 新增认识：每个公共数字需要 scope、生成提交、时间、去重口径、状态定义和变更说明。
- 证据类型：visibility audit、closure summaries、public pages
- 112 输出类别：`MAINTENANCE_ONLY`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：数字谱系是出版可信度的基础设施问题。
- 当前边界：本包不替正式仓库维护者选择权威口径。
- 纠正/撤回/取代：none
- 已有人类作品：审计结果
- 正文目的地：chapter-04、chapter-09
- 来源路径：README.md；data/foundation/migration-summary.json；02-成果缺口与不可见性审计.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-075｜真实失败案例接口

- 原始问题：怎样把历史或现实案例变成有 target、I/O、oracle、重复失败和回归保护的实验？
- 新增认识：苹果案例显示，先问目标是否存在比先问故事是否正确更重要。
- 证据类型：task111 target audit、failure taxonomy、case status
- 112 输出类别：`NO_RECOVERABLE_KNOWLEDGE_INCREMENT`
- 当前有效性：`OPEN_OR_INCOMPLETE`
- 当前结论：失败案例的可执行化是连接出版叙事和工程实验的关键。
- 当前边界：没有目标时只能做来源和主张审计，不能虚构执行结果。
- 纠正/撤回/取代：none
- 已有人类作品：有审计，无实验
- 正文目的地：chapter-07、chapter-10
- 来源路径：data/operations/iterations/111/TARGET_AUDIT.md；case_failures
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：开放问题或出版缺口；不能写成已经完成的结果

### R0-076｜KNOWLEDGE 主题库

- 原始问题：研究过程中的定义、比较和边界如何被持续检索？
- 新增认识：主题知识库提供了跨任务、跨报告的概念连接和阅读入口。
- 证据类型：knowledge notes、indexes、crosslinks
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_ASSET_WITHOUT_NEW_EXTERNAL_RESULT`
- 当前结论：知识库是发现和导航层。
- 当前边界：内容仍要回到报告、源文件和提交核验。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-04、chapter-09
- 来源路径：KNOWLEDGE；RESULTS/RESEARCH-AND-ARTICLES.md
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-077｜outputs audit/research/stories

- 原始问题：如何把中间研究和故事产物从正式注册表中分开而不丢失？
- 新增认识：输出目录承载了研究、审计和叙事的中间/可读成果。
- 证据类型：output files、audit reports、story drafts
- 112 输出类别：`INFRASTRUCTURE_ONLY`
- 当前有效性：`CURRENT_ASSET_WITHOUT_NEW_EXTERNAL_RESULT`
- 当前结论：分层保存使研究过程可回看。
- 当前边界：输出目录中的每篇文件都需要单独判断状态。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：部分；需由本卷或附录明确承接
- 正文目的地：chapter-01、chapter-09
- 来源路径：outputs/research；outputs/audit；outputs/stories
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-078｜失败与 null 的正价值

- 原始问题：没有通过、没有目标、没有全文或没有 exact DOI 的结果是否有研究价值？
- 新增认识：false reject、target absent、fulltext 0 和 7 null 能阻止错误升级，缩小当前能说的范围。
- 证据类型：failed benchmark、null responses、fail-closed gate
- 112 输出类别：`CORRECTION_RESULT`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：负结果是边界知识。
- 当前边界：负结果不能自动告诉我们真实机制，只说明当前路线不能支持目标。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：分散在报告中；需由本卷或附录明确承接
- 正文目的地：chapter-02、chapter-06、chapter-07
- 来源路径：case_failures；reports/external-research；data/operations/iterations/111
- 来源提交：9b15d359c54694d851c38df6ab3c7ae42544a51b
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层

### R0-079｜后续恢复协议提交

- 原始问题：任务 111 后续恢复如何被识别而不误读成基线终态？
- 新增认识：后续候选提交显示了 recovery fixture 与 immutable terminal-tag protocol 的结构，但它们不改变本包固定基线。
- 证据类型：later Git history、candidate commits
- 112 输出类别：`MAINTENANCE_ONLY`
- 当前有效性：`HISTORICAL_NOT_CURRENT`
- 当前结论：后续历史可以帮助理解结构和缺口。
- 当前边界：未终态恢复状态不提升为 task111 formal completion，也不进入本包的基线结论。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：未作为正文证据；需由本卷或附录明确承接
- 正文目的地：chapter-08
- 来源路径：git history: c8249e855；git history: 16252c609
- 来源提交：c8249e855、16252c609
- 结论天花板：保存、导航、同步或维护能力；不产生自动外部知识

### R0-080｜成果与基础设施分离

- 原始问题：怎样回答哪些是新认识、哪些只是让研究能运行的设施？
- 新增认识：研究候选、纠正、实验、注册/同步/发布基础设施必须在台账中并列但不混称。
- 证据类型：whole-repo census、classification schema、source review
- 112 输出类别：`MIXED`
- 当前有效性：`CURRENT_WITH_EXPLICIT_LIMITS`
- 当前结论：分类本身是出版前置工程的核心产出。
- 当前边界：很多对象是混合成果，必须逐项说明哪一部分是认识、哪一部分是设施。
- 纠正/撤回/取代：none
- 已有人类作品：人类作品状态：本台账；需由本卷或附录明确承接
- 正文目的地：chapter-01、chapter-09、chapter-10
- 来源路径：01-百轮成果总台账.md；01-百轮成果总台账.jsonl
- 来源提交：51e737667e9a39d943c80d428d1c424a218c84c5
- 结论天花板：当前来源和版本可支持的窄结论；不超过其证据层
