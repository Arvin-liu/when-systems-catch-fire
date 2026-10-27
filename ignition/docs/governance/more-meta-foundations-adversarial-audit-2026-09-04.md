# 153 反证轮：双基础最小性、A 的归属与跨合同诊断承载力

Status: `RESEARCH_RECORD / ADVERSARIAL_AUDIT / NON_CANONICAL`

Task: `IGNITION-20260904-154`
Predecessor: `IGNITION-20260904-153`, candidate head `08c837cd5d74b9ac14dcea7288c77786e10e3bac`
Baseline: `when-systems-catch-fire` `main@212322d41db79bce2dbd116166d3f1ad226291f3`
Scope: 只反证 153 的 `ORTHOGONAL_DUAL_FOUNDATION / NO_NEW_CANONICAL_LAYER` 候选综合；不修改现有治理合同、运行时、权限、schema、registry 或 Current 身份。

## 1. 结论先行与证据等级

### 1.1 主判定

本轮主判定为：`FALSIFIED`。

这里被反证的是“`P/O/N/A` 与五源 role topology 构成一个最小且正交的双基础”这一强命题，不是对当前 Charter、Claim Ceiling、Kernel、Approval、Runtime、Stage Snapshot 或 OS Steering 合同的否定。逐项消融显示：

1. `P`、`O` 和 `A` 都可以被现有合同或已有跨合同关系重新承载；它们没有显示出必须作为新 primitive 才能提供的独立判定。
2. `N` 保留了一个不能从证据逻辑推出的规范边界，但它是 Charter 的价值约束，不是由本轮材料证明的通用基础 primitive。
3. `A` 最多是 authority source、accountability sink、contest path 与 stop/revocation 的连接条件；它可拆分、可挂接已有合同，不能作为独立基础层。
4. 五个诊断词可以指出合同交界处的审计问题，但尚未被独立 fixture、稳定 predicate 或重复测试证明为新的 failure class。

因此更窄的保留判定是：`SURVIVES_AS_HEURISTIC_ONLY`。`P/O/N/A` 与五源 loop 可以继续作为不改变状态的 review vocabulary；`NO_NEW_CANONICAL_LAYER` 作为本轮治理决策仍成立。这里的 `FALSIFIED` 不授权任何继任任务、字段或权限。

### 1.2 证据标记

- `OBSERVATION`：当前仓库文件、schema、实现或已有 validator 直接表达的内容。
- `COUNTERMODEL`：用当前字段形状构造的最小反例；它是逻辑测试材料，不是实际生产事件，也不表示某个 workflow 已经通过。
- `INFERENCE`：由观察和反例得到的有边界分析。
- `VERDICT`：本轮对 153 候选命题的判定。
- `OPEN`：还没有可重复 fixture 或独立复核，不能升级为新 failure、事实或规范。

## 2. 反证方法与最小性门

153 的强命题要成立，至少需要同时满足以下五个条件：

|门|可接受的最小证据|本轮判定口径|
|---|---|---|
|独立性|移除 primitive 后，不能由现有合同和其余 primitive 保留同一独立工作。|若现有合同已经承载该工作，候选只算重命名或导航词。|
|非循环|primitive 不能用自身定义的 authority、ceiling 或“需要该 primitive”来证明自身必要。|用源文件与 schema 的先验字段，不用 153 的结论回证 153。|
|可操作性|有输入、输出、failure trigger、适用域和 falsifier。|没有稳定 predicate 时最多是 review lens。|
|非扩权|引入后不能无意中授予新的 authority、execution 或 Current 传播效果。|任何新字段/registry/validator 都必须另走制度化任务，本轮不做。|
|独立增量|相对于现有 federated contracts，能减少可重复的漏检或误判。|单纯把多个已有字段放在一张图上不算新 failure reduction。|

本轮只做离线文档与仓库内结构分析。没有把 synthetic countermodel 伪装成运行结果，也没有把 schema 能承载某字段误写成该字段已被治理使用。

## 3. R1：P/O/N/A 逐项消融

### 3.1 消融矩阵

