# P1 机器数据接入碰撞工作流（设计稿 2026-07-08）

> 本文档定义「P1 机器数据接入碰撞工作流」的管线设计、目录约定、模板与执行步骤。
> 本步只做管线设计 + 说明 + 最小模板，**不大规模跑 UNESCO、不跑得到笔记、不改两张表、不生成新增函数/案例**。

## 1. 工作流定位

P1 机器数据接入碰撞工作流的作用是**辅助**碰撞，而不是替代或自动结论：

- **不是替代两张表**：碰撞主源仍是 `统一函数总表/` 与 `统一案例总表/`。
- **不是自动生成最终结论**：P1 数据只提供索引、提醒、约束与分流信号。
- **是辅助碰撞检索、风险控制、证据约束和输出分流**：见第 2 节七类数据用途。
- **得到大脑默认读不了网页链接**：输入必须优先是本地正文、MD、DOCX、JSON、CSV，而不是 GitHub URL。

## 2. 七类 P1 数据的用途

> 数据位置：`data/`（json + csv 成对），schema 在 `data/schemas/`。校验：`python3 tools/validate_data.py`。

### 2.1 classic_problems_benchmark（34 条，CP-001~）
- 提供经典问题对照基准。
- 判断当前碰撞对象是否落入已有经典问题。
- 辅助生成输出中的「相关经典问题」小节（命中 `id` + `title`）。
- 关键字段：`id`、`title`、`domain`、`claim_level_max`、`pending_required`、`related_failure_types`、`related_evidence_regime`。

### 2.2 storytelling_backlog（30 条，SB-001~）
- 判断碰撞对象是否适合转成文章、案例、解释型输出。
- 辅助输出「可写作方向」。
- 关键字段：`id`、`priority`、`title`、`recommended_form`、`main_risk`、`related_cp_ids`。

### 2.3 pending_claims（34 条，PEND-001~）
- 检查哪些结论必须 `pending`，防止把证据不足的内容写成确定结论。
- 关键字段：`id`、`domain`、`claim`、`allowed_level`、`forbidden_wording`、`recommended_wording`、`default_decision`（多为 pending）。

### 2.4 publication_risk_rules（8 条，RISK-001~）
- 判断哪些表述需要 `PASS` / `REVISE` / `HOLD`。
- 辅助生成「不采纳项」和「风险提示」。
- 关键字段：`id`、`category`、`trigger`、`required_action`、`decision`、`related_failure_type`。

### 2.5 failure_typology（12 条，FAIL-001~）
- 标记可能的失败类型：过度类比、证据不足、层级误置、概念漂移等。
- 关键字段：`id`、`name`、`description`、`symptom`、`correction`、`related_risk_rules`。

### 2.6 evidence_regimes（12 条，EVID-001~）
- 按学科/领域约束证据标准，防止把低证据材料写成高层级结论。
- 关键字段：`id`、`domain`、`valid_claim_types`、`max_claim_level_without_external_evidence`、`pending_conditions`、`forbidden_claims`。

### 2.7 function_dependency（13 条，FUNC-L0~）
- 提示函数之间的依赖关系。
- 判断新增函数候选应挂到哪个上游函数、函数族、层级。
- 关键字段：`id`、`name`、`layer`、`role`、`depends_on`、`used_by`。

## 3. 标准输入

输入目录模板：

```
inputs/collisions/YYYYMMDD-task-name/
```

允许内容：

- `source.md` / `source.txt` / `source.docx`
- `source.json` / `source.csv`
- `task.md`（任务说明，可用 `templates/collision/task-template.md`）

**如果输入是网页链接，必须先转存为：**

```
outputs/sources/YYYYMMDD-task-name/source.md
```

不得只给 URL。

## 4. 标准输出

输出目录：

```
outputs/collisions/YYYYMMDD-task-name/
```

每次至少输出：

- `collision-report.md`
- `new-functions.md`
- `new-cases.md`
- `notes.md`
- `expanded-notes.md`
- `rejected.md`
- `backfill-plan.md`（用 `templates/collision/backfill-plan-template.md`）
- `source-snapshot.md`

## 5. 碰撞流程（12 步）

1. 读取任务说明（`task.md` 或输入模板）。
2. 确认输入材料是否完整（本地正文存在，非仅 URL）。
3. 运行 `python3 tools/validate_data.py`，确认 `ALL_P1_DATA_VALID`。
4. 加载 P1 七类数据（见第 2 节）。
5. 读取最新函数表（`统一函数总表/`）。
6. 读取最新案例表（`统一案例总表/`）。
7. 对输入材料做概念拆解。
8. 用 `classic_problems_benchmark` / `failure_typology` 做预筛（命中经典问题、标记失败类型）。
9. 用 `evidence_regimes` / `publication_risk_rules` 做证据约束（claim level、PASS/REVISE/HOLD）。
10. 与函数表和案例表碰撞（找同构、缺口、可合并项）。
11. 生成五类输出（见第 6 节）。
12. 生成回填建议与保存文件（见第 4、9 节）。

## 6. 输出五分类

固定为：新增函数 / 新增案例 / 新增注释 / 扩展注释 / 不采纳项。字段沿用 `docs/getbrain-operation-guide-20260708.md` 第 6 节。

## 7. 得到大脑使用方式

给得到大脑任务时，**不要只说「看 GitHub 仓库」**。必须把以下内容贴给它或打包给它：

- 当前任务（用 `task-template.md`）
- 输入正文（本地文件或贴文）
- P1 数据说明（本文件第 2 节摘要）
- 两张表路径（`统一函数总表/`、`统一案例总表/`）
- 输出目录（`outputs/collisions/YYYYMMDD-task-name/`）
- 保存规则（第 4 节）
- 不得做的事（第 11 节）

## 8. 最小试运行建议（本轮只写建议，不执行）

先不跑大任务。建议用一个很小的测试输入：

```
inputs/collisions/20260708-smoke-test/task.md
```

内容：

```
任务名称：P1 接入烟雾测试
碰撞对象：一个新案例是否应该进入函数表或案例表
输入材料：一段 300 字以内的本地文本
使用函数范围：全量
使用案例范围：全量
是否使用 P1 机器数据：是
输出要求：只测试流程，不回填正式两张表
不得做的事：不得修改正式两张表，不得生成大规模报告
保存位置：outputs/collisions/20260708-smoke-test/
```

**本轮不执行 smoke test**，仅完成管线设计。下一步再跑。

## 9. 回填两张表的规则（引用）

遵从 `docs/getbrain-operation-guide-20260708.md` 第 9 节：不直接覆盖正式表、先生成候选、查重、只回填增量、保留来源、生成审计、编号检查、不确定进 pending。

## 10. 禁止事项（本工作流）

- 不修改 `统一函数总表/`
- 不修改 `统一案例总表/`
- 不修改 `data/`
- 不修改 `data/schemas/`
- 不修改 `tools/validate_data.py`
- 不跑 UNESCO
- 不跑得到笔记
- 不删除 rescue 分支
- 不删除临时仓库
- 不创建 release
- 不打新 tag

## 11. 配套模板

- `templates/collision/task-template.md`
- `templates/collision/output-template.md`
- `templates/collision/backfill-plan-template.md`

## 12. 下一步

完成管线设计后，下一步执行 `inputs/collisions/20260708-smoke-test/` 的小规模烟雾测试，验证 P1 数据接入流程是否跑通，**不回填正式两张表**。
