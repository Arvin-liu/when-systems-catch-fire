# 价值—认识论推导审计：六类元协议前提

Status: `RESEARCH_RECORD / CANDIDATE_AUDIT / NON_CANONICAL`

Task: `IGNITION-20260904-153`
Baseline: `when-systems-catch-fire` `main@212322d41db79bce2dbd116166d3f1ad226291f3`
Scope: 仅审计仓库内现有规范、协议、治理和运行边界；不修改运行时、CI、gate、policy 或 canonical protocol。

## 1. 问题、口径与边界

本审计回答一个开放问题：当前围绕 Evidence、Uncertainty / Claim Ceiling、Negative Capability、Ownership、Failure Budget、Degradation 的六类治理语汇，是否能够从更小的价值—认识论基础推导出来；如果不能，缺口在哪里，哪些部分只是事后命名或跨层拼接。

六类是本任务的审计对象，不预设它们已经是六个 canonical protocol，也不预设“更底层”一定意味着新增一层。全文使用三种标签：

- `OBSERVATION`：直接来自当前仓库文件、结构或可复核的词项检索；
- `INFERENCE`：在这些来源之上作出的有边界分析，不是仓库现状；
- `PROPOSAL`：供后续 Owner / reviewer 决定的候选模型，不进入当前规范栈。

本轮没有引入外部文献、外部事实或现实案例数据。因而下文不能证明六类在仓库外普遍必要，也不能证明任何价值命题、因果命题或协议有效性。

## 2. 当前状态证据

### 2.1 六类并不是当前的六个 canonical protocol

`OBSERVATION`：当前原始 12 个协议仍按三个维度组织：V1–V4（value）、S1–S4（structure）、E1–E4（evolution）；原始入口把它们标为 `candidate_formalized`、`L2` 候选形式化，并明确单个协议不单独预测系统命运。见 [12 个基础元协议](../meta-protocols/12-meta-protocols.md)。

`OBSERVATION`：针对 12 个协议的现行规范性审核给出的结果是 12 项 `CONDITIONAL_ACCEPTANCE`，独立人类复核、事实验证、governance approval、ratification 和 formal promotion 均未完成，canonical 状态保持不变。见 [元协议规范性审核 README](./meta-protocol-reviews/README.md) 与 [统一审核矩阵](./meta-protocol-reviews/12-meta-protocol-normative-review.md)。

`OBSERVATION`：在本审计使用的当前文档范围内，精确词项检索得到：

|检索对象|当前命名命中|解释|
|---|---:|---|
|`negative capability` / `消极能力`|0|没有以该词名登记的 canonical protocol 或 gate。|
|`failure budget` / `失败预算`|0|当前有 action/resource/time/output budget、risk cap、failure 与 rollback，但没有该命名对象。|
|`degradation`|0|英文词未作为当前命名对象出现；中文 `降级` 出现于状态和操作规则中。|
|`claim ceiling`|186|这是已广泛使用的断言上限语汇，但它不是 V/S/E 的一个坐标。|
|`ownership`|10|主要出现在工程 ownership / authority boundary；不是一个单独的价值协议。|

检索范围为 `ignition/docs/**/*.md`、`ignition/ARCHITECTURE.md` 与 `ignition/FOUNDATION.md`，执行日期为 2026-09-04。词项计数是导航证据，不是语义真值裁决。

### 2.2 当前仓库已经存在的较小接口

以下接口可以作为现有材料，而不是本审计新发明的层：