|移除项|模型层面立即失去的解释|现有合同能否重新承载|不能被重新承载的残余|独立 primitive 判定|
|---|---|---|---|---|
|`P` provenance-bounded assertion|不能用一个短标签同时表达 source、M/E、claim ceiling、依赖、独立性和公开措辞限制。|能。Claim Governance、Kernel K13、Non-Sycophancy 和 human-surface 规则已经分别承载来源、成熟度、上限、非升级与措辞边界。|仍缺少“某一 action 的选择是否由该 claim 的 ceiling 支持”的跨合同绑定；这属于交叉审查问题，不证明新 primitive 必要。|`REDUNDANT_AS_PRIMITIVE / SURVIVES_AS_REVIEW_LABEL`。|
|`O` option preservation|不能用一个词把 abstain、pause、stop、rollback、reconcile 和保留未来选择联系起来。|大部分能。Charter Gate、Runtime rollback/reconciliation、Attention Attractor 的 `NO_INFORMATION_GAIN` 与 Steering 的暂停/重审路径已有对象局部规则。|等待的期限、下一证据、机会成本和责任承载没有一个通用闭环；适用域仍是对象化的。|`COMPOSITE_HEURISTIC / NO_INDEPENDENT_STATE`。|
|`N` non-domination / non-externalization|失去一个对风险承担者、沉默主体、维护者和未来参与者可见的规范性压缩词。|不能由 P 或五源 topology 推出；但 Charter 已直接承载受影响者、不可逆性、残余伤害、拒绝与回滚边界。|具体权重、冲突优先级和跨域可比性仍未定义；它不能自动变成一个分类器。|`VALUE_PREMISE_RETAINED / NOT_A_PROVEN_UNIVERSAL_PRIMITIVE`。|
|`A` accountable authorization|不能在一张图上把合法 authority、approval/consent、contest path、责任 sink 与技术 execution 的分离叫作一个名字。|能。OS Steering、Approval Bridge、Stage Snapshot、responsibility actor registry、Runtime trace 已把这些接口分开表达。|通用的“批准者看见了哪些后果并拥有怎样的争议路径”没有连接 predicate；这说明闭合审查缺口，不说明 A 是独立基础。|`DECOMPOSABLE_BRIDGE / NOT_AN_INDEPENDENT_FOUNDATION`。|

### 3.2 逐项反例说明

#### `P`：有来源不等于需要 P 作为新基础

`OBSERVATION`：Claim Governance 的记录已经要求 definition、source、M/E、evidence、dependencies、claim ceiling 与 dispositions；Kernel 又规定重复、规模、工程完成、跨域对应和共识不能自动升级断言。`P` 对这些关系作了有用的压缩，但压缩词没有独立输入或独立状态。

`COUNTERMODEL`：一个 claim 已有 source anchor、M/E 和 public ceiling，另一个 action packet 已有 `source_plan_hash`、requested scope、validator refs 和 reason summary。删除 `P` 这个名字，两个已有合同仍然可以分别运行；真正丢失的是“claim → action”是否闭合的复核问题。结论是跨合同 lens，而非新的 epistemic primitive。

#### `O`：保留选项是关系族，不是统一状态

`OBSERVATION`：Runtime 只对 `ROLLBACKABLE_LOCAL_FILE` 的有界 preimage 做回滚；未知副作用进入 reconciliation；Attention 控制器把无信息增益和 attractor 风险分开；Steering 的 deadline、blocked、unknowns 和 human review 也已有局部承载。

`COUNTERMODEL`：对一个没有外部后果、可随时撤销的本地格式化动作，立即行动和短暂 pause 都不改变风险或未来选项。此域中没有必要引入 `O` 才能做安全选择。反例不否认高后果动作需要 stop/rollback，只否认“所有对象共享一个 O 基础”。

#### `N`：不可从事实逻辑推出的部分应留在 Charter

`OBSERVATION`：生命共同体 Charter 明确要求记录 beneficiaries、risk bearers、silent subjects、consent/participation、irreversibility、evidence threshold、reject/rollback 与 residual harm。它是规范性输入，不是 evidence 的推论。

`COUNTERMODEL`：两条路径拥有完全相同的 source、claim ceiling、approval、lease 与 rollback 能力，但一条把不可逆代价转给未参与的风险承担者，另一条没有该外部化对象。P/O 和五源 topology 不能区分这两条路径；只能由 Charter 语境判定。因而 `N` 有不可约的价值来源，但没有被证明为跨对象、可计算、独立于 Charter 的基础。

#### `A`：authority–accountability 的连接不等于新层

