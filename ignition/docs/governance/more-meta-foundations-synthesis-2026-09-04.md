# 更元基础综合：价值—认识论与可追责认知的双基础审计

Status: `RESEARCH_RECORD / CANDIDATE_SYNTHESIS / NON_CANONICAL`

Task: `IGNITION-20260904-153`
Baseline: `when-systems-catch-fire` `main@212322d41db79bce2dbd116166d3f1ad226291f3`
Inputs: [六类价值—认识论推导审计](./value-epistemology-derivation-audit-2026-09-04.md)；[可追责认知边界图](./accountable-cognition-boundary-map-2026-09-04.md)

## 1. 综合问题与结论先行

本文件只在 A 审计和 B 审计独立完成后作综合。问题不是“再加一个更高的层是否更完整”，而是：

1. 六类 Evidence、Uncertainty / Claim Ceiling、Negative Capability、Ownership、Failure Budget、Degradation 是否真的是更小基础的不同投影；
2. 价值—认识论约束与 authority–execution–accountability topology 是否需要同一个新层；
3. 如果保留更小基础，它们能否诊断新失败，还是只有更漂亮的词。

综合选择：`ORTHOGONAL_DUAL_FOUNDATION / NO_NEW_CANONICAL_LAYER`。

这不是新增架构层，也不是“两个基础已经被证明”。它是一个研究结论：

- 价值—认识论面可暂用四个候选 primitive `P/O/N/A` 解释现有约束的交叉复用，但 `N` / `A` 不能从纯认识论推出；
- 可追责认知面是一个与上述基础正交的 role topology / loop，用于检查信息、授权、执行、责任和回滚是否断开；
- 二者相互约束而不是互相包含：`P/O/N/A` 不会制造 authority，role loop 也不会制造 truth 或 value；
- 当前仓库的 Kernel、Claim Ceiling、Charter、Approval、Runtime、Stage Snapshot 和 self-correction 已经承载大部分必要接口；缺口目前足以支持研究诊断，不足以支持新 canonical protocol、L7 或 mandatory enforcement layer。

## 2. 独立输入的闸门

### A 审计交付了什么

`OBSERVATION`：A 文档确认当前 canonical 仍是 V1–V4、S1–S4、E1–E4 的 12 个候选协议；12 项规范性审核都是 `CONDITIONAL_ACCEPTANCE`，0 项 formal promotion，canonical 未修改。六类审计对象是横跨证据、认识论、治理和运行时的 concerns，而不是六个同层 protocol。

`INFERENCE`：A 的最小候选解释不是一个总原理，而是：

- `P`：provenance-bounded assertion；
- `O`：option preservation / corrigibility；
- `N`：non-domination / non-externalization；
- `A`：accountable authorization。

`INFERENCE`：Evidence / Claim Ceiling 主要落在 `P`；Negative Capability / Degradation 主要落在 `O`；Ownership 主要落在 `A`；Failure Budget 是 `N + O + P` 的危险包装，不是独立基础；`N` 的价值来源仍要回到生命共同体价值宪章。

### B 审计交付了什么

`OBSERVATION`：B 文档确认当前仓库已经把 Human Owner、Agent、CI、policy/gate、service account、repository、artifacts/evidence、logs/audit trails 与 automation/runtime 放在不同的技术/治理位置。OS Steering 的链条是 `Owner Intent → Goal → Commitment → Run → bounded Action`；Runtime 的链条是 `Reasoner → Packet → Approval → Lease → Journal → Executor → Validator → Stop`；发布责任主体和技术执行者有不同字段。

`INFERENCE`：最小的可追责 loop 需要分开五种来源：`epistemic source`、`authority source`、`execution source`、`accountability sink`、`stop/rollback source`。它们可以在一次事件中由不同实体承载；把它们合并成“一个会思考的主体”反而掩盖失败。

## 3. 六种综合结论的比较