|接口|当前作用|本审计可观察到的边界|
|---|---|---|
|生命共同体价值宪章|把“一宇、今宵、共在、相契、长瞻”转为规范性前提，并要求记录受益者、风险承担者、沉默主体、同意、不可逆性、证据门槛、拒绝、回滚和残余伤害。|它提供价值与行动边界，不是事实证明；价值、证据、语义审核、governance approval 必须分开。见 [价值宪章](./life-community-value-charter.md)。|
|Claim / M-E / claim ceiling|要求来源、类型、证明、证据、成熟度、依赖和公开上限保持区分；机器不确定时停止或要求人工复核。|它能约束断言，不决定什么价值上值得追求，也不授予行动权限。见 [断言治理与函数身份规范](../foundation/claim-governance-and-function-identity.md)。|
|Kernel / federated planes|记录共享禁升规则和类型化交接，要求状态按对象和问题命名；不建立统一真值、统一生命周期或无损总顺序。|`K13_ASSERTION_NON_ESCALATION` 已经把重复、规模、工程完成、跨域对应和共识与真值分开。见 [Epistemic Governance Kernel](../architecture/epistemic-governance-kernel-and-federated-planes.md)。|
|Stop / exit / rollback / reconciliation|V1–V4、S1–S4、E1–E4 的审核和 OS/runtime 合同都包含不同程度的停止、退出、回滚、降级、隔离或重审。|这些是按对象分布的操作规则，不证明有一个独立的 Negative Capability 或 Degradation 基础。|
|Owner / responsibility actor|OS Steering 使用 `OWNER_DECLARED` / `OWNER_APPROVED_DERIVED`；发布责任主体必须解析为 ACTIVE `PERSON` 或 `ORGANIZATION`，Agent/workflow 只是技术记录。|它是 authority / responsibility topology，不等于事实正确、Owner 一定理解后果或法律责任。见 [OS Steering](../architecture/os-steering-intent-r1.md) 与 [阶段成果持续快照与分层发布制度](../operations/stage-snapshot-publication.md)。|

### 2.3 候选基础的命名约束

`PROPOSAL`：为避免把漂亮的抽象词当作新权威，本审计暂用四个工作标签。它们不是当前 canonical ID，也不应直接写入 registry：

- `P` — provenance-bounded assertion：断言只能沿真实来源、证据、证明、依赖、成熟度和 claim ceiling 传播；未知和不适用保持可区分；
- `O` — option preservation：在不确定或高后果情形保留停止、退出、回滚、重审和未来选择空间；
- `N` — non-domination / non-externalization：不能用局部目标把不可逆、非自愿或不可见的生命共同体代价外部化给风险承担者、沉默主体、维护者或未来参与者；
- `A` — accountable authorization：有后果的决定要有合法的 authority / consent 来源、可争议路径和明确的责任承载者；技术执行不替代它。

四者混合了认识论、价值和治理层。正因为层级不同，它们不能被一条纯粹认识论公式无损地推出。

## 3. 六类审计矩阵

下表中的“推导链”统一写成：`value / axiom → epistemic or normative constraint → protocol → operational rule`。链条中的空位、跳跃和跨层拼接本身就是审计结果。