`OBSERVATION`：`approval-decision-r1` 记录 `authority_id`、`authority_type`、`decision` 和 action digest；Stage Snapshot 的 `actor_ref` 只接受 active `PERSON` / `ORGANIZATION`，技术 actors 另列；Runtime trace 的 `actor_id` 是技术事件引用。三组记录之间已经存在角色分离。

`COUNTERMODEL`：Approval 可以是 `ALLOW`，actor_ref 可以有效，Runtime 也可以完整记录 trace，但这不自动给出 consequence view、contest/refuse path 或理解证明。这个反例说明连接处需要复核；它同时证明 A 不是一个不可拆分的原子，而是若干既有接口的闭合条件。

## 4. R2：A 的五个归属假设

本节的 A 专指 153 的 `accountable authorization` 工作标签，不把它写入任何 schema。

|假设|来源与支持|反例|循环性检查|独特工作|可证伪条件|判定|
|---|---|---|---|---|---|---|
|`H-A1` A 是独立 primitive|153 把合法 authority、consent、contestability 与责任 sink 压成一个基础。|Approval、Stage Snapshot、OS Steering 分别能承载批准者、actor_ref、Owner transition 与技术执行分离；删除 A 名称不删除这些字段。|不能用“没有 A 就没有 accountability”证明 A；这正是待证明结论。|提供一个跨合同 closure question：谁批准、谁执行、谁承载后果、谁能争议。|存在至少一个现有合同无法表达且 A 单独能稳定阻断的高后果 case。|`FALSIFIED_AS_INDEPENDENT_PRIMITIVE`。|
|`H-A2` A 只是 topology|五源 loop 能表示 authority source、execution source、accountability sink、stop/rollback source。|Topology 能标注“有节点/边”，不能决定批准是否合法、是否超出 scope 或是否符合 Charter。|若把合法性直接定义成 topology 完整，就把需要证明的规范结论藏进图结构。|保留角色与边的可见性，避免把技术 actor 误认为 authority。|一个仅有完整节点边的图能稳定处理 Charter conflict 且不引入额外规范输入。|`FALSIFIED_AS_COMPLETE_PLACEMENT`；topology 只承载结构面。|
|`H-A3` A 是 bridge/closure condition|A 连接 evidence/claim、authority、execution、accountability、contest/stop。|连接关系可能随对象局部 contract 改变；没有一个跨所有对象的闭合谓词。|只要不把“闭合”定义为 A 自身存在，就不会循环。|指出现有合同之间需共同审查的 edge。|在多个对象族中，同一闭合检查可不依赖具体 schema 且稳定改善漏检。|`SURVIVES_AS_CROSS_CONTRACT_REVIEW_LENS`。|
|`H-A4` A 可拆为 authority/consent/accountability|Approval、Owner Intent、actor registry、review/contest、stop/revocation 是不同来源。|`ALLOW` 不等于 consent；actor_ref 不等于 signer comprehension；technical execution 不等于 accountability sink。|拆分后每项均有独立来源，循环性下降。|把“谁能授权”“谁被影响”“谁承载责任”“谁能争议”分开。|若所有对象都能由单一字段无损替代四项，才会反驳拆分。|`SUPPORTED_AS_DECOMPOSITION`。|
|`H-A5` A 完全冗余于 Owner/Approval/Stage Snapshot|现有合同已经有 Owner、Approval、actor_ref 和 lifecycle。|这些合同在不同表面各自闭合，未必有 generic consequence view、contest path 或 action binding。|不能把“有字段”当作“跨表面已闭合”；需检查连接。|暴露剩余的 junction risk，而不是新 authority。|所有 strengthened tests 在现有 validators 中均有同一明确 predicate。|`PARTIALLY_FALSIFIED`：基础命题冗余，闭合问题未决。|

### 4.1 不带 A 的 Track B 检查

用 `P/O/N + role topology`，不使用 A 这个名称，能得到：

- `能得到`：能力不等于授权（Kernel、Approval、Runtime 的显式边界）；技术执行者不等于责任引用（Stage Snapshot / actor registry）；Owner transition 不能从 Agent、CI、receipt 或重复输出推断（OS Steering）。
- `部分能得到`：是否存在一个 responsibility sink。若对象本身进入 Stage Snapshot 发布合同，`actor_ref` 是硬字段；若只是 runtime run，trace 的 `actor_id` 只是技术 actor，不能推出治理责任已闭合。
- `不能得到`：批准者是否看见具体后果、是否有 contest/refuse path、等待是否造成可避免损害、claim ceiling 是否支撑 action choice。这些需要把多个已有合同一起审查。