|候选结论|它说什么|当前证据能支持到哪里|综合裁定|
|---|---|---|---|
|1. `NO_NEW_LAYER`|六类只是现有 contracts 的不同阅读入口，不需要更元结构。|Kernel 已明确不是 meta-meta protocol；Attention control 还把“每个 gap 都加新层”列为吸引子；当前机制已覆盖不少边界。|作为当前架构决定，支持；作为“任何未来 gap 都不需新 contract”的普遍命题，不支持。|
|2. `LATENT_AXIOMS_ONLY`|六类背后只有若干隐含原理，显式协议只是投影。|`P/O/N/A` 能解释重复约束，且能指出混合层级。|部分支持；“隐含”不能抹掉 Charter 的独立规范来源、Owner authority 和对象局部状态。|
|3. `CONSTITUTIONAL_AXIOMS_JUSTIFIED`|本审计已证明可把若干价值/认识论基础提升为宪章级公理。|现有 Charter 是项目规范性前提，但本审计没有独立 ratification、external evidence 或治理授权。|拒绝。可提出候选，但没有升级权限。|
|4. `ACCOUNTABLE_COGNITION_LAYER_JUSTIFIED`|角色/责任 loop 应成为新的架构层或总权威。|B 暴露了跨合同断裂和理解/contestability 缺口，但没有证明新层比现有 Stage Snapshot、Approval、Runtime、Review 合同更少重复、更安全。|拒绝作为新层；保留为 cross-cutting boundary map。|
|5. `ORTHOGONAL_DUAL_FOUNDATION`|价值—认识论基础与 authority–execution–accountability loop 正交耦合。|A 的 `P/O/N/A` 与 B 的五源 loop 不能互相还原；现有仓库正好按多平面分离。|选定的研究结论；仍是 candidate model，不改 canonical。|
|6. `ONE_EXPLAINS_THE_OTHER`|要么伦理价值完全解释认识论/角色，要么认识论完全解释价值/责任。|Charter 明确价值、证据、语义审核和治理批准分开；Kernel 明确各轴独立。|拒绝。单向还原会发生 category error 或责任越界。|

## 4. 四个候选 primitive 的综合审计

以下四项是分析索引，不是 registry ID、schema 字段或新规范。每项必须有最小定义、适用范围、已解释协议、未解释内容和可证伪条件。

|候选 primitive|最小定义与必要性|仓库证据|能解释 / 不能解释|边界与可证伪条件|治理影响 / power-expansion risk|
|---|---|---|---|---|---|
|`P` provenance-bounded assertion|任何会被复查、传播、用作决策输入的 claim，都只能沿真实 source、evidence、proof、M/E、dependency、disposition 和 ceiling 传播；必要性限于需要可复核的主张/结果。|Claim Governance 的十门；Kernel K13、public ceiling、source family、withdrawal/no rebound；Non-Sycophancy 的 object/criterion/version/evidence/boundary 绑定。|解释 Evidence、Uncertainty / Claim Ceiling、部分 Degradation；不能决定某目标有无价值、谁能授权或后果是否可接受。|若某封闭形式对象有完备公理和可复算证明，可不使用经验 evidence gate；若移除 `P` 后 source repetition、scope inflation、后补理由均不增加，才可反驳其必要性。|不新增权限，只提醒每个 positive claim 回到现有 registry；风险是把可读性/流程完成误作证据，或把 provenance bureaucratize 成真值。|
|`O` option preservation / corrigibility|在不确定、可扩散或高后果动作中，尽量保留 stop、exit、rollback、reconciliation、revision 和未来选择；必要性限于存在真实选项损失的行动。|Charter Gate 的不可逆、拒绝、回滚和残余伤害；V3/E2 stop/reversible；Runtime pre/post image、reconciliation、no blind retry；Decision Collapse 保留 pre-collapse uncertainty。|解释 Negative Capability、Degradation、Stop/Exit/Recovery、部分 E1→E2 退出；不能说明哪个目标值得保留、主张是否为真或谁有 authority。|若一个封闭域所有行动都低风险、可逆且 abstention 从不减少伤害/信息/未来选项，则 `O` 在该域不必要；若 rollback 永远不能改变结果，名义 rollback 反而是反例。|不改变 runtime 行为；风险是把“保留选择”膨胀为无期限延期，或把停机当作默认善而隐藏 avoidance。|
|`N` non-domination / non-externalization|不得以局部目标把非自愿、不可逆、不可见的生命共同体代价转嫁给受影响者、沉默主体、维护者或未来参与者；必要性来自 Charter 的价值承诺，而非证据逻辑。|生命共同体 Charter 的一宇/今宵/共在/长瞻、风险承担者/沉默主体/残余伤害；V2 全成本、V4 再生、S1/S2 防掠夺、E4 保留多样性。|解释为什么 Failure Budget 不能是伤害额度、为什么 irreversible action 需要更强 gate、为什么 continuity/efficiency/innovation 受限；不能生成事实证据、Owner 身份或具体权重。|若移除 `N` 后任何局部优化均不改变风险承担者、沉默主体和未来选择，或者仓库能证明不存在外部化对象，才会削弱其必要性；现实中两者都未被本仓库证明。|若接受，只能强化 Charter Gate 的可见性字段；风险是把规范性前提包装成自动“善恶分类器”，或扩大到法律/道德结论。|
|`A` accountable authorization|有后果的决定必须有合法 authority / consent 来源、可 contest 路径和可识别责任承载者；技术能力/credential/approval event 不能自动充当它；必要性限于跨主体、公共、不可逆或需要事后解释的决定。|OS Steering Owner transition；Approval Bridge strict intersection；Stage Snapshot ACTIVE `PERSON`/`ORGANIZATION` actor_ref；S3/S4 责任可问责/可追溯；Charter revision procedure。|解释 Ownership、proposal→approval→execution 分离和 responsibility sink；不能证明签字者理解、主张正确、风险合理或回滚可行。|个人低风险可逆动作可简化 authority；若在高后果事件中移除 `A` 仍能稳定回答谁批准、谁能 contest、谁停/回滚、谁承载后果，才可能反驳。|不创建“最终主体”层；风险是把责任 registry 误当作充分伦理/法律归责，或借“Owner”扩张权限。|

