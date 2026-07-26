# 阶段成果持续快照与分层发布制度

Status: `Ignition Iteration Method 1.4.0 Candidate — Continuous Stage Snapshot Publication`。

本制度是对 Current 方法 `1.3.0` 的候选增量。它尚未 Accepted、Current 或 Activated，不得利用自身规则快速合并；本候选必须继续经过独立 exact-head 验收、普通合并和 post-merge 同步。

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
- 记录执行者、发布者和负责组织，禁止把责任自动推给创始人或上游项目；
- 保留前驱、后继、替代、撤回、修订与回滚路径；
- 保证主页文字由 registry 确定性生成；
- 保证失败实例逐案阻断，不能用测试总数或绿色 CI 掩盖。

在线远端验证使用：

```bash
python3 tools/operations/validate_stage_snapshots.py --check --verify-remotes
```

CI 的仓库内门使用确定性 schema、语义和投影检查；独立验收者还必须在线重新获取 PR 身份、HEAD 与 Actions，不能只采信记录时间的 attestation。

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

形成真实阶段成果的 Agent 可以在最终回执中附 `stage snapshot request`。接口 schema 是 `schemas/operations/stage-snapshot-request.schema.json`，模板是 `templates/operations/stage-snapshot-request-template.json`。请求包含成果对象、来源 HEAD、证据入口、状态、claim ceiling、主页摘要、限制、未完成项、责任主体与 `PUBLISH / REVISE / WITHDRAW / DO_NOT_PUBLISH` 建议。

`agent_claims_published_to_main` 永远必须为 false。Agent 提交请求不等于发布；只有独立轻量同步任务核验远端真值、公开边界和生成结果后，才能提出把快照记录合并进 Main。

## 7. 兼容、迁移与退出

1.3.0 的能力生命周期、typed propagation、增量执行和生产 Pages 门保持原样。没有快照记录的旧任务仍合法；只有希望进入展示层的真实阶段成果才使用新接口。

若 1.4.0 候选被拒绝，删除新 schema、registry、validator、投影和 workflow 步骤即可回到 1.3.0；不需要回滚任何候选能力，因为本制度从未把候选载荷注册或激活为正式能力。
