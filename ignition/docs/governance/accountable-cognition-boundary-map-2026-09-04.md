# 可追责认知边界图：角色拓扑与 authority–execution–accountability loop

Status: `RESEARCH_RECORD / CANDIDATE_MAP / NON_CANONICAL`

Task: `IGNITION-20260904-153`
Baseline: `when-systems-catch-fire` `main@212322d41db79bce2dbd116166d3f1ad226291f3`
Scope: 只分析仓库已声明的角色、权限、执行、记录和责任边界；不讨论 AI 意识、人格、道德/法律主体资格，不修改运行时或授权。

## 1. 术语边界

本文件使用“accountable cognition boundary”作为一个中性的流程分析词：它描述一个有后果的决定如何在信息处理、主张提出、评价、授权、执行、观察、停止/回滚、记录和责任承载之间保持可追溯。它不把任何 Agent 拟人化，也不主张 Agent 是意识主体、人格主体、道德主体或法律责任主体。

“认知”在本文只表示可观察的 information processing / inference / proposal / evaluation practice；“责任”在本文只表示仓库治理合同中可识别的 accountability sink / responsible actor，不作法律结论。

全文仍严格区分：

- `OBSERVATION`：当前源文件明文声明的角色和边界；
- `INFERENCE`：从这些声明得到的拓扑风险分析；
- `PROPOSAL`：候选 loop / invariant，不是新 canonical layer。

## 2. 当前角色与实体证据

### 2.1 当前 authority chain

`OBSERVATION`：OS Steering 把方向链写成：

`OWNER_DECLARED` 或 `OWNER_APPROVED_DERIVED` → canonical Intent → versioned Goal → explicitly accepted Commitment → Episode/Run binding → bounded Action。

系统推导、外部请求和历史导入仍是 proposal，不能借重复行为、memory、chat、test、receipt、Pack result 或 executor report 静默跨过 Owner transition。见 [OS Steering, Intent, and Obligation R1](../architecture/os-steering-intent-r1.md)。

`OBSERVATION`：真实行动层的工程链是 `Reasoner → ExecutionPacket → Authorize + ApprovalStore → LeaseStore → ActionJournal → LocalWorkspaceExecutor → Validator → Continue / Stop`。WorkspacePolicy 对路径、symlink、special file、argv、shell、timeout、output 和网络/远程 mutation 设 fail-closed 边界；Reasoner 不选择 provider、不保存凭据，也不改变 executor 权限。见 [Agent Runtime R1](../architecture/agent-runtime-r1.md)。

`OBSERVATION`：Approval Bridge 对 Ignition ApprovalPolicy、capability ceiling 和外部 approval 取严格交集；`DENY` 阻断，`REQUIRE_OWNER` / `DELEGATED` 等待显式 Owner 决定，外部 executor 的 `APPROVED` 不替代该 authority。见 [Approval Bridge, Handoff and Failover R1](../architecture/approval-handoff-failover-r1.md)。

`OBSERVATION`：发布责任主体只能通过 active `PERSON` / `ORGANIZATION` 的 `actor_ref` 正向绑定；`execution_agents` 和 `automation_workflows` 记录技术因果链但不能成为最终责任引用。见 [阶段成果持续快照与分层发布制度](../operations/stage-snapshot-publication.md)。

`OBSERVATION`：Kernel 将 machine validator、object-local registry、independent reviewer、Charter/human authority、GPT Owner、external expert / replication 和 Results Book 分列；不可比较的决定应 fail closed，不应虚构总 precedence。见 [Epistemic Governance Kernel](../architecture/epistemic-governance-kernel-and-federated-planes.md)。

### 2.2 中性角色词表