|审计对象|当前 canonical 名称 / 直接来源|避免的失败模式与高层理由|显式 / 隐含前提|候选 primitive|推导链（候选）|推导状态|反例或可证伪条件|移除后的独立性|
|---|---|---|---|---|---|---|---|---|
|Evidence|不是 V/S/E 坐标；以 evidence、provenance、M/E、source family、independent review 分散存在。见 [Kernel](../architecture/epistemic-governance-kernel-and-federated-planes.md)、[Claim Governance](../foundation/claim-governance-and-function-identity.md)。|阻止无来源断言、重复引用冒充独立证据、工程绿灯冒充事实；让他人能重查“这句话来自哪里”。|显式：来源必须绑定，证据与 proof / value / governance 分开。隐含：判断有可能错，来源之间可能不独立，接受者需要 contest。|主要是 `P`；对有后果的行动还需要 `A` 和 `N`。|`P`（来源可追溯）→ provenance / source-family / M-E 约束 → evidence gate 与 claim ceiling → 只输出来源支持的范围并保留反例、未决项和撤回路径。|`DIRECT+PARTIAL`：仓库已有直接机制，但“为什么任何情形都需要独立 evidence”不是由当前价值宪章形式化推出的。|在封闭、完整给定公理和可复算证明的纯形式对象上，可以不另设经验 evidence gate；这会反驳“所有对象都必须同一类 evidence”，不会反驳证明和来源的可追溯性。|`P` 移除后，claim ceiling 仍可被文字保留，但无法稳定绑定来源、独立性和反弹；Evidence 不是 Uncertainty 的同义词。|
|Uncertainty / Claim Ceiling|`claim ceiling` 是当前明确语汇；`unknown`、`ABSTAIN`、`REQUIRES_HUMAN_REVIEW`、M/E 正交也已有局部契约。见 [Kernel K13](../architecture/epistemic-governance-kernel-and-federated-planes.md)。|阻止局部结果变成普遍、确定、因果或外部真实；阻止完成态、共识、模型美感和叙事完整度抬高断言。|显式：unknown ≠ missing ≠ rejected；一轴不能自动升级另一轴。隐含：信息不完备且公众会把强措辞当作更强事实。|主要是 `P`，并在高后果场景调用 `O`。|`P`（可证明的来源边界）→ epistemic modesty / explicit uncertainty → claim ceiling 与 scoped disposition → public wording 更窄、机器停止或请求 review。|`DIRECT+PARTIAL`：claim ceiling 是直接制度，但其最优阈值、是否足够、何时能决策而不能宣称，仍未被统一形式化。|若某类对象的完备公理、证明和目标均已封闭，且不可能发生解释迁移，则“保留不确定性”可退化为对象局部的零不确定性；这反驳普遍阈值，不反驳对开放世界主张保留 ceiling。|移除它不会移除 evidence；会失去“有证据但不能说得更强”的独立刹车，故与 Evidence 不可合并。|
|Negative Capability|精确词项不存在。当前近似机制是 `ABSTAIN`、`STOP`、`REQUIRES_RECONCILIATION`、`NO_INFORMATION_GAIN`、暂停、退出与不自动重试。见 [Attention / Attractor](../architecture/attention-attractor-control-plane.md) 与 [Runtime R1](../architecture/agent-runtime-r1.md)。|阻止行动偏置、为了闭环而猜测、把等待伪装成失败或把“什么都不做”伪装成审慎；其合理版本是有理由、期限和下一证据目标的 abstention。|显式：不确定时不得猜测；未知副作用不自动 failover。隐含：不行动也可能造成伤害，等待需要机会成本和责任人。|`P + O + N`；不是单独的价值 primitive。|`P/O/N` → “在证据不足或不可逆性过高时降低行动强度” → abstain / pause / stop / reconcile → 明确不行动理由、期限、触发证据与 owner。|`POST-HOC/COMPOSITE`：仓库有多项等价操作，但没有对“有益克制”与“逃避”进行统一定义或独立测量。|若在某一封闭域中总有一个安全、可逆、低成本的行动，且 abstention 从不减少伤害、信息或未来选项，则 Negative Capability 对该域不必要。反向压力测试是“不做”是否掩盖了可避免的逃避。|移除它仍可保留 claim ceiling 和 stop condition，但系统会更难表达“暂不行动本身是有边界的决定”；它独立于 Uncertainty，因为知道不确定不等于愿意停下。|
|Ownership|不是一个名为 Ownership 的协议。当前对应 `OWNER_DECLARED`、`OWNER_APPROVED_DERIVED`、`responsible_actor`、`publisher_actor`、`actor_ref`、Charter authority。|阻止“提出者 = 批准者 = 执行者 = 责任人”的塌缩，阻止 Agent、CI、commit 或上游项目自封为 Owner。|显式：Agent/workflow 仅是技术执行记录；最终责任引用必须是 ACTIVE 人或组织。隐含：有后果的决定需要可识别的 authority、可争议路径和承担代价的主体。|主要是 `A`，并受 `N` 约束。|`A`（合法授权与责任分配）→ authority / consent / contestability constraint → Owner / Charter / actor registry / approval gate → 显式授权、签名、责任记录、停止和回滚。|`DIRECT+PARTIAL`：role separation 与 actor registry 直接存在；“为什么某个主体有资格承担价值责任”仍不是由仓库机制证明的。|低风险、个人范围、可逆且无第三方后果的动作可以不需要独立 Owner registry；这限制普遍性，但一旦涉及公共、不可逆或他人风险，移除责任承载者会使动作无法治理。|移除 `A` 后仍可做 evidence 和 validation，却无法区分 proposal、permission、execution 和 accountability；Ownership 不能被“更多日志”替代。|
|Failure Budget|精确词项不存在。当前有 action/time/output/resource budget、queue quota、risk cap、failure states、rollback 与 open obligation；V2/V3/E2 等有全成本、风险上限和失败反馈。|合理用法是预先限制试错暴露；危险用法是把预算变成“允许造成多少可避免伤害”的许可证，或把耗尽预算当作自动正当化。|显式：预算是 bounded action 输入，不等于成功或 truth；Charter 禁止外部化生命代价。隐含：某些试验风险可承担且可以预先限额。|`N + O + P`；不是独立 primitive。|`N/O` → whole-cost / risk / reversibility constraint → action budget / risk cap / stop trigger → 预算预注册、耗尽即停、失败可回滚；绝不把预算当作预付伤害许可。|`UNSUPPORTED_AS_PRIMITIVE / CONFLICTING`：作为工程资源预算有用，作为价值基础会与反外部化原则冲突；当前没有统一的“失败预算”语义。|如果预算无法区分“不可避免且被同意的学习成本”与“可预防的主体伤害”，它会系统性制造道德许可；这足以否定其作为独立基础。|移除“Failure Budget”这个名字不损失现有 action/resource ceilings；保留 `N/O` 即可解释风险上限。它是最容易被误用、也最不应直接 canonicalize 的对象。|
|Degradation|英文命名不存在；中文 `降级`、`WITHDRAWN`、`QUARANTINE`、`DOWNGRADE`、`REQUIRES_RECONCILIATION`、历史保留和 narrow public ceiling 已在多个局部机制中出现。见 [Kernel lifecycle](../architecture/epistemic-governance-kernel-and-federated-planes.md)。|阻止二元 pass/fail 掩盖部分失效、未知副作用、撤回、证据不足和不可比较状态；让能力、断言、公开措辞和行动许可可以分别变窄。|显式：下游 ceiling 只能更窄；撤回和 supersession 保留历史；unknown、blocked、withdrawn 不互换。隐含：状态有偏序或至少存在可安全保留的中间态。|`P + O`，必要时加 `A`。|`P/O` → monotonic loss of assertion/action authority + history preservation → downgrade / quarantine / withdraw / reconcile → 更窄措辞、停止传播、回滚或重新审查。|`DIRECT_OPERATIONAL / PARTIAL_FOUNDATION`：局部规则很直接，但不存在一条覆盖所有对象的 degradation 代数；Kernel 明确承认 ceiling vocabulary 不能无损总排序。|在只有“有效/无效”且没有安全中间状态的封闭对象上，降级会增加歧义而不增加控制；应退回对象局部的 reject，而不能强行推广。|移除它仍可保留 reject/withdraw，但会失去部分恢复、窄化、隔离和不抹除历史的路径；它独立于 Uncertainty，因为“未知”不等于“可降级”。|

