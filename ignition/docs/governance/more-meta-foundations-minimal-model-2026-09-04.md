# 153 反证轮：通过消融后的最小模型

Status: `RESEARCH_RECORD / MINIMAL_MODEL / NON_CANONICAL`

Task: `IGNITION-20260904-154`
Predecessor: `IGNITION-20260904-153`, candidate head `08c837cd5d74b9ac14dcea7288c77786e10e3bac`
Scope: 记录 153 候选被反证后仍有用的最小审计表示；不把任何表示提升为新协议、schema、registry、权限或 Current。

## 1. 结论

严格最小的 canonical 选择是：`EXISTING_FEDERATED_CONTRACTS_ONLY`。

对研究和 review 仍有用、但不能制度化的最小视图是：

`EXISTING_FEDERATED_CONTRACTS + CROSS_CONTRACT_REVIEW_MAP`

其中 review map 可以使用 `P/O/N/A` 和五源 topology 作为临时标签，但这些标签没有独立状态、没有 authority effect、没有自动 disposition，也不进入 registry。它们的保留判定是 `SURVIVES_AS_HEURISTIC_ONLY`，不是新基础。

153 的强综合 `ORTHOGONAL_DUAL_FOUNDATION` 在 154 的 strict minimality 与 strict orthogonality 测试下为 `FALSIFIED`。更窄的结论如下：

- `P`：已有 Claim Governance、Kernel、Non-Sycophancy 和 source lineage 已承载，作为 primitive 冗余；可做 provenance-to-action review 标签。
- `O`：已有 stop、pause、rollback、reconciliation、degradation 和 attention controls 的跨对象关系；可做 option-preservation review 标签。
- `N`：仍表示 Charter 的规范性边界，不能从 evidence 或 topology 推出；保留为价值前提的审计提醒，不当作通用可计算 primitive。
- `A`：不属于独立基础；拆成 authority source、approval/consent、accountability sink、contest/revocation 与 stop path 的 junction review。
- 五源 loop：是角色和记录边界图，不是新生命周期或统一主体模型。

本文件不说“更少的抽象必然更安全”；它只说，在当前仓库证据下，新增基础层没有显示出独立 failure reduction，因而不能越过现有联邦合同。

## 2. 最小模型的判定规则

### 2.1 Canonical minimality

一个候选模型只有在同时满足以下条件时，才可能被考虑为新的 canonical contract：

1. 指明不由现有合同承载的独立输入和输出；
2. 删除它会丢失可重复、可观察且非同义的 failure detection；
3. 有稳定适用域、明确 predicate、反例和误阻断控制；
4. 不把 review vocabulary 变成 authority、truth、capability、Current 或 lifecycle effect；
5. 相对于“现有合同 + 人类交叉审查”，有可观察的净收益。

当前没有满足第 2、3、5 项的候选。`N` 有不可从事实字段替代的规范来源，但它的来源已经是 Charter，不能据此再造一个更底层的规范层。

### 2.2 Audit-map minimality

研究表示只需要保留三种边：

|边|问题|最小来源|
|---|---|---|
|claim edge|这个措辞/推断是否仍在 source、M/E、evidence 和 ceiling 内？|Claim Governance、Kernel、Non-Sycophancy。|
|authority edge|谁可以批准、拒绝、暂停或要求回滚？批准是否只缩窄已声明 capability？|Charter、OS Steering、Approval Bridge、Policy compiler。|
|consequence edge|谁执行、谁记录、谁观察后果、谁承载责任、谁可以争议或撤回？|Runtime、Stage Snapshot、responsibility registry、review records。|

如果一项 review 需要跨越三条边，使用临时 junction question 即可；不需要先创建统一 meta layer。若未来要把某条边写进现有 contract，必须为该 contract 提供独立字段理由和 exact fixture。

## 3. 候选模型比较

### 3.1 模型定义