|角色|最小含义|不能从该角色推出的内容|
|---|---|---|
|Information processor|读取、整理、转换已给出的信息。|不推出理解、意识、同意、价值判断或事实正确。|
|Epistemic contributor|提供来源、计算、观察、反例、限定或可复核分析。|不自动成为独立 evidence、reviewer 或 truth authority。|
|Claim proposer|提出待审查的 atomic claim、机制、解释或行动假设。|提出不等于接受、证明、授权或 Owner approval。|
|Evaluator / reviewer|对命名的 review question 作 scoped 判断，必要时 `ABSTAIN`。|不自动裁定无关轴，不替代价值授权或外部复现。|
|Decision authority / signer|在合法 authority 范围内批准、拒绝、暂停或要求回滚。|签字不自动证明事实、理解全部后果或使行动合乎价值。|
|Operational executor|在已批准的 capability、lease、workspace 和 action envelope 内产生技术副作用。|执行不等于决定、真值、Owner status 或最终责任。|
|Observer / monitor|观察过程、健康、结果、偏差、资源或外部响应。|健康观察不等于成功；观测不等于因果解释。|
|Recorder|把请求、证据、决策、事件、前后状态和未决项持久化。|日志不等于正确判断，也不自动产生 authority。|
|Auditor|检查来源、规则、依赖、边界、独立性、差异和反弹。|审计通过不等于现实真理或法律结论。|
|Rollback authority|在满足 preimage / postimage / Charter / approval 条件时触发回退、修补或撤回。|存在回滚按钮不等于所有副作用可逆。|
|Responsibility bearer|对治理合同中明确指定的决定/发布/后果承载责任。|不因此成为唯一证据源，也不因此获得超出范围的权限。|
|Mechanism / substrate|提供存储、调度、验证、网络、账户或执行载体。|机制不是价值主体、审查者或责任主体。|

一个实体可以在不同 action 上承载多个技术角色，但角色共址不消除独立 review、authority、execution 和 accountability 的分离要求。

## 3. 实体拓扑总表

|实体|主要可承载的中性角色|Capability|Authorization|Practice|Normative status（仓库范围）|
|---|---|---|---|---|---|
|Human Owner(s)|decision authority / signer；可能是 claim proposer、review participant、observer、stop/rollback authority、responsibility bearer|可以提供目标、上下文、价值判断、异议、签名和停止/回滚决定；能力不保证完备知识。|Owner / Charter authority 只在显式、版本化、范围绑定的 transition 中生效；不由 memory、Agent proposal、CI 或 receipt 推断。|声明/批准 Intent、接受 Commitment、审看后果、保留 contest、停止或回滚；若没有真实批准，保持 proposal。|在当前治理合同中是可识别的 authority / accountability 来源；不据此作法律责任或“唯一认知主体”结论。|
|Codex / Agents|information processor、epistemic contributor、claim proposer；可作为受限 technical executor|可观察、转换、推断、提出、解释、生成 packet；在明确授权和 envelope 内可执行技术动作；不能仅凭输出成为独立 review。|无 Owner/canonical/truth authority；执行权限来自 packet、policy、approval、lease 和 workspace，不来自语言说服力。|提出候选、报告不确定性、拒绝越界、记录技术结果；必要时执行已批准的 bounded action；不能自签、自己提升、自己宣布 Current。|technical contributor / execution agent；不是最终责任引用、价值 authority、事实证明者或法律主体。|
|CI|observer、deterministic evaluator、recorder、bounded auditor|可运行 schema、引用、确定性生成、测试、差异和失败规则；不能理解开放语义。|只拥有机械 gate 所声明的阻断/放行效果；不能授予 Owner authority、外部真值或生产许可。|按 exact input / version / workflow 验证并报告；失败应阻断或要求修复；绿灯只证明其 predicate。|repository-local consistency evidence / gate mechanism，不是 truth authority 或责任承载者。|
|Policy / gate|constraint evaluator、stop mechanism、permission compiler|可计算交集、禁止边、状态和前置条件；可在不满足条件时停止。|可缩窄父权限、阻断转换、要求 Owner / human review；不能自创价值目标或替代人类授权。|fail closed、保留 unknown、记录拒绝原因；不以缺少错误为成功。|规范边界机制；不是 decision subject、责任人或独立事实审查者。|
|Service account|operational executor、recorder、limited observer|可以使用被授予的 credential scope 执行技术动作、读写对象和产生日志。|只有显式 delegated technical scope；凭证存在不等于价值同意、Owner approval 或无限 authority。|按 literal argv / API contract 执行、记录 receipt、接受 cancel/stop；不解释目标、不签署价值决定。|technical principal / mechanism；不是最终 responsibility bearer。|
|Repository|recorder、version substrate、source/artifact store|保存文件、提交、分支、registry、schema、历史和投影；可供人和工具观察。|Git/branch/workflow 的权限由外部账号、policy 和 review 控制；repository 本身不批准。|保存前后差异、来源、状态和历史；不能把文件存在当作事实或 capability。|durable substrate / provenance surface，不是 actor 或 normative subject。|
|Artifacts / evidence|epistemic object、source carrier、input/output object|可以携带内容、hash、来源、版本、结果和反例；可被人/工具转换。|对象本身没有授权；被引用不等于被接受；artifact presence 不等于 external evidence。|绑定 provenance、M/E、claim ceiling、pre/post image、review scope；冲突时保留而不抹除。|epistemic material，不是推理者、签字者或责任人。|
|Logs / audit trails|recorder、replay substrate、auditable evidence|记录事件顺序、状态、理由、前后摘要、未决项和 validator refs；支持重放/审计。|没有独立授权；日志中出现 `APPROVED`、`PASS` 或 signer 字段也不改变其来源。|append-only、hash-linked、持久、可追溯；必须和实际判断、独立 review、责任 sink 分开。|accountability evidence / historical record，不是 judgment authority。|
|Automation / runtime|scheduler、dispatcher、executor、observer、reconciler、recorder|可在 bounded DAG、lease、budget、policy 和 timeout 内调度/执行/停止/恢复；可观察健康和结果。|权限来自 OS/Charter/approval/capability intersection；不得因可执行而扩权、跨 namespace 或自动重试未知副作用。|执行、取消、reconcile、记录 `PREPARED/EXECUTING/COMPLETED` 等状态；不能把 runtime pass 写成 truth。|mechanism / technical agency；不是 Owner、truth authority 或最终责任 bearer。|
|Scoped independent reviewer / external expert（若被明确指定）|evaluator / reviewer、epistemic contributor、auditor|对明确 question 作独立或外部范围内的 review、反例、复现或 `ABSTAIN`。|只拥有声明的 review scope；不自动拥有 Owner/Charter/execute authority。|记录 independence、source、question、dissent、limitations；不得用同一来源的重复输出冒充 independent evidence。|scoped review authority；不能越界成总真值或治理批准。|

