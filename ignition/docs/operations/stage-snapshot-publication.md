# 阶段成果持续快照与分层发布制度

Status: `Ignition Iteration Method 1.4.0 — Continuous Stage Snapshot Publication`（已升为 Current；1.3.0 转为 Historical）。

本制度现由 Current 方法 `1.4.0` 承载（1.3.0 转为 Historical）。作为正交发布轴，它不改变能力生命周期；R5-A 快照已发布为 `PUBLISHED_SNAPSHOT`，但仍非 Accepted/Current/Activated，不得利用自身规则快速合并候选能力。

责任主体窄修复状态：PR #134 的精确头 `5a856c031616ec0a959150baebb7edced34f22bc` 因 A15c/A15d 可把 Agent 或自动发布流程伪装成负责组织而被拒绝；第一轮修复 PR #135 精确头 `567aef78345564adb646b59590924cf24f4bbc45` 又因 44/104 个 Schema 旁路、四个 Schema/runtime 双重旁路及 runner 单表面误报被拒绝。R2 把责任身份收紧为 registry 解析的 `actor_ref` 并修复双表面门；PR #135 精确头 `c13da782` 经独立验收并合入 PR #134 来源分支（head `48f87616`），PR #134 经 R2 main closeout 普通合并入 Main（merge commit `f9abf90e`）；方法 1.4.0 经受控同步 R1-20260726 升为 Current，1.3.0 转为 Historical。

## 1. 两条正交状态轴

能力生命周期保持不变：

`Candidate → Ready → Accepted → Merged Capability → Current → Closed`

阶段成果发布轴独立存在：

`UNPUBLISHED → PR_VISIBLE → PUBLISHED_SNAPSHOT → SUPERSEDED_SNAPSHOT / WITHDRAWN_SNAPSHOT → HISTORICAL_SNAPSHOT`

机器 registry 必须逐项保存以下不等式，validator 必须按完整集合检查：

- `PUBLISHED_SNAPSHOT != ACCEPTED`
- `PUBLISHED_SNAPSHOT != CURRENT`
- `PUBLISHED_SNAPSHOT != ACTIVATED`
- `SNAPSHOT_MERGED_TO_MAIN != CANDIDATE_PAYLOAD_MERGED_TO_MAIN`
- `HOMEPAGE_VISIBLE != CAPABILITY_AVAILABLE`

“进入 Main”首先只表示 `data/operations/stage-snapshots.json` 和它的确定性展示投影进入 Main。它不改变正式 capability registry，不合并候选载荷，也不启用运行时入口、workflow 或 executor。

## 2. 权威链

1. `data/operations/responsibility-actors.json` 是最终责任身份的受控注册表，受 `schemas/operations/responsibility-actor-registry.schema.json` 约束；
2. `schemas/operations/stage-snapshot-registry.schema.json` 与 `stage-snapshot-request.schema.json` 的 `actor_ref` 集合由该注册表确定性生成；
3. `data/operations/stage-snapshots.json` 是阶段快照唯一仓库权威；
4. `tools/operations/stage_snapshot_contract.py` 做 schema、actor reference 解析、语义、隐私、关系、远端 identity/HEAD 和投影检查；
5. 阶段快照只确定性生成并校验 `docs/generated/recent-stage-results.md`（专用页面）；不再向 README 插入「正在炼化」模块或 STAGE-SNAPSHOTS 标记。人类阅读层通过仓库 Markdown 直接链接该页面；
6. PR body 与 1111 回执保存 exact-final-HEAD、GitHub Actions run ID 和外部审查结论。

`docs/generated/recent-stage-results.md` 是阶段快照的唯一展示投影，不能成为第二份人工状态源。`--check` 重新渲染该专用页并逐字比较；registry 变化但该专用页未同步时失败。README 首页不含阶段快照块，由 `validate_human_front_door.py` 单独保证「正在炼化 不在 README」。

## 3. 轻量但失败关闭的发布门

阶段快照门比能力接受门轻，只审查公开摘要的真实性与边界，不重新裁决候选能力本身。每条记录必须：

- 解析来源仓库、PR、分支、精确 HEAD，以及 1111 回执或等价证据入口；
- 显式记录生命周期状态、发布状态、结果类型、完成项、未完成项、claim ceiling、限制和阻断；
- 显式记录 Accepted、Current、Activated、正式能力影响与实际应用许可五个布尔状态；
- 只含可公开摘要，不含隐私、密钥、受限原始材料或本机路径；
- 以 `PERSON` 或 `ORGANIZATION` 正向合同记录最终责任主体与发布主体，另外记录执行 Agent 和自动化工作流，禁止把技术执行者伪装成最终责任，也禁止把责任自动推给创始人或上游项目；
- 保留前驱、后继、替代、撤回、修订与回滚路径；
- 保证主页文字由 registry 确定性生成；
- 保证失败实例逐案阻断，不能用测试总数或绿色 CI 掩盖。

在线远端验证使用：

```bash
python3 tools/operations/validate_stage_snapshots.py --check --verify-remotes
```

CI 的仓库内门使用确定性 schema、语义和投影检查；独立验收者还必须在线重新获取 PR 身份、HEAD 与 Actions，不能只采信记录时间的 attestation。

### 3.1 责任主体正向合同

`responsible_actor` 与 `publisher_actor`（请求接口中为 `proposed_publisher_actor`）只能保存一个 `actor_ref`。该引用必须解析到 `data/operations/responsibility-actors.json` 中状态为 `ACTIVE` 的条目；自由文本姓名、显示名、角色名或临时组织声明都不能自封为最终责任身份。注册表条目只能是：