`VERDICT`：A 不承担新的事实内容；它只是把“跨合同是否闭合”命名。最小保留形式是 junction review question，不是 primitive、layer 或 registry record。

## 5. R3：正交性的操作定义与四象限

### 5.1 “正交”必须是操作性命题

本轮把 strict orthogonality 定义为同时满足：

1. 两侧输入来源不同，且一侧的输入不是另一侧的派生字段；
2. 两侧输出的 disposition、authority effect、claim effect 和 stop effect 可以分别判定；
3. 移除一侧不会改变另一侧的 failure trigger；
4. 一侧不需要另一侧的合法性、后果或角色边来解释自己的结果；
5. 两侧各自都有适用域、反例和可复核的证据入口。

在这个定义下，153 的“正交”只在“分析视角不同”这个弱意义上成立；在 action、approval、stop、accountability 的交界处并不成立。

### 5.2 四象限 synthetic countermodel

|Track A：P/O/N 约束|Track B：authority–execution–accountability topology|最小例子|通过/失败含义|
|---|---|---|---|
|PASS|PASS|source、M/E、ceiling 和 Charter residual-harm boundary 完整；Owner/approval、lease、executor、actor sink、stop/rollback 与 contest review 均有明确引用。|只表示两组既有合同在该案例中可以共同闭合；不证明 dual foundation。|
|PASS|FAIL|claim 来源和 ceiling 合格，且没有把预算写成价值许可；但 action 有批准和 executor，却没有可解析的 accountability sink 或 contest path。|证明 epistemic boundedness 不能推出 topology closure；是 cross-contract review case。|
|FAIL|PASS|Owner/approval、lease、actor、trace、stop/rollback 都完整；但 public wording 或 action choice 使用超过 source ceiling 的 claim。|证明 topology 完整不能修复 epistemic overclaim；P-side failure 独立存在。|
|FAIL|FAIL|source/ceiling 缺失或越界，同时 approval/actor/stop 也未闭合；只能停止、降级或要求重审。|两个局部面都失败；不能作为正交性证据。|

以上四例是 schema-shaped countermodels，不是仓库中已经观察到的执行事件。它们的用途是检验“一个侧面的 PASS 是否蕴含另一侧面的 PASS”；答案是否定的，但“不蕴含”不等于“存在两个基础”。

### 5.3 四个指定耦合反例

|反例|为什么破坏 strict orthogonality|现有合同承载|本轮结论|
|---|---|---|---|
|epistemically grounded but authority broken|source 和 ceiling 可以全对，但没有合法 Owner/approval、授权 scope 或责任沉点；P-side PASS 不产生 action permission。|Claim Governance / Kernel 与 OS Steering / Approval / Stage Snapshot 分离承载。|`ORTHOGONALITY_METAPHOR_REJECTED`；两侧可分诊断，不可称为独立基础。|
|authority complete but evidence/ceiling fails|signer、approval、lease、actor、stop 都完整，仍可能出现 source 不足或 wording 超 ceiling。|Approval/Runtime 不检查 claim ceiling；Claim Governance 另行约束。|相互不可还原，但耦合于同一 action review。|
|N changes authorized space|即使 capability 与 approval 交集非空，Charter 对风险承担者、沉默主体、不可逆性和残余伤害的判断仍可拒绝或收窄动作。|Charter Gate、Approval intersection、Policy compiler 的 forbidden effects/deny。|N 不是 topology 的派生项，也不是与 authorization 无关的独立轴。|
|contestability/rollback relies on O|有争议的决定需要保留拒绝、暂停、回滚、重审或未来选择；没有 option path，contest 只是记录。|Runtime rollback/reconciliation、Charter reject/rollback、Attention stop/review。|O 是跨合同关系族；它与 A 的 contest/stop edge 相连。|
|P changes signer information|source、claim ceiling 或 evidence scope 变化可能要求重新评估是否能授权、是否应扩大动作或是否应撤回。|Claim delta / impact / evidence lineage 与 approval/action digest 分开。|P 的变化可能改变 authority review 输入，strict orthogonality 失败。|