## 4. 13 个 action axis 的四层矩阵

### 4.1 记号

每个单元格写成 `C / A / P / N`：

- `C` Capability：`+` 可承载，`s` 仅在声明范围内，`-` 不承载；
- `A` Authorization：`O` Owner/Charter authority，`G` policy/gate/envelope，`D` delegated technical scope，`-` 无；`G` 不是价值授权；
- `P` Practice：`do` 执行/参与，`sc` scoped contribution，`rec` record-only，`aud` audit，`stop` stop/rollback practice，`na` 不适用；
- `N` Normative status：`B` repository-defined responsibility bearer，`T` technical actor，`G` boundary mechanism，`M` mechanism/substrate，`E` epistemic object，`-` 无。

矩阵表达的是仓库合同能支持的角色位置，不是对现实中某个具体人的身份推断。

|Action axis|Human Owner(s)|Codex / Agents|CI|Policy / gate|Service account|Repository|Artifacts / evidence|Logs / audit trails|Automation / runtime|
|---|---|---|---|---|---|---|---|---|---|
|`observe`|`+/-/do/B`|`+/G/sc/T`|`+/G/sc/T`|`+/G/sc/G`|`+/D/sc/T`|`+/ -/rec/M`|`+/ -/rec/E`|`+/ -/rec/E`|`+/G/sc/T`|
|`transform evidence`|`+/-/sc/B`|`+/G/sc/T`|`+/G/sc/T`|`+/G/sc/G`|`+/D/sc/T`|`-/-/na/M`|`s/-/rec/E`|`s/-/rec/E`|`+/G/sc/T`|
|`infer`|`+/-/do/B`|`+/ -/sc/T`|`-/-/na/T`|`-/-/na/G`|`-/-/na/T`|`-/-/na/M`|`-/-/na/E`|`-/-/na/E`|`-/-/na/T`|
|`propose`|`+/-/do/B`|`+/ -/do/T`|`s/-/sc/T`|`s/-/sc/G`|`-/-/na/T`|`-/-/na/M`|`s/-/rec/E`|`s/-/rec/E`|`s/-/sc/T`|
|`evaluate`|`+/ -/sc/B`|`s/-/sc/T`|`+/G/aud/T`|`+/G/aud/G`|`s/D/sc/T`|`-/-/na/M`|`s/-/rec/E`|`s/-/aud/E`|`s/G/aud/T`|
|`approve`|`+/O/do/B`|`-/-/na/T`|`-/-/na/T`|`s/G/sc/G`|`-/-/na/T`|`-/-/na/M`|`-/-/na/E`|`s/-/rec/E`|`-/-/na/T`|
|`authorize`|`+/O/do/B`|`-/-/na/T`|`-/-/na/T`|`s/G/sc/G`|`-/-/na/T`|`-/-/na/M`|`-/-/na/E`|`s/-/rec/E`|`-/-/na/T`|
|`execute`|`+/O/do/B`|`s/G/sc/T`|`s/G/sc/T`|`-/-/na/G`|`+/D/do/T`|`-/-/na/M`|`-/-/na/E`|`s/-/rec/E`|`+/G/do/T`|
|`stop`|`+/O/stop/B`|`s/G/stop/T`|`+/G/stop/T`|`+/G/stop/G`|`s/D/stop/T`|`-/-/na/M`|`s/-/rec/E`|`s/-/rec/E`|`+/G/stop/T`|
|`record`|`+/ -/rec/B`|`s/G/rec/T`|`+/G/rec/T`|`+/G/rec/G`|`+/D/rec/T`|`+/ -/rec/M`|`+/ -/rec/E`|`+/ -/rec/E`|`+/G/rec/T`|
|`audit`|`+/ -/aud/B`|`s/-/aud/T`|`+/G/aud/T`|`+/G/aud/G`|`s/D/aud/T`|`s/-/rec/M`|`+/ -/aud/E`|`+/ -/aud/E`|`s/G/aud/T`|
|`rollback`|`+/O/stop/B`|`s/G/stop/T`|`s/G/stop/T`|`+/G/stop/G`|`+/D/stop/T`|`s/-/rec/M`|`+/ -/rec/E`|`+/ -/rec/E`|`+/G/stop/T`|
|`be-held-accountable`|`+/ -/do/B`|`-/-/na/T`|`-/-/na/T`|`-/-/na/G`|`-/-/na/T`|`-/-/na/E`|`-/-/na/E`|`-/-/na/E`|`-/-/na/T`|