|模型|组成|它承诺的最强内容|
|---|---|---|
|`M4`|`P/O/N/A + five-source role topology`|四 primitive 形成双基础，topology 作为第二基础，二者正交但相互补足。|
|`M3a`|`P/O/N + role topology`|移除 A，把 authority/accountability 作为 topology 的边。|
|`M3b`|`P/N/A + O derivative`|把 option preservation 作为 P/N/A 的派生结果，而非 primitive。|
|`M2+T`|`existing contracts + cross-contract review map`|不新增基础，只把 claim、authority、execution、accountability、stop/rollback 的交叉点显式画出。|
|`Existing-only`|当前 Charter、Claim Governance、Kernel、OS Steering、Approval、Runtime、Stage Snapshot、审计与生成面|不增加模型；按对象合同和既有 review 处理问题。|

### 3.2 九维比较

|维度|`M4`|`M3a`|`M3b`|`M2+T`|`Existing-only`|
|---|---|---|---|---|---|
|六类语汇覆盖|高，但用四项压缩多个层级|中高，A 缺位由图边代替|中高，O 的等待/回滚边界易被低估|高，直接链接已有局部合同|足够，但需要逐合同阅读|
|source / claim ceiling|P 解释清楚|P 解释清楚|P 解释清楚|直接指向 Claim/Kernel|已有完整局部机制|
|value / non-externalization|N 可见，但可能被误作算法|N 可见|N 可见|指向 Charter，不造新规范|Charter 直接承载|
|authority / consent|A 使其显式，但有原子化幻觉|由 topology 表示，合法性仍外置|A 仍过度压缩 consent 与 sink|按 Approval/Owner/Charter 分开|已有明确 Owner/Approval 规则|
|execution / stop / rollback|O 与 runtime 关系清晰但重叠|图边表达，适用域可能含混|O 被派生，可能漏掉等待成本|直接使用 Runtime/Charter 对象边界|已有对象局部路径|
|accountability / contest|A 提醒缺口，但不能提供 predicate|topology 能找节点缺失，不能判合法责任|A 与 contest 仍是压缩词|可把 sink、actor、contest 分列|发布场景已有 actor；通用 run 需人工复核|
|可重复性|未形成 fixture；最低|未形成 fixture；最低|未形成 fixture；最低|可把 fixture 绑定到既有合同，仍待实证|各既有 validator 有自身可重复性|
|权力/权限扩张风险|最高：容易读成新基础或新 gate|中：容易把图边读成 authority|中：容易把派生关系读成必然|低：明确是 review map|最低：不增模型|
|维护与 claim 成本|最高：新词、边界、冲突和反弹多|高|高|中：需保持 map 与合同同步|最低，但交叉审查负担留在人类阅读|

`VERDICT`：`M4` 的解释面最宽但最不满足最小性；`M3a`、`M3b` 只改变压缩方式，没有新 failure reduction；`M2+T` 是最小的研究表示；`Existing-only` 是最小的 canonical 选择。

### 3.3 最小模型的分层结果

```
canonical contract layer:
  Charter + Claim Governance + Kernel + OS Steering + Approval + Runtime
  + Stage Snapshot + responsibility registry + existing validators

research review layer:
  claim edge / authority edge / consequence edge
  optional labels: P / O / N / A
  optional map: epistemic source -> authority source -> execution source
                -> accountability sink -> stop/rollback source

not present:
  new primitive state, L7, meta-meta protocol, universal precedence,
  automatic comprehension or harm score, capability expansion
```

这张图不是仓库运行时流程；它只帮助 reviewer 在已有文件之间定位 junction。每个箭头仍必须回到其 source contract，图不能成为第二 authority。

## 4. A 的最终位置

### 4.1 A 的分解

用最小视图表示 A 时，至少分成以下五个问题：