## 6. R4：五个候选诊断的承载力

### 6.1 现有字段与缺口

|候选诊断|现有局部合同已覆盖|schema-shaped countermodel|真正缺失的连接|新颖性/等价性|子判定|
|---|---|---|---|---|---|
|`PROVENANCE_WITHOUT_CEILING`|Claim record 可有 source/evidence/M-E/ceiling；action packet 有 `source_plan_hash`、reason、validator refs。|claim 有合法 source，但 packet 的 reason 或 public wording 没有引用该 claim 的 ceiling；每个局部记录仍可完整。|claim-to-action / claim-to-wording binding。|不是新的 provenance 或 ceiling；是已有字段的 junction test。|`CROSS_CONTRACT_LENS`。|
|`ABSTENTION_AS_AVOIDANCE`|Runtime 有 STOP/BLOCKED/RECONCILIATION；Steering 有 deadline state、blockers、unknowns；Attention 有 `NO_INFORMATION_GAIN`/`RUMINATION_RISK`。|记录了 stop/pause reason，却没有 review time、next evidence、等待代价、责任 actor 或 contest path。|abstention reason → next evidence → deadline → responsible actor → contest。|不是新 stop state；需要证明某一高后果对象缺少该闭环才构成 failure。|`CROSS_CONTRACT_LENS`，且 fixture 尚 `OPEN`。|
|`BUDGET_AS_HARM_LICENSE`|Policy compiler 对预算取 minimum、对禁止效果取 union；Charter 保留 residual harm、irreversibility 与 reject/rollback；Runtime budget 是资源上限。|“budget_available=true” 被叙述成可接受代价；局部 policy 可能允许资源消耗，但不能产生 Charter consent。|resource budget → normative residual-harm review 的语义防串线。|现有 Charter 与 forbidden effects 已否定该推论；诊断主要是反误读护栏。|`REDUNDANT_AS_FAILURE_CLASS / RETAIN_AS_WARNING_LENS`。|
|`SIGNATURE_WITHOUT_CONTESTABILITY`|Approval decision 有 authority、decision、action digest；Stage Snapshot 有 active `actor_ref`；Runtime trace 有技术 `actor_id`。|签字/ALLOW、actor_ref、consequence-free-looking summary 都存在，但没有 consequence view、范围异议、refuse/withdraw path，也没有自动理解判断。|approval event → consequence view → contest/refuse/revoke path。|不是 signer 身份新定义；是 approval、Charter、Stage/Review 的交叉测试。|`CROSS_CONTRACT_LENS`。|
|`COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY`|Trace event 必须有技术 `actor_id`、summary、refs；Stage Snapshot 在发布场景要求 accountable `actor_ref`；logs/journal 有前后状态。|事件、artifact、trace、approval 都完整，但只有 service/runtime actor，没有可解析的 responsibility sink。|technical causal record → accountable actor → consequence/contest path。|单个日志 schema 不能推出 governance responsibility；不是给 log 增加权力。|`CROSS_CONTRACT_LENS`。|

这里的 `CROSS_CONTRACT_LENS` 不是 `NEW_FAILURE` 的替代性断言：它表示当前材料足以说明“应将几张既有表面一起复核”，但没有独立复现证明该名字对应一个新的、稳定的错误类。

### 6.2 强化后的签名测试

在任何未来 review fixture 中，只有同时满足以下项目，才能说 approval path 至少完成了“可争议授权”这一问题的一部分：

1. 存在 approval event，并绑定 exact action digest、scope、expiry 与 decision；
2. signer/authority 能解析为当前合同允许的 authority 来源，而不是仅有字符串或技术 actor；
3. signer 在作决定前能看到该 action 的影响摘要、risk bearers、不可逆性、证据/ceiling 和预计后果；
4. 有明确的 contest、refuse、pause、withdraw 或 rollback 路径，且路径的责任承载者可解析；
5. 不把“是否理解全部后果”交给自动分类器或 `ALLOW` 字段推断。

当前 `approval-decision-r1` 明确支持第 1 项的一部分；Stage Snapshot 支持特定发布场景的第 2 项；第 3–5 项没有一个通用 joined predicate。由于本轮没有实际 high-consequence fixture，不把它命名为已证实的新 failure，也不新增字段。