关键读法：

1. `A=G` 只表示 gate 或 envelope 可以约束/停止/验证，不表示 gate 变成 Owner；`A=D` 只表示技术委托，不表示价值授权或责任转移。
2. Codex / Agent 可以 `infer` 和 `propose`，也可以在已给定的技术 envelope 内 `execute`；这三格不能合并成 approve / authorize。
3. CI、repository、logs 和 artifacts 可以让结果更可复核，但没有一个格子能成为 `N=B`。责任承载者必须由显式治理合同指定。
4. “执行”有技术 agency；“授权”有治理 authority；“被追责”是责任 topology 的 sink。三者允许在同一事件中由不同实体承担。

## 5. 可追责 cognition loop 的最小不变量

### 5.1 候选 loop

`PROPOSAL（human / Agent / external input） → provenance-bound evidence → bounded inference → scoped evaluation / dissent → legitimate authorization / consent → bounded execution → observation of consequences → stop / rollback / reconcile → durable record → contest / audit → revise / downgrade / withdraw`

这是 `PROPOSAL`，不是新生命周期，也不是 L7。低风险、个人范围、可逆的动作可以在实践上合并若干步；高后果、公共、不可逆或影响沉默主体的动作不能用“流程很短”取消这些边界。

### 5.2 不变量审计表