### 3.1 矩阵结论

`INFERENCE`：六类的推导状态不是同质的。

1. Evidence 与 Uncertainty / Claim Ceiling 最接近 `P`，但前者偏来源与可复核性，后者偏允许说到哪里；二者有共享基础而非同义。
2. Negative Capability 与 Degradation 更像 `O` 的两个操作面：一个控制“现在不要扩大动作”，一个控制“状态已经变差后如何收窄”。两者仍不能互换，前者可能发生在任何失败之前，后者需要状态变化或新证据。
3. Ownership 是 `A` 的制度化形态，且不能由 `P` 推出。知道某命题来自哪里，不会自动回答谁有权让它进入现实、谁必须承担后果。
4. Failure Budget 不是基础而是一个风险/资源参数的候选包装；如果它可以成为“先买好伤害额度”，就与 `N` 冲突。
5. 六类横跨认识论、规范性、治理和运行时；把它们平铺成“六个更深元协议”会把层级混为一谈。

## 4. 价值—认识论—协议—操作的断裂点

### 4.1 价值不能仅由认识论推出

`OBSERVATION`：价值宪章把生命共同体、反局部掠夺、长期与再生、未知主体、维护者可持续性和商业互惠写为规范性前提；同一文件明确价值判断、事实证据、语义审核和 governance approval 是四类不同问题。见 [价值宪章](./life-community-value-charter.md)。

