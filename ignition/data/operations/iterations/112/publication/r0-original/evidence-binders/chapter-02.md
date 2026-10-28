# Chapter 02 Evidence Binder：为什么能解释不等于已经证明

## 章节核心问题

一个结构模型可以把材料解释得很顺，为什么这还不等于它已经证明了什么？本章要建立读者最重要的判断工具：解释是一种组织材料的能力，证明、因果识别、外部事实和工程通过则是不同的证据事件。

## 可支持的认识

1. `docs/evidence_regime_library.md` 将数学证明、物理理论/实验、历史来源交叉核对、医学证据、法律文本与程序、工程测试和文学/艺术语境分开。
2. `FOUNDATION.md` 明确区分了 FUNCTION、THEOREM、ISOMORPHISM、CAUSAL 和 PROVED backend 的门槛；有限模型、样本或符号化简不能自动证明普遍命题。
3. `ITERATION.md` 使用 claim ceiling 区分 artifact_created、schema_validated、workflow_passed、implementation_observed、mechanism_plausible、mechanism_discriminated、causal_identification_pending 和 insufficient_evidence。
4. MCF/PSD/ARN 的架构说明都强调：网络、路径、图谱、相关概率或表示映射不能取代干预、识别或领域证据。
5. `RESULTS/CORRECTIONS.md` 已把“测试通过不等于外部真理”“映射边不等于因果”“registry closure 不等于全真”列为当前防护。

## 不可支持的强说法

* “系统有一个漂亮的解释，所以机制已被证明。”
* “形式化工具运行成功，所以现实对象成立。”
* “两个领域共享节点和路径，所以存在严格同构。”
* “CI 绿灯、地图生成或 1.0 benchmark 证明了跨域理论。”
* “一个来源被 API 找到，所以来源内容支持研究主张。”

## 来源与提交

* `docs/evidence_regime_library.md` — 基线 `9b15d359c54694d851c38df6ab3c7ae42544a51b`。
* `FOUNDATION.md` — 基线；L0–L6、权威与数学/因果 gate。
* `ITERATION.md` — 基线；当前方法 1.4、claim ceiling 和候选/合并/当前区分。
* `docs/architecture/multiscale-causal-fabric.md`、`probabilistic-system-dynamics.md`、`adaptive-relational-network.md` — 基线。
* `RESULTS/CORRECTIONS.md` — 基线；纠正链。

## 相互冲突的历史版本

|版本|看起来能说|必须降到|
|---|---|---|
|早期“统一结构”|同构、因果、普遍规律|候选对应或结构类比|
|形式化资产|已证明某个现实命题|声明模型内有限结果/反例|
|Function OS 通过|所有函数都可执行|bounded symbolic deterministic scope|
|外部来源回收|文献内容已核验|metadata/abstract/fulltext/claim support 分层|

## 关键数字

* Foundation 的有限工具链包含 Lean 4.19、SymPy 1.14、Z3 4.16；版本信息只说明工具环境。
* Foundation 中既有 M0/M1/M2/M3/M4/M6 等数学成熟度，也有大量 pending/quarantine；成熟度不是现实真理等级。
* claim ceiling 至少有 8 个可区分状态；正文应使用自然语言解释而非只贴枚举。

## 反例

* 在 `Z/6Z` 中 `2×3=0` 可以成立，但不能由此推出所有物理系统都有同样的零乘法语义。
* 一个网络存在从 A 到 B 的路径，不说明现实中干预 A 会改变 B。
* 文章在不同领域都使用“压缩”一词，不说明它们有相同的操作、成本或反事实。
* 对同一 DOI 两个元数据源都返回记录，不说明论文内容互相支持。

## 开放问题

* 什么样的桥接实验能把内部模型与外部领域证据连起来？
* 如何把“机制合理”与“机制可区分”落实为预注册的失败标准？
* 普通读者怎样感受证据层级，而不是只看到“证明/未证明”的二元对立？

## Claim ceiling

本章可以支持的是证据分层原则，以及点火已经建立了一套自我限制的表示和状态工具。它不支持任何跨域现实机制已被证明。可写到 `schema_validated`、`workflow_passed` 和局部 `implementation_observed`；涉及现实因果时应停在 `causal_identification_pending` 或 `insufficient_evidence`。

## 可进入正文的材料

应选一个读者熟悉的转折：同一张图或同一个模型可以让两个事件“看起来相似”，但当我们询问干预、反事实、测量和替代解释时，答案开始分岔。用一个有限形式化反例和一个图边反例，让读者实际感到解释与证明之间的距离。随后引入 claim ceiling，作为贯穿全卷的语言工具。

## 只能放附录的工程信息

工具版本、schema 字段、validator 名称、测试命令、对象 ID、L0–L6 全部枚举、报告间交叉链接可放来源附录。正文只保留能帮助读者作判断的最小例子。