### 4.1 组合覆盖而非还原

`INFERENCE`：四个候选并不是独立的四个宇宙公理。它们构成一个交叉覆盖：

```text
P ──> evidence / claim ceiling / public wording
│
└──> bounded inference ──> O ──> stop / exit / downgrade / rollback

N ──> affected parties / non-externalization / residual harm
│                                  │
└──────────────> A ──> consent / authority / accountability sink
```

这张图只表示研究中的解释关系，不表示现实因果、数学推导或 registry dependency。`P` 约束“能说什么”，`N` 约束“不能以谁为代价”，`A` 约束“谁能决定并承载”，`O` 约束“在不确定时保留什么选择”。没有一项单独覆盖其余三项。

## 5. 是否产生了新的失败诊断

### 5.1 不是只换词

如果 `P/O/N/A` 只是把已有 `evidence / ownership / rollback / claim ceiling` 换成更抽象的别名，本审计就不应推进。当前证据支持的增量在于：它们把不同已有合同的“交叉缺口”放到同一个压力测试中，产生四个可观察诊断；但这些诊断仍未经过真实世界或独立复现。

|候选诊断|最低可观察谓词|现有机制能否完整发现|研究增量|若未来反复出现的下一步|
|---|---|---|---|---|
|`PROVENANCE_WITHOUT_CEILING`|有 source/evidence/hash，但 public wording 或 action choice 越过该 source 的 scope。|Claim ceiling、K13、public-surface gate 能发现部分；跨到 action 的 mapping 仍可能断开。|把“证据存在”与“证据足以支持该动作/措辞”分开。|为 claim→action boundary 做窄 review contract；不新增总层。|
|`ABSTENTION_AS_AVOIDANCE`|记录了 stop/等待，但没有 deadline、next evidence、opportunity cost、责任人或 contest 路径。|Attention control 能标 `RUMINATION_RISK`；当前没有统一判别字段。|把 Negative Capability 与无行动/拖延区分为可审计条件。|先增加案例和人工 review；不可直接加“负能力协议”。|
|`BUDGET_AS_HARM_LICENSE`|风险/失败预算已耗用或未耗用，被写成可接受伤害的许可。|Charter Gate、V2/V4、risk cap 可否定，但“failure budget”未命名、未专门检测。|把工程 budget 与 normative residual harm 分开，避免正常化偏差。|若多次发生，考虑现有 action budget 文档的明确负面字段。|
|`SIGNATURE_WITHOUT_CONTESTABILITY`|有 Owner/签名/actor_ref，但没有表明签字者看到的后果、异议、范围和撤回路径。|Stage Snapshot 验证身份；Approval 验证 gate；不自动验证 comprehension/contestability。|识别“责任身份存在”与“授权可争议”之间的断裂。|设计人工可读 review record，不做自动理解分数。|
|`COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY`|事件、日志和 artifact 完整，但无明确 accountability sink 或 stop/rollback source。|日志与 registry 各自能发现部分断裂；跨表面连接不总是一个 predicate。|把 auditability 与 accountability 明确分离。|为 high-consequence transition 建跨合同闭合检查。|