`INFERENCE`：`P` 可以说明“某个事实主张没有足够来源”，却不能仅凭这一点推出“不得把他人当作代价”。后一个判断需要 `N` 类规范前提或等价的 Charter commitment。把“应该诚实地表达不确定”推成“应该保护所有受影响者”，会发生 category error。

### 4.2 结构与演化协议不是价值的直接函数

`OBSERVATION`：S1–S4 和 E1–E4 在审核中被说明为情境性结构/演化工具；Charter 明确它们没有脱离后果的绝对优先级。S3 的层级、S4 的网络、E1 的线性和 E2 的非线性可以描述如何组织或观察系统，但描述本身没有告诉我们哪种后果值得接受。

`INFERENCE`：即使把 S3 解释为“责任清晰”、S4 解释为“冗余”、E2 解释为“诚实面对不确定”，这些都是被 `A/P/O` 约束后的规范性重写，不是从结构名称直接演绎出来的定理。

### 4.3 当前真正共享的是“不升格”而非“统一价值函数”

`OBSERVATION`：Kernel 的共享 invariants 是 formalization 不等于 confirmation、proof 不自动提升 E、public wording 不得高于 local ceiling、依赖只传递复核压力、撤回不得回弹，以及不可比较时 fail closed。它把跨平面的误推理堵住，但不生成统一真值或统一价值排序。

`INFERENCE`：若一定要找更小共同项，最有证据的共同项是 `P` 与 `O` 的组合；`N` 和 `A` 来自价值/治理边界，不能被这两个认识论项吞并。

## 5. 冲突与压力测试

### 5.1 规范之间的冲突处理

|张力|当前仓库的可观察处理|仍未解决的部分|
|---|---|---|
|Evidence vs continuity|低风险、可逆、可承受损失的 action 可以用较低 certainty 进入 Action Threshold；Claim Threshold 和 Scale Threshold 仍更高。|什么是跨域可比较的“低风险”和“可承受损失”仍需外部/Owner 语境，不能由 CI 总数决定。|
|Negative Capability vs avoidance|要求说明 stop/pause/reconcile 的理由、未决证据和下一步；Attention control 允许 stop，也允许 branch、seek evidence 或 test。|当前没有统一 deadline、机会成本和责任归属字段来区分有益等待与拖延。|
|Failure budget vs normalization of deviance|OS 的 budget 是资源/行动上限；Charter Gate 要求记录风险承担者、残余伤害、拒绝与回滚，不能把预算写成伤害许可证。|“预算内但仍不可接受”的价值判断没有一个叫 Failure Budget 的独立裁决器；不能补造公式。|
|Ownership vs distributed cognition|S4 可提供分布式协作和冗余，但明确责任不能因去中心化而消失；OS 把 proposal、authority、execution 分开。|多人 Owner 的冲突、替代/代理和理解义务的可操作规则仍不完整。|
|Reversibility vs irreversible action|V3/E2、Scale Threshold 和 Charter Gate 把不可逆行动推向更强证据、明确拒绝/回滚条件和沉默主体记录。|真正不可回滚时，记录并不制造回滚；是否允许行动仍需具体 Owner/Charter 决定。|
|Audit completeness vs real-time response|DecisionCollapseRecord 可以记录动作前候选、排名依据、trigger、异议、未决项、rollback 和 threshold；决策塌缩不等于真理塌缩。|紧急情况下谁有预授权、谁理解并承担事后代价，当前没有一个总合同。|
|Two protocols point in opposite directions|Kernel 要求记录冲突、保留局部 authority；OS Steering 对 permission failure fail closed，对安全冲突进入 `HUMAN_REVIEW`，不可比较时不伪造 precedence。|当前没有普遍适用于所有 V/S/E 组合的价值总序；这不是缺一个“更高协议”就能安全解决的。|

### 5.2 七个最小压力案例