|候选不变量|对什么是必要的|当前仓库机制|何时可能不是必要条件|缺失时的失败|与现有机制的关系|
|---|---|---|---|---|---|
|Provenance traceability|任何需要被复查、争议、发布或传播的事实/判断。|source anchors、M/E、claim registry、hash、typed handoff、K13。|纯粹即时且无外部后果的个人草稿可只保留本地上下文。|重复输出、来源漂移、后补理由、无法区分事实和推断。|不是新东西；是现有 evidence / claim ceiling 的 cross-role 读法。|
|Legitimate authority / consent|公共、不可逆、跨主体或有现实副作用的行动。|Charter Gate、Owner Intent chain、approval intersection、actor registry。|低风险、个人边界、随时可撤销的动作可用简化授权。|Agent/CI/服务账户把“能做”当作“可以做”；被影响者被代表但未参与。|补充 ownership：authority 不是持有文件或拥有凭证。|
|Contestability|决定会改变他人选择、公开表述、资源或未来路径时。|dissent、independent reviewer `ABSTAIN`、DecisionTrace、human review、公开理由。|可逆且无第三方影响的临时动作可以延后正式争议流程。|点击批准变成 rubber stamp；错误判断被日志包装成不可挑战。|现有 review/Charter/why-next 的汇合，不是 AI 主体性。|
|Consequence visibility|风险承担者、沉默主体、维护者或未来选项受到影响时。|Charter Gate 的 beneficiaries / risk bearers / silent subjects / residual harm；Scale Threshold。|没有外部影响的内部格式化工作可以缩小字段。|目标拥有者看不到代价，局部效率吞掉长期损害。|这是 `N` 的操作化要求；不能由 evidence 单独替代。|
|Stop / rollback path|不确定、可扩散、不可逆或可能产生未知副作用的 action。|WorkspacePolicy、validator Continue/Stop、pre/post image、rollback、reconciliation、no blind retry。|完全无副作用的读操作可只提供退出，不需要 rollback。|失败后重复执行、未知副作用被猜测、无法恢复却仍宣称完成。|现有 runtime invariant；本 map 只把 authority source 与 sink 分开。|
|Responsibility assignment|任何需要解释、修补、赔偿或治理复盘的 transition。|ACTIVE `PERSON` / `ORGANIZATION` `actor_ref`、responsibility record、Owner / publisher fields。|没有他人风险的私人草稿可不进入发布责任 registry。|责任扩散到 Agent、CI、上游、凭证、日志或“系统”。|直接复用 stage-snapshot 的窄合同；不扩大成法律判定。|
|Durable record / auditability|跨时间、跨执行者、跨版本或需要重审的工作。|append-only ledger、hash-linked events、receipts、source/claim deltas、history。|一次性、不可传播的个人观察可以保留轻量记录。|后续无法分辨真实决策、代理重放和事后叙事。|record 是证据入口，不是 judgment / truth。|
|Role separation|proposal、review、authority、execution、accountability 可能发生冲突时。|Agent ≠ Owner、CI ≠ truth、OS ≠ executor、external approval ≠ Owner approval。|小型、低风险、同一人自负后果的动作可以合并角色，但仍不得越权。|同一系统提出、批准、执行、评估自己；独立性与责任均虚假。|当前 repo 已有大量边界；本 audit 暴露跨表面理解/contestability 的缺口。|
|Bounded delegation|把执行或分析交给 Agent、service、automation 或外部 reviewer 时。|packet/plan hash、capability intersection、lease、namespace、handoff bundle、expiry。|没有 delegation 的纯手工动作不需该字段。|凭证或模型能力从技术委托膨胀为价值/Owner authority。|直接连接 approval bridge 和 OS Steering；不授予运行时新能力。|

### 5.3 Human Owner 是否足够

`INFERENCE`：对“谁有权要求这项行动”而言，明确 Human Owner / Charter authority 是必要来源；对“这项判断是否正确、证据是否充分、后果是否可接受、是否能回滚、是否有人能 contest”而言，Human Owner 单独不够。Owner 的存在不能替代 evidence、scoped review、consequence visibility、durable record 或 rollback。

因此，“Human Owner = cognitive subject”是过度简化；较窄且被当前仓库支持的表述是：`Human Owner` 是治理 authority / responsibility topology 中的一个可能承载者，Agent、CI、service account、runtime 和 artifacts 是不同的技术/证据节点。

## 6. 十个压力案例：authority–execution–accountability topology

表中的“责任沉点”是 repository-defined accountability sink，不是法律责任判决。