- `PERSON`：具体、可识别的人类责任主体，注册表保存正式姓名、`person:` 稳定 ID、明确角色、责任依据和可追溯联系人入口；
- `ORGANIZATION`：现实中可识别且能承担治理或发布责任的组织，注册表保存正式名称、`org:` 稳定 ID、明确角色、责任依据和负责人／治理入口。

新增责任主体必须是独立、可审查的 registry 变更，并带生效／退役状态、来源和连续历史；快照请求不能临时创建主体。Schema 只接受当前 ACTIVE 引用的确定性 enum，runtime 再解析同一 registry；生成器和 validator 会阻断 enum 陈旧、两份 Schema 集合不一致、记录删除／篡改、不存在或退役引用。显示名称从 registry 投影，快照不能覆盖。合理含有 “automation” 的已审查现实组织不会仅因显示名被误杀，但自动系统不能靠名称进入 registry。

自由文本旧字段 `responsible_person`、`responsible_organization`、`executor` 与 `publisher` 不再属于开放接口，旧的结构化自由文本 actor 对象也不再属于新接口；它们因 `additionalProperties=false` 或缺少有效 `actor_ref` 而失败关闭。`execution_agents` 与 `automation_workflows` 只记录技术执行和因果链节点：Agent、模型、机器人、算法、工作流、CI、脚本、软件、平台或系统可以出现在这里，但不得成为最终责任引用。

每条 registry 记录还必须有独立 `responsibility_record`。责任主体变化时，必须建立新的 snapshot revision，以新的责任记录 ID 显式指向前驱责任记录；validator 拒绝静默覆盖。该合同是有限的仓库发布问责门，不是完整因果与责任宪章，也不作法律责任判断。

稳定逐案门由 `tests/stage_snapshot_responsibility_actor_cases.json` 定义，`tools/operations/run_stage_snapshot_responsibility_cases.py` 输出每个 ID、字段位置、Schema 结果和 runtime 结果。攻击只有 `Schema=REJECT AND runtime=REJECT` 才通过；正例只有 `Schema=ACCEPT AND runtime=ACCEPT` 才通过，任意表面分歧均使门返回非零。既有 26×4 位置与新增四种自动发布变体×4 位置分别报告，不得再用模糊总数或绿色 CI 代替。

## 4. 显示语义

- “项目现状”说明 Current 正式能力；“正在炼化”是阶段成果标签，现仅出现在专用页 `docs/generated/recent-stage-results.md`，说明 PR 可见候选和阶段成果；README 首页不再嵌入该块。
- `REJECTED`、`FAILURE`、`WITHDRAWN` 必须在摘要中直接显示拒绝、失败或撤回。
- `SUPERSEDED_SNAPSHOT` 必须指向后继；历史快照不抹除原始证据。

当前首个真实试点是 R5-A。它只说明两轮具体合同修复已独立验收并进入 R5-A 宪章来源分支（PR #130，整体仍 OPEN/DRAFT）；其阶段快照记录在 PR #134（责任主体修复栈）普通合并入 Main 后，经本受控同步由 `PR_VISIBLE` 更新为 `PUBLISHED_SNAPSHOT`。R5-A 候选本身仍非 Main、非 Accepted、非 Current、非 Activated；R5-B、R5-C、R6 未启动。它不证明 R5-A 已完成、生命完整性、人体安全、疗效或普遍语义能力。

本受控同步将试点状态由 `PR_VISIBLE` 更新为 `PUBLISHED_SNAPSHOT`，`snapshot_record_merged_to_main=true`（记录经 PR #134 普通合并入 Main）；`PUBLISHED_SNAPSHOT != ACCEPTED/CURRENT/ACTIVATED` 不等式保持不变，R5-A 候选本身仍非 Accepted/Current/Activated。

## 5. 修订、替代、撤回与回滚

- 修订：建立新稳定 ID，将旧项列为 predecessor，并说明事实差异。
- 替代：旧项改为 `SUPERSEDED_SNAPSHOT`，旧项 `superseded_by` 与新项 `supersedes` 必须互为引用。
- 撤回：保留旧记录和证据，将状态改为 `WITHDRAWN_SNAPSHOT`、outcome 改为 `WITHDRAWN`，首页必须明示撤回。
- 回滚：只回退 registry 记录和其确定性投影；不得借快照回滚去改写候选载荷或历史。

测试套件用三条内存实例演示完整修订、替代和撤回链，不向正式 registry 注入虚构项目成果。

## 6. Agent 任务结束接口

形成真实阶段成果的 Agent 可以在最终回执中附 `stage snapshot request`。接口 schema 是 `schemas/operations/stage-snapshot-request.schema.json`，模板是 `templates/operations/stage-snapshot-request-template.json`。请求包含成果对象、来源 HEAD、证据入口、状态、claim ceiling、主页摘要、限制、未完成项、预注册责任／发布 `actor_ref`、非责任性的执行 Agent／自动化记录，以及 `PUBLISH / REVISE / WITHDRAW / DO_NOT_PUBLISH` 建议。Agent 不得在请求中临时创建、改名或覆盖责任主体。

`agent_claims_published_to_main` 永远必须为 false。Agent 提交请求不等于发布；只有独立轻量同步任务核验远端真值、公开边界和生成结果后，才能提出把快照记录合并进 Main。

## 7. 兼容、迁移与退出

1.3.0 的能力生命周期、typed propagation 与增量执行保持历史兼容。没有快照记录的旧任务仍合法；只有希望进入展示层的真实阶段成果才使用新接口。独立部署阅读面已经退役，当前展示义务由仓库 Markdown 与人类可见性 CI 承担。

若 1.4.0 候选被拒绝，删除新 schema、registry、validator、投影和 workflow 步骤即可回到 1.3.0；不需要回滚任何候选能力，因为本制度从未把候选载荷注册或激活为正式能力。