### 6.3 强化后的 abstention 测试

对 `STOP`、`ABSTAIN`、`PAUSE`、`REQUIRES_RECONCILIATION` 或等价表达，未来至少要逐项问：

1. 为什么现在不行动，具体阻塞是哪一个证据、权限、后果或状态条件？
2. review time / deadline 是什么，逾期谁重新判断？
3. 下一条目标证据或可减少不确定性的动作是什么？
4. 等待的机会成本、可避免伤害或失去窗口是什么？
5. 谁承载等待期间的责任，谁能 contest 该等待？
6. 等待是否真的保留了 future option，还是只把决定移出可见范围？

Runtime 的 stop summary 能保存原因，Steering 能保存 deadline/unknowns，Stage Snapshot 能保存责任主体；它们尚未构成对所有对象的统一 joined record。若没有实际用例证明一个字段能改变 disposition，就不应先加 schema。

## 7. R5：冲突仲裁的真实残余

下表把当前路径、primitive 能做的工作与不能自动解决的部分分开。`priority` 不是普遍 precedence；当前 OS Steering 已明确在不可比时保留候选、理由、reconciliation 与 human review。

|冲突|当前路径|P/O/N/A 能否解决|仍需的优先级/语境/人类判断|残余|
|---|---|---|---|---|
|Evidence vs window|Claim ceiling、evidence lineage 与 Steering deadline/why-next 分开。|`P` 能收窄措辞；`O` 能要求 pause；不能单独决定“窗口关闭前是否必须行动”。|对象风险、Charter Gate、Owner/affected-party context 与明确 deadline。|无 universal order；若不可比，fail closed 或进入 scoped review。|
|Negative Capability vs avoidable neglect|Runtime/Attention 支持 stop、reconcile、no-information-gain；Steering 保存 blockers/unknowns。|`O` 能要求说明等待；不能给等待造成的机会成本排序。|谁承受等待后果、是否存在低风险替代动作、是否有救济/复审。|“不行动”不自动等于审慎，也不自动等于失职；当前没有通用判定。|
|Risk budget vs non-externalization|Policy compiler 对 resource budget 取最小；Charter 对 residual harm、irreversibility、拒绝/回滚另判。|`N` 可阻止把 budget 写成价值许可；不能生成具体 harm weight。|Charter/Owner/affected-party context；必要时拒绝或收窄 action。|预算永远不是 consent、truth 或 harm quota；不需新 arbitration layer。|
|Owner vs distributed epistemic contribution|OS Steering 让 contributors 提案/评估，Owner 承载明确 authority；Kernel 保持来源独立。|`P` 可保留不同来源和 dissent；`A` 可标 authority source/sink；不能把贡献者共识变成 Owner authority。|Owner transition、independent review、Charter conflict procedure。|Owner 不是唯一 evidence source，contributor 也不是授权者；二者不可互换。|
|Reversibility vs irreversible necessary action|Runtime 只承认声明的 rollback class；Charter 先问 irreversibility、reject/rollback、residual harm。|`O` 可要求保留选项；不能把不可逆动作变成可逆。|具体对象、必要性、受影响者、补救/补偿/停止路径与显式 authority。|“有 rollback 字段”不等于现实可逆；无真实 preimage 时必须改用拒绝、停止或残余记录。|
|Audit completeness vs real-time response|Journal/trace 追求 durable record；Runtime lease/timeout/stop 处理实时边界。|`P` 让记录可复核；`O` 允许先停；不能保证记录完成与实时动作同时达成。|预声明 bounded emergency envelope（若已存在）、risk class、post-action review；否则等待/停止。|没有新 primitive 能消除时间与审计的物理冲突。|
|Contestability vs emergency delegation|Approval Bridge 只允许 predeclared capability/approval intersection；delegated technical scope 不替代 Owner。|`A` 可暴露 contest/refuse/sink 缺口；`O` 可要求撤回/复核；不能创造紧急 authority。|紧急范围、expiry、affected-party safeguards、事后复核与真实责任主体。|没有通用 emergency/comprehension contract；不能以自动授权填补。|

`VERDICT`：当前确有若干需要 human/context arbitration 的残余，但它们不能证明一个更深的统一仲裁层。把优先级、语境和责任写进具体已有合同，比新增 meta-meta layer 更小。

## 8. 综合 verdict 表