|案例|测试的失败|当前可用的防线|审计判定 / 需要的反例|
|---|---|---|---|
|1. 证据持续增加，但窗口即将关闭，等待会错过时机|把 Evidence 变成无限延期；或把时间压力误写成证据充分。|Action / Claim / Scale 三阈值、Decision Collapse、保留 pre-collapse uncertainty。|支持“证据与行动阈值正交”；不能推出“证据越多就必须等待”或“时间到了就自动批准”。若低风险可逆动作没有等待收益，`O` 的更强阻断会被反驳。|
|2. “什么都不做”掩盖了可避免的逃避|把 Negative Capability 当作免责词。|要求停下的理由、期限、下一证据/测试、Owner 与 unresolved residue；Attention control 可把循环标为 `RUMINATION_RISK`。|当前只支持 bounded abstention，不支持“任何不作为都审慎”。若不行动的机会成本未记录，结论应保持开放。|
|3. Failure Budget 为可预防伤害开脱|把资源预算误作伦理额度，正常化偏差。|Charter Gate 的风险承担者/残余伤害、V2 全成本、E2 risk cap、stop/rollback。|“Failure Budget”作为独立 primitive 被否定；若无法逐案区分可预防伤害，必须拒绝该词的 canonical 化。|
|4. 有名义 Owner，但 Owner 不理解、未授权或不知道后果|形式签字被当作合法授权与责任闭合。|Owner → Intent → Goal → Commitment 链；actor registry；contestability/DecisionTrace；execution agent 不能代签。|Owner 是 authority 来源但不是充分条件。若没有理解、后果可见、反对/撤回路径，`A` loop 不闭合；仅存在点击或姓名不足。|
|5. 必须执行不可逆动作|把可逆性当成绝对前提，导致无法救助；或在不可逆名义下绕过门禁。|Charter Gate、Scale Threshold、沉默主体、证据门槛、拒绝/回滚与残余伤害字段；无通用豁免。|可证伪的是“任何动作都可逆”；不可证伪地声称“不可逆就自动允许”同样越界。回滚不存在时只能记录补偿/停止/拒绝条件，不能假称 rollback 成立。|
|6. 日志完整，但判断本身错误|把可审计性误当作正确性；责任被日志洗掉。|日志与 evidence 分离；独立 reviewer 可 `ABSTAIN`；Claim/M-E/semantic review 分开；Kernel 明确 Git/CI/receipt 不制造真值。|证明了 durable record 的必要性不等于证明判断正确。若错误判定没有可争议的人类 review / 外部证据路径，`A` 与 `P` 都是不完整的。|
|7. 两个协议给出相反行动|用新元层伪造全局 precedence，或选择更会说服人的叙事。|局部 authority、冲突记录、permission intersection、fail closed、human review、保留两边理由。|当前结论是“冲突可审计但不总能自动裁决”。若未来出现大量相同冲突并能给出稳定、Owner 接受且可证伪的排序规则，才有理由开新任务审查是否需要窄 arbitration contract。|

## 6. 共享基础、非共享部分与独立性

### 6.1 `P / O / N / A` 的候选覆盖图

|候选基础|主要解释|不能解释的内容|若被移除，最先出现的可观察失败|
|---|---|---|---|
|`P` provenance-bounded assertion|Evidence、Uncertainty、Claim Ceiling、M/E、source family、anti-rebound、公开措辞边界。|什么目标值得做、谁有权授权、谁承担生命/维护/未来代价。|同一来源的重复引用变成“独立证据”；claim ceiling 失去稳定来源，CI/共识更容易抬高断言。|
|`O` option preservation|Negative Capability、Stop/Exit/Recovery、Degradation、Reconciliation、future choice space、Decision Collapse 后保留不确定性。|事实是否成立、价值冲突的最终权衡、谁有 authority。|高不确定性下 action 变成不可逆；停止、回滚和重审被当作异常而非设计条件。|
|`N` non-domination / non-externalization|Charter 的受影响者、沉默主体、不可逆风险、长期/代际、V2 全成本、V4、反掠夺和不把预算当许可证。|证据独立性、具体 Owner 身份、数学/经验真值。|局部效率、连续性或创新以无声受害者和维护者为成本，且能在“流程完成”后被叙事掩盖。|
|`A` accountable authorization|Ownership、Owner/Charter gate、actor registry、consent、contestability、authority–execution–accountability 分离。|签字者是否事实正确、证据是否充分、不可逆后果是否真的能回滚。|Agent proposal、CI pass、service execution 和 final responsibility 串成一条匿名链，没人能被明确要求停止、解释或承担。|

