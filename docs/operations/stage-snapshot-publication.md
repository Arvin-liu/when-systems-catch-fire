# 阶段成果持续快照与分层发布制度

Status: `Ignition Iteration Method 1.4.0 Candidate — Continuous Stage Snapshot Publication`。

本制度是对 Current 方法 `1.3.0` 的候选增量。它尚未 Accepted、Current 或 Activated，不得利用自身规则快速合并；本候选必须继续经过独立 exact-head 验收、普通合并和 post-merge 同步。

责任主体窄修复状态：PR #134 的精确头 `5a856c031616ec0a959150baebb7edced34f22bc` 因 A15c/A15d 可把 Agent 或自动发布流程伪装成负责组织而被拒绝。当前修复只加固责任字段、validator、实例门与直接投影；PR #134 仍为 Draft，方法 1.4.0 仍为 Candidate。

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

1. `schemas/operations/stage-snapshot-registry.schema.json` 定义开放接口；
2. `data/operations/stage-snapshots.json` 是阶段快照唯一仓库权威；
3. `tools/operations/stage_snapshot_contract.py` 做 schema、语义、隐私、责任、关系、远端 identity/HEAD 和投影检查；
4. README 标记块和 `docs/generated/recent-stage-results.md` 由同一 renderer 生成；Pages 首页继续从 README 构建；
5. PR body 与 1111 回执保存 exact-final-HEAD、GitHub Actions run ID 和外部审查结论。

README 或 Pages 不能成为第二份人工状态源。`--check` 重新渲染并逐字比较；registry 变化但首页未同步时失败。

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

`responsible_actor` 与 `publisher_actor`（请求接口中为 `proposed_publisher_actor`）只能是：

- `PERSON`：具体、可识别的人类责任主体，必须给出姓名、`person:` 稳定 ID、明确角色、责任依据和可追溯联系人入口；
- `ORGANIZATION`：现实中可识别且能承担治理或发布责任的组织，必须给出组织名、`org:` 稳定 ID、明确角色、责任依据和负责人／治理入口。

自由文本旧字段 `responsible_person`、`responsible_organization`、`executor` 与 `publisher` 不再属于开放接口，因 `additionalProperties=false` 而失败关闭。`execution_agents` 与 `automation_workflows` 只记录技术执行和因果链节点：Agent、模型、机器人、算法、工作流、CI、脚本、软件、平台或系统可以出现在这里，但不得出现在两个最终责任字段中。大小写、空格、连字符、下划线、复数与常见缩写先归一化再检查；占位符、未知值和“维护者／管理员／有关人员”等泛称也不能取得责任资格。

每条 registry 记录还必须有独立 `responsibility_record`。责任主体变化时，必须建立新的 snapshot revision，以新的责任记录 ID 显式指向前驱责任记录；validator 拒绝静默覆盖。该合同是有限的仓库发布问责门，不是完整因果与责任宪章，也不作法律责任判断。

稳定逐案门由 `tests/stage_snapshot_responsibility_actor_cases.json` 定义，`tools/operations/run_stage_snapshot_responsibility_cases.py` 输出每个 ID 的 schema/runtime 结果。A15c、A15d 和每个同族变体必须逐案为 REJECT；明确责任个人与具体责任组织必须逐案为 ACCEPT。测试总数或绿色 CI 不能代替这些记录。

## 4. 显示语义

- “项目现状”说明 Current 正式能力；“正在炼化”说明 PR 可见候选和阶段成果。
- `REJECTED`、`FAILURE`、`WITHDRAWN` 必须在摘要中直接显示拒绝、失败或撤回。
- `SUPERSEDED_SNAPSHOT` 必须指向后继；历史快照不抹除原始证据。

当前首个真实试点是 R5-A。它只说明两轮具体合同修复已独立验收并进入 PR #130 来源分支；PR #130 整体仍为 OPEN/DRAFT，非 Main、非 Current、非 Activated，R5-B、R5-C、R6 未启动。它不证明 R5-A 已完成、生命完整性、人体安全、疗效或普遍语义能力。

本候选分支上的试点状态是 `PR_VISIBLE`，`snapshot_record_merged_to_main=false`。独立验收和合并后，另一次受控同步才可将它更新为 `PUBLISHED_SNAPSHOT`；本任务不预写未来事实。

## 5. 修订、替代、撤回与回滚

- 修订：建立新稳定 ID，将旧项列为 predecessor，并说明事实差异。
- 替代：旧项改为 `SUPERSEDED_SNAPSHOT`，旧项 `superseded_by` 与新项 `supersedes` 必须互为引用。
- 撤回：保留旧记录和证据，将状态改为 `WITHDRAWN_SNAPSHOT`、outcome 改为 `WITHDRAWN`，首页必须明示撤回。
- 回滚：只回退 registry 记录和其确定性投影；不得借快照回滚去改写候选载荷或历史。

测试套件用三条内存实例演示完整修订、替代和撤回链，不向正式 registry 注入虚构项目成果。

## 6. Agent 任务结束接口

形成真实阶段成果的 Agent 可以在最终回执中附 `stage snapshot request`。接口 schema 是 `schemas/operations/stage-snapshot-request.schema.json`，模板是 `templates/operations/stage-snapshot-request-template.json`。请求包含成果对象、来源 HEAD、证据入口、状态、claim ceiling、主页摘要、限制、未完成项、结构化责任／发布主体、非责任性的执行 Agent／自动化记录，以及 `PUBLISH / REVISE / WITHDRAW / DO_NOT_PUBLISH` 建议。

`agent_claims_published_to_main` 永远必须为 false。Agent 提交请求不等于发布；只有独立轻量同步任务核验远端真值、公开边界和生成结果后，才能提出把快照记录合并进 Main。

## 7. 兼容、迁移与退出

1.3.0 的能力生命周期、typed propagation、增量执行和生产 Pages 门保持原样。没有快照记录的旧任务仍合法；只有希望进入展示层的真实阶段成果才使用新接口。

若 1.4.0 候选被拒绝，删除新 schema、registry、validator、投影和 workflow 步骤即可回到 1.3.0；不需要回滚任何候选能力，因为本制度从未把候选载荷注册或激活为正式能力。