`INFERENCE`：因此本审计有诊断增量，但它是“跨切面测试增量”，不是新真值层或新的主体本体。若这些诊断在未来没有独立复现，四个标签就应降级为导航词，不应保留为治理规范。

### 5.2 诊断的可证伪门

每个候选必须接受以下强反例：

1. 找到一个高后果事件，在 `P/O/N/A` 缺失其一时仍能由现有 contract 完整回答来源、授权、执行、责任、停止和后果，而且没有新增误判；
2. 找到一个事件，增加该 primitive 后只增加文档负担，没有改变任何 decision、claim ceiling、stop、rollback、contestability 或责任可见性；
3. 找到一个由该 primitive 触发的系统性误阻断，且原有更窄规则不能通过限定适用域修复；
4. 证明某一 primitive 只是另一个局部字段的同义别名，删除它不会丢失任何独立 failure mode；
5. 在不同 Owner、不同 reviewer 或不同执行者下重复测试，结果仍完全由人员偏好决定，无法形成稳定的判定边界。

目前没有执行这些反例的独立实验或外部证据；本文件只登记它们作为未来 falsifiers。

## 6. 六类与四基础的最终映射

|六类|首要 primitive|次要 primitive|综合解释|不可还原部分|
|---|---|---|---|---|
|Evidence|`P`|`A`|先问来源、独立性、scope、M/E 与可复查性；若用于行动，再问谁有权使用。|Evidence 不能推出价值或授权。|
|Uncertainty / Claim Ceiling|`P`|`O`|先把 claim 限在证据范围，再决定是继续取证、降低动作强度还是停下。|不确定性不能单独决定风险权重。|
|Negative Capability|`O`|`P/N`|有边界的 abstain、pause、stop、reconcile；不行动也要有 reason、deadline、next evidence 和 accountability。|不能从“知道不确定”推出“必须等待”。|
|Ownership|`A`|`N`|把 proposal、authority、execution、责任沉点分开；Owner 是 authority source 的一种治理实现。|有 Owner/actor 不等于理解、正确或合乎价值。|
|Failure Budget|`N/O`|`P`|只可作为受限工程/试验 budget；不能成为伤害许可证或 truth threshold。|该命名没有独立 canonical 语义，应保持 unsupported。|
|Degradation|`O`|`P/A`|证据或状态恶化时允许 downgrade/quarantine/withdraw/reconcile，保留历史并收窄传播。|没有跨所有对象的统一 degradation order。|

## 7. 当前治理决策与权力边界

### OBSERVATION

- Kernel 已将跨平面共享规则定义为 typed handoff / no-upgrade；它明确 `L0–L6` 不增加 L7，且没有覆盖所有 ceiling vocabulary 的无损总顺序。
- Charter 已明确它是最高规范性边界，但价值、事实、语义审核和 governance approval 分开；其具体冲突程序要求记录影响、异议、试行、回滚和底线。
- OS / Runtime / Approval / Stage Snapshot 已把技术 agency 与 authority、validation、responsibility 分开；执行 Agent 和自动化不得成为最终责任引用。
- Attention / Distribution control 已明确“每个 gap 变新层”“CI success 变理论 success”“同源 Agent 输出变独立证据”是项目级吸引子。

### INFERENCE

当前更稳妥的治理动作是把本次结论放在研究记录和治理索引中，让它可被搜索、反驳和引用；不把它写入 canonical protocol、capability registry、Current identity、state changelog、schema 或 runtime。一个新层若没有新 authority、new evidence、new capability 或独立 failure reduction，只会扩大解释面和权限误读风险。