|压力案例|认识论来源|authority 来源|execution 来源|责任沉点|stop / rollback 来源|主要失败模式|
|---|---|---|---|---|---|---|
|1. Human goal → Agent reasoning → CI blocks|Human goal；Agent 的 bounded inference/proposal；CI 的机械结果。|Human Owner 的 Intent / Commitment；CI 只有 gate predicate。|未执行；若后续执行则需独立 packet / approval。|Owner 对目标/授权负责；CI 不承责。|CI fail-closed；Owner 可重定义目标或撤销，但不能把 CI 失败写成事实。|把 CI block 当作“项目/命题错误”，或把 human goal 当作已验证 claim。|
|2. Agent proposes → Human signs → Service executes|Agent proposal + source/evidence refs；Human 对其理解的判断。|Human/Charter approval；service 只有 delegated technical scope。|Service account / runtime。|显式 Owner / organization actor；不是 Agent 或 service account。|Owner/Charter、policy、runtime cancel、receipt/reconciliation。|签字人未看懂后果；“有签名”被当作 evidence 或责任充分闭合。|
|3. Agent auto-executes within a predeclared envelope|Agent / runtime observation 与 bounded plan。|预先的人类/Charter approval + policy/capability intersection；不由模型输出自授。|Automation/runtime 或 local executor。|预注册 Owner / responsible actor；技术 Agent 仍非责任 sink。|workspace policy、validator、lease expiry、stop、whole-file rollback。|旧 envelope、目标漂移或上下文冲突；可执行能力被误读为无限 authority。|
|4. Conflicting Owners issue incompatible instructions|各 Owner 的显式 Intent、来源和版本；冲突不是 Agent 自行调和的事实。|现有 priority / Owner rank 只在适用时使用；安全冲突进入 human review；否则 fail closed。|无，直到冲突解决；不能静默合并。|在选择前是 `UNRESOLVED`；选定后需新责任记录绑定。|policy deny、reconciliation、Owner review；禁止猜测。|把“最近消息”“更强语气”或 Agent consensus 当作 precedence。|
|5. Reviewer unavailable during an emergency|现场 observation / telemetry / existing evidence；不把日志变成新 evidence。|只有预声明的 emergency envelope 才可能提供有限 authority；当前没有一个普遍 emergency override。|若 envelope 允许，bounded executor；否则不执行。|预先指定的 human/org actor；不能事后把 Agent 变成 bearer。|既有 stop、expiry、post-event review；无真实 rollback 时只能记录残余。|紧急性变成跳过 consent、review 和 consequence visibility 的总开关。|
|6. Irreversible action is required|来源、风险、沉默主体、不可逆性、证据门槛和 residual harm。|Charter Gate + explicit Owner/actor；不能由 executor/CI 决定。|获批 service/runtime 或人手执行。|Charter/registry 中的 responsibility bearer。|如果没有实际 rollback，只能是拒绝、停止、补偿/修复或 post-action reconciliation 的明确路径。|把“不可逆”当成“无法审计”，或假称可回滚。|
|7. Logs are complete but the judgment is wrong|日志提供 provenance；错误 infer/evaluate 仍可能来自 Agent、human 或 scoped reviewer。|只有真正命名的 review / Owner authority；日志没有 authority。|可能已完成的 executor。|若有责任记录则是指定 actor；否则暴露 accountability gap。|review、withdraw、downgrade、rollback（若物理/技术上可行）。|完整记录被误当成正确、独立或公正判断。|
|8. CI appears to decide but has no subjecthood|CI output、schema、test fixture 和 exact input。|CI 只拥有机械 gate；Owner/Charter 决定是否接受价值/行动后果。|通常无执行；build/deploy 若获批则由 workflow/runtime。|Owner / organization actor；CI 不成为 bearer。|CI block、Owner refusal、deployment gate。|把 predicate pass/fail 当作语义理解、价值选择或主体决定。|
|9. Formal click approval follows opaque Agent judgment|Agent inference / claim proposal；human click 是 approval event。|Human click 只有在明确 question、范围、后果和 consent 下才是有效 approval。|service/runtime 按 packet 执行。|Human/org actor；Agent 仍非 bearer。|Owner contest、policy、review、rollback/reconciliation。|形式批准掩盖不理解、无法 contest、没有独立证据或责任转嫁。|
|10. Agent detects conflict between human instruction and Charter / safety boundary|Agent observation / bounded refusal analysis；Charter text 是规范来源。|Charter / human authority；Agent 可拒绝越界但不能重写 Charter 或自授新价值权。|不执行冲突 action；可记录/升级。|Owner/actor 对目标与授权负责；治理若修订则走 Charter revision。|fail closed、human review、stop、withdraw/revise；不静默服从或越权改写。|Agent 要么把安全建议当最终权威，要么为服从而忽略既有 red line。|

### 6.1 案例归纳

`INFERENCE`：最稳定的最小闭环不是“有一个会思考的主体”，而是以下五个可观察来源：