|审计面|子判定|解释|
|---|---|---|
|`P` minimality|`REDUNDANT_AS_PRIMITIVE`|现有 claim/provenance/ceiling 合同保留其工作；只缺 claim-to-action junction review。|
|`O` minimality|`HEURISTIC_ONLY`|是 stop/pause/rollback/reconciliation 的关系族；没有统一状态或跨域必要性。|
|`N` minimality|`VALUE_PREMISE_RETAINED`|Charter 规范边界不能由 P 或 topology 推出，但没有通用 primitive 证明。|
|`A` minimality|`DECOMPOSABLE_BRIDGE`|可拆为 authority source、approval/consent、accountability sink、contest/revocation。|
|A placement|`CROSS_CONTRACT_JUNCTION`|不属于独立 foundation；属于既有合同间的 closure question。|
|orthogonality|`ORTHOGONALITY_METAPHOR_REJECTED`|分析轴可分开，action/authorization/contest/rollback 中存在耦合。|
|`PROVENANCE_WITHOUT_CEILING`|`CROSS_CONTRACT_LENS`|需要 claim-to-wording/action 的 joined review；无新 primitive 证据。|
|`ABSTENTION_AS_AVOIDANCE`|`CROSS_CONTRACT_LENS / OPEN`|可形成 review question；缺少重复 fixture 和通用适用域。|
|`BUDGET_AS_HARM_LICENSE`|`REDUNDANT_AS_FAILURE_CLASS`|已有 Charter/policy 边界否定该推论；保留为反误读提醒。|
|`SIGNATURE_WITHOUT_CONTESTABILITY`|`CROSS_CONTRACT_LENS`|身份/批准存在不等于后果可见与可争议闭合。|
|`COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY`|`CROSS_CONTRACT_LENS`|technical trace 完整不产生治理 responsibility sink。|
|arbitration gap|`REAL_RESIDUE / NO_NEW_LAYER`|需要 scoped human/context arbitration；没有统一 precedence 证明。|
|153 primary synthesis|`FALSIFIED`|强的 `ORTHOGONAL_DUAL_FOUNDATION` 不满足最小性与正交性门。|
|保留价值|`SURVIVES_AS_HEURISTIC_ONLY`|现有联邦合同加交叉视图仍有审计价值，但不改变 canonical。|

## 9. 反反弹门与明确不编码

以下结果不能从本轮反证反向推出：

- `FALSIFIED` 不等于现有 Charter、Kernel、Approval、Runtime 或 Stage Snapshot 失败；它只否定 153 的强综合模型。
- 诊断词出现于本文不等于当前仓库已经有对应 failure record、validator、schema 字段或生产缺陷。
- “存在 junction gap”不等于应该创建 L7、meta-meta protocol、universal arbitration 或统一价值函数。
- `N` 的价值来源不能被改写成自动 harm classifier；`O` 不能被改写成一律等待；`A` 不能被改写成一张隐藏权限表。
- approval、actor、trace、CI green、完整日志和 generated projection 仍不能互相升级为 truth、authority、Current 或 acceptance。

本轮明确不做：

1. 不新增 `P/O/N/A`、五源 loop、comprehension、failure budget 或 universal degradation 的 schema、registry、validator、runtime 字段或权限。
2. 不修改 V/S/E 12 个候选协议、Charter、Kernel、Owner/Executor 边界、Current identity、state changelog 或 live obligation。
3. 不触发 live executor、authenticated channel、provider、network mutation、Owner transition 或外部发布。
4. 不把 synthetic countermodel 写入当前 data registry，不把它当作真实事件或外部证据。

## 10. 最小保留建议

若后续确有 Owner 指令继续，最小下一步应是针对一个具体现有合同的 `RESEARCH_TO_CONTRACT` review：冻结一个 junction case，给出输入字段、预期 stop/review、独立 reviewer、反例和影响；只有证明现有合同无法表达且新增最小字段稳定减少漏检时，才讨论修改既有合同。任何修改仍需独立 exact-head、Draft review、merge/current 分离和 1111 receipt。

本文件最终状态：`ADVERSARIAL_REVIEW_COMPLETE / DUAL_FOUNDATION_FALSIFIED / CROSS_CONTRACT_LENSES_RETAINED / NO_CANONICAL_CHANGE / OPEN_TO_REPRODUCTION`。