### PROPOSAL（不进入 canonical）

1. 把 `P/O/N/A` 与五源 loop 作为 future review vocabulary，保留明确 `CANDIDATE / NOT_CANONICAL`；
2. 后续任何制度化任务必须先声明目标是修复现有 contract 的交叉缺口，而不是创建 meta-meta protocol；
3. 用压力案例比较“现有 contract + cross-cutting map”与“新增 layer”的误阻断、漏检、维护负担和 authority expansion；
4. 若没有可重复的独立增量，则明确关闭探索并保留负结论。

## 8. 反矛盾与待解决问题

|未决问题|当前处理|为什么尚未关闭|
|---|---|---|
|多个 Owner 冲突时谁能授权|记录所有 candidates；安全冲突 human review；permission fail closed；不按语气/时间猜测。|现有 Owner rank / priority 不能覆盖所有价值冲突，也没有普遍 precedence。|
|紧急动作而 reviewer 不在|只有预声明的 bounded emergency envelope 才可能做有限动作；否则停下并记录。|当前没有一个覆盖所有域的 emergency authority / comprehension contract。|
|不可逆 action 的 rollback|若真实上不可回滚，则使用拒绝、停止、补偿/修复、残余记录或 post-action review；不能伪造 rollback。|价值是否允许该不可逆后果必须由具体 Charter/Owner 语境决定。|
|日志完整但判断错误|保留日志，另走 scoped review、withdraw/downgrade、外部 evidence 或 human contest。|record、evidence、review、responsibility 四者没有单一总权威。|
|Failure Budget 是否应该保留|保留工程 budget 语义；拒绝其作为价值/伦理 primitive。|尚无最小定义能排除 normalization of deviance。|
|是否需要新 meta layer|当前不需要；只在现有 contract 无法发现、且压力案例反复再现时重新评估。|新层的新增权限、迁移、validator 和责任成本尚未被证明可接受。|

## 9. 不主张、明确不编码与下一步

### Not claims

- 不主张 `ORTHOGONAL_DUAL_FOUNDATION` 是数学定理、现实真理或已获 Owner ratification；
- 不主张四个 primitive 是唯一、完备或不可再分的基础；
- 不主张本综合改变 V/S/E 12 协议、64 组合、Ψ₀、L0–L6、Current identity、M/E 或 `EPISTEMICALLY_ACCEPTED`；
- 不主张 Agent、CI、service account、runtime、日志或 artifact 具有人格、意识、道德主体性或法律责任；
- 不主张 Human Owner 单独足以保证证据、理解、同意、正确性、可逆性或公平后果；
- 不主张“更多抽象”本身提供更高治理质量。

### Deliberately not codified

- 不新增第 13 个元协议、L7、meta-meta protocol 或统一价值函数；
- 不新增 `P/O/N/A`、五源 loop、comprehension score、failure budget 或 universal degradation order 的 schema / registry / validator；
- 不把本研究作为 Charter revision、Owner approval、production readiness、external truth、publication acceptance 或 epistemic acceptance；
- 不改变 executor、service account、policy、approval、rollback、CI 或 Current 传播权限；
- 不把诊断词写成事实因果或现实预测。

### Next institutionalization recommendation

若 Owner 要继续，下一任务应是一个小范围 `RESEARCH_TO_CONTRACT` 审计，而不是新架构任务：

1. 冻结四个 primitive 的最小定义、适用域、输入和 falsifier；
2. 以 A 的 7 个和 B 的 10 个压力案例形成去重后的 adversarial set；
3. 对每个案例记录现有 contract 能否发现、误阻断、漏检、责任 sink 和 stop/rollback source；
4. 让独立 reviewer 针对命名 question 评估并允许 `ABSTAIN`；
5. 只有在结果显示稳定的新 failure reduction 且无 authority expansion 时，才讨论把字段加到现有 contract；
6. 任何新 canonical layer 仍需独立 Owner / review / exact-head / merge / current 流程，不能由本文件自授。

最终综合状态：`RESEARCH_COMPLETE / NO_CANONICAL_LAYER_RECOMMENDED / KEEP_EXISTING_FEDERATED_CONTRACTS / OPEN_TO_FALSIFICATION`。