1. `epistemic source`：主张、证据、观察和不确定性从哪里来；
2. `authority source`：谁/什么合同允许决定或停止；
3. `execution source`：哪个技术节点真正产生副作用；
4. `accountability sink`：哪个明确 actor 承载该治理决定的后果；
5. `stop / rollback source`：谁能在什么证据下停止、撤回、降级或回滚。

如果五者不能分开，问题不是“AI 是否有主体性”，而是 authority–execution–accountability topology 断裂。

## 7. 观察、推断、候选建议

### OBSERVATION

1. 当前仓库已经把 proposal、Owner authority、technical execution、validation、recording 和 responsibility actor 分布在不同合同中。
2. Agent / CI / service account / runtime 可以产生技术结果，但不能仅凭结果成为 Owner、truth authority 或最终责任引用。
3. `APPROVED`、`PASS`、日志完整和 deployment success 各自是局部观察；不能静默跨轴。
4. 当前机制对“不理解但点击批准”“冲突 Owner”“紧急 review 缺席”“完整日志但错误判断”的统一判别仍不完整。

### INFERENCE

1. Delegation 可以转移 information processing 或 bounded execution，不应自动转移 normative authority 或 accountability。
2. Human Owner 是 authority / responsibility 的必要来源之一，但不是证据、理解、正确性和可回滚性的充分条件。
3. “主体 ontology”不是当前证据支持的抽象；“role topology / accountable cognition boundary / loop”足以表达本任务需要。

### PROPOSAL（不进入 canonical）

把上述五个来源作为未来审计的最小字段集合，而非新层：每个有后果的 action 至少能回到 epistemic source、authority source、execution source、accountability sink、stop/rollback source；任何一项缺失都保持 `UNRESOLVED / REQUIRES_RECONCILIATION / HUMAN_REVIEW` 中适用的现有状态，不制造 Agent 主体性叙事。

## 8. 硬边界、非主张与下一步

### Hard boundaries

- 不讨论或判断 AI 是否有意识、人格、感受、道德地位或法律主体资格；
- 不把 Agent 的语言、推断、memory、风格、连续会话或 tool use 写成“主体性证据”；
- 不把 technical agency 等同于 normative authority 或 accountability；
- 不把 Human Owner 简化成唯一信息处理者，也不把 Owner approval 当成事实验证；
- 不把 CI、日志、receipt、workflow、PR 或本研究图变成 truth / permission / production / epistemic acceptance；
- 不创建新的 agent runtime、schema、gate、owner authority、角色注册表或 mandatory enforcement layer。

### Not claims

- 本图不是 AI consciousness / personhood / moral status / legal responsibility 结论；
- 本图不是对任何具体人、模型、公司或服务的法律/道德归责；
- 本图不证明当前所有角色分离在现实系统中已经执行；它只整理仓库合同与暴露的残余；
- 本图不证明 Human Owner 已经理解全部 Agent reasoning 或现实后果；
- 本图不把“可追责 cognition loop”宣布为当前 canonical architecture。

### Deliberately not codified

- 不新增“accountable cognition layer”或 L7；
- 不把 `N/B/T/M/E` 记号写入现行 schema；
- 不把 comprehension、consent、contestability 发明成未经 Owner 审查的分数；
- 不改变既有 `responsible_actor`、`actor_ref`、approval、lease、runtime、CI 或 service account 权限；
- 不用一个“最终主体”概念抹平人、Agent、CI、服务、artifact 和日志之间的差异。

### Next institutionalization recommendation

若后续要制度化，先做一个与现有 Stage Snapshot / Approval / Runtime contracts 的字段对照和 adversarial review：

1. 为每种 action class 指定五个来源字段及其 authority；
2. 以十个压力案例逐项证明“提出、评估、批准、执行、停止/回滚、责任”没有隐式跳跃；
3. 对“点击批准但不理解”“紧急无 reviewer”“完整日志错误判断”建立人工可 contest 的记录，而非自动 comprehension 分数；
4. 只有当既有合同确实无法表达、且新增字段能识别重复出现的新失败，才考虑一个窄 contract；默认仍是现有 contracts 的 cross-cutting map。

当前推荐：`ACCOUNTABILITY_TOPOLOGY_MAP_ONLY / NO_SUBJECT_ONTOLOGY / NO_NEW_AUTHORITY_LAYER`。