|A 的组成|当前来源|能做什么|不能自动推出|
|---|---|---|---|
|authority source|Owner Intent、Charter、Approval decision 的显式来源|识别谁在什么范围内可以批准、拒绝或暂停。|不能推出事实正确、理解全部后果或对所有受影响者有同一价值判断。|
|approval / consent|Approval Bridge 的 strict intersection、Charter Gate 的 consent/participation|阻止未声明或未批准的 action 进入执行。|技术 `ALLOW` 不能替代 Charter 语境中的同意与异议。|
|accountability sink|Stage Snapshot 的 active `actor_ref`、responsibility actor registry|为特定发布/治理对象指定可解析的责任承载者。|Runtime 的 `actor_id`、service account 或日志存在不等于治理责任 sink。|
|contest / revocation|review、dissent、withdraw、pause、rollback、reconciliation 现有路径|让决定可以被质疑、撤回、停止或重新审查。|有日志或回滚字段不等于真实存在可用的争议或恢复路径。|
|consequence visibility|Charter 的 risk bearers/silent subjects/residual harm，加上 action impact summary|把行动代价带回审查问题。|不能由一个签名字段证明审查者看见了全部后果。|

这些组成的输入、authority 与 failure 含义不同。把它们重新命名为 A 不会使它们成为一个不可分割 primitive。

### 4.2 不带 A 的结果

如果只使用 `P/O/N + role topology`：

- 能保留“capability 不等于 authorization”的显式非升级规则；
- 能保留“technical actor 不等于 responsibility sink”的角色分离；
- 能指出某个图缺少 authority source、accountability sink 或 stop/rollback edge；
- 不能单独判断 consent、Charter conflict、等待成本或后果可见性是否足够；
- 不能把一个 runtime run 的技术 trace 自动升级为治理 responsibility closure。

因此 A 的独特贡献是把 junction 问题命名为“可追责授权闭合”，但它不提供不能由既有合同拆出的新状态。最终 placement：`CROSS_CONTRACT_JUNCTION / HEURISTIC_ONLY`。

## 5. 正交性最终判定

### 5.1 分析独立与操作耦合

P/O/N 与 authority–execution–accountability topology 仍然是不同的观察角度：前者问 claim、价值边界和选项，后者问角色、权限、执行、记录和责任沉点。但以下操作耦合已经足以否定 strict orthogonality：

1. action 是否可执行既取决于 capability/approval，也取决于 Charter 的风险承担者、不可逆性和残余伤害；
2. public wording 或 action reason 既取决于 source/ceiling，也影响 signer 是否需要重新审查；
3. contest、pause、rollback 既是 role topology 的边，也是 option preservation 的表现；
4. 完整 trace 只能证明记录完整，是否有 accountability sink 取决于另一张 registry 或发布合同；
5. deadline/窗口可能改变应否继续取证或应否停止，不能由任一侧独自排序。

`VERDICT`：`ORTHOGONALITY_METAPHOR_REJECTED`；较准确的描述是 `COUPLED_BUT_NON_REDUCIBLE_REVIEW_AXES`。这个描述不授予新层。

### 5.2 四象限的最小使用法

|A-side P/O/N|B-side topology|review action|
|---|---|---|
|PASS|PASS|沿已有合同逐项确认；不产生新 promotion。|
|PASS|FAIL|收窄/暂停 action，补做 authority、sink、contest 或 stop review。|
|FAIL|PASS|收窄 wording/claim，必要时撤回或要求 evidence/ceiling review。|
|FAIL|FAIL|fail closed，保留记录，等待 scoped human/context reconciliation。|

四象限只是组合测试表。它说明两个轴不能互相推导，不说明两个 axis 需要两个 foundation。

## 6. 五个诊断的最终处置

|诊断|最小现有承载|最终子判定|允许的使用|禁止的使用|
|---|---|---|---|---|
|`PROVENANCE_WITHOUT_CEILING`|Claim record + public wording + action reason/plan 的 junction review|`CROSS_CONTRACT_LENS`|在 review 中要求 claim/source/ceiling 与 wording/action 同时出现。|不新增 universal claim-to-action schema 或自动 truth gate。|
|`ABSTENTION_AS_AVOIDANCE`|Stop/abstain/reconcile + Steering deadline/unknowns + next-evidence human question|`CROSS_CONTRACT_LENS / OPEN`|要求说明 reason、deadline、next evidence、等待代价、责任与 contest。|不把等待自动标成审慎、逃避或新 disposition。|
|`BUDGET_AS_HARM_LICENSE`|Policy minimum budget + Charter residual-harm/irreversibility + forbidden effects|`REDUNDANT_AS_FAILURE_CLASS`|作为预算和价值许可分离的反误读提示。|不把 resource budget 转成 harm quota、consent 或价值评分。|
|`SIGNATURE_WITHOUT_CONTESTABILITY`|Approval decision + actor registry + Charter/review/withdraw path|`CROSS_CONTRACT_LENS`|检查 action digest、signer scope、impact view、contest/refuse/revoke path。|不增加 comprehension score，也不把 `ALLOW` 当作理解证明。|
|`COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY`|Trace/journal + Stage Snapshot actor_ref + responsibility registry|`CROSS_CONTRACT_LENS`|检查 technical actor 与 governance sink 是否分别可解析。|不把日志、CI 或 artifact 变成责任主体，也不自动补写 actor。|