### 6.2 不是完整推导的地方

`INFERENCE`：目前没有证据可以把四个候选基础进一步压缩成一个“总原理”而不丢失层级。尤其：

- `P` 的真实性边界不会生成 `N` 的价值承诺；
- `N` 的规范边界不会生成某一项经验主张为真；
- `A` 的合法授权不会使签字者理解后果，也不会替代 independent review；
- `O` 的可回滚性不会自动告诉我们哪个未来选项值得保留；
- V1/V2/V3/V4 之间已有重叠和待验证差异，不能把它们全部重新命名成一个 primitive 后宣布推导完成。

因此“六类来自四个候选共同基础”只能作为 partial explanatory model，而不是数学演绎、canonical ontology 或治理批准。

## 7. 观察、推断、候选建议

### OBSERVATION

1. 当前 canonical 是 12 个 V/S/E 候选协议；六类审计对象不与其一一对应。
2. `claim ceiling`、source/provenance、M/E、withdrawal、downgrade、stop、rollback、Owner/actor boundary 已分别存在。
3. 当前规范性审核的事实状态是 conditional、pending、未晋级；研究记录不能改变它。
4. `negative capability` 和 `failure budget` 不是当前命名对象；“降级”是分散的状态/操作词。

### INFERENCE

1. 六类是跨层 failure-control concerns，不是六个同构的价值原子。
2. 四个候选基础能够解释相当多的重复约束，但不能从认识论单向推出价值或授权。
3. 最大的真实缺口不是“少了一个层”，而是若干 cross-product 情形没有被一个现有字段同时表达：例如“名义 Owner + 不可争议的 Agent 判断”、“预算内但不可接受的伤害”、“证据完整但没有可承担责任的人”。
4. 若把每一个 gap 都命名为新元层，会触发 [Attention And Attractor Control Plane](../architecture/attention-attractor-control-plane.md) 所警告的“every gap becomes a new layer”吸引子。

### PROPOSAL（不进入 canonical）

暂保留 `P/O/N/A` 作为研究索引词，只用于后续反例和缺口定位。若未来需要制度化，应优先把它们映射回现有 Claim / Charter / Approval / Runtime / Result contracts，并以新增失败诊断为准；只有在既有 contract 无法表达、且压力测试重复再现时，才另立窄范围 candidate contract。

## 8. 不主张、明确不编码与下一步

### Not claims

- 不主张六类在项目外普遍必要；
- 不主张生命共同体价值可以从证据或不确定性逻辑演绎；
- 不主张当前 12 协议已经被重新推导、重命名、形式化或晋级；
- 不主张有名义 Owner 就已经理解、同意、能承担或能撤销后果；
- 不主张 CI、日志、Agent 共识、PR 或本研究文档制造事实、真值、生产 readiness、Owner acceptance 或 epistemic acceptance。

### Deliberately not codified

- 不新增第 13 个或第 7 层 meta / meta-meta protocol；
- 不把 Negative Capability、Failure Budget、P/O/N/A 写入 canonical registry、schema、validator 或 runtime；
- 不重写 V1–V4、S1–S4、E1–E4 的 canonical name、状态或定义；
- 不为“失败预算”“风险权重”“Owner 理解度”发明未验证的统一公式；
- 不将反例压力测试伪装成外部验证或真实世界数据。

### Next institutionalization recommendation

若 Owner 后续要把本审计推进为制度候选，建议单独创建一个明确声明 `RESEARCH_TO_CONTRACT` 的任务，至少补齐：

1. 对 `P/O/N/A` 各自的最小可判定谓词、适用域、输入/输出和反例；
2. 对七个压力案例的独立人类 review、不同 Owner 冲突和真实/模拟后果记录；
3. 与现有 claim ceiling、Charter Gate、approval intersection、rollback/reconciliation 的非冗余证明；
4. 明确“不行动”与“逃避”、预算与伤害许可、签字与理解之间的判别；
5. 如果仍无独立增量，则以“无新层、现有 contracts 足够”正式结束，而不是继续加抽象名词。

当前推荐：`NO_CANONICAL_CHANGE / NO_NEW_LAYER / KEEP_AS_RESEARCH_RECORD`。