五个诊断均不进入 current registry。`NEW_FAILURE` 本轮没有得到支持：没有一个诊断被独立运行 fixture 证明为超出已有 contract 的新错误类。

## 7. 冲突与治理处置

### 7.1 当前能做的事

- Claim/Kernel 可以收窄断言并保留 unknown、missing、blocked、rejected、abstain 等不同状态。
- Charter/Approval/Policy 可以阻止无授权、越界 capability、禁止 effect 或未经审查的高风险动作。
- Runtime 可以在 lease、budget、workspace、validator、preimage 和 journal 条件下执行、停止、回滚或 reconciliation。
- Stage Snapshot 可以在发布合同中绑定 active accountable actor，并保持 published/accepted/current/activated 分离。
- OS Steering 可以记录候选、owner rank、deadline、fairness、dependency、risk、permission、unknowns 与 reconciliation；不可比时不虚构总顺序。

### 7.2 当前不能自动做的事

- 不能从 source completeness 自动决定某个时间窗口内的最佳行动。
- 不能从 pause/abstain 自动决定等待是否造成可避免损害。
- 不能从 budget 剩余量推导价值许可或受影响者同意。
- 不能从签名、actor_ref 或 trace 推导理解、contestability 或恢复成功。
- 不能从日志完整性推导责任判断正确，也不能从技术 actor 推导治理 sink。

这些残余需要 specific object、Charter context、Owner/affected-party input、scoped reviewer 或明确的 human reconciliation。它们不构成统一 arbitration layer 的证据。

## 8. 不改变的当前边界

本最小模型不改变：

1. V/S/E 12 个候选协议及其 conditional review 状态；
2. Charter、Kernel、M/E、claim ceiling 与 K13 assertion non-escalation；
3. Owner → Intent → Goal → Commitment → Run → Action 的 steering chain；
4. Approval strict intersection、local workspace executor、lease、journal、validator、stop、rollback 与 reconciliation；
5. Stage Snapshot 的 active actor、published/accepted/current/activated 分轴；
6. Current identity、open obligation、live external ceiling、CI/gate、provider、authenticated channel 与任何 executor capability；
7. `STATE-CHANGELOG.md` 的当前状态和正式任务生命周期。

本任务是 Draft 候选上的 docs-only research。若新文档触发 Knowledge Experience 或人类导航的确定性更新，那些更新只是源文档的派生可读投影，不是 Current 或 canonical promotion。

## 9. 未来复核的必要条件

只有在未来任务同时给出以下材料，才可以重新评价是否需要修改某个既有合同：

1. 一个具名对象和高后果 transition，而不是抽象的“系统”；
2. 完整输入字段、当前 validators 的实际结果和最小 countermodel；
3. 当前合同无法表达的具体 predicate，以及新增字段如何改变 stop/review/claim ceiling；
4. 至少一个 independent reviewer，允许 `ABSTAIN` 并记录反例；
5. 误阻断、漏检、迁移成本、权限影响和责任路径的比较；
6. 明确不把 Draft research、CI green、PR 状态或 projection 变成 acceptance。

在这些证据出现之前，最终推荐保持：

`EXISTING_FEDERATED_CONTRACTS_ONLY / CROSS_CONTRACT_REVIEW_MAP_ALLOWED / NO_NEW_CANONICAL_LAYER / OPEN_TO_REPRODUCTION`。
