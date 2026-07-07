# 机器可读化数据结构规范

本文定义点火项目 P1 阶段的机器可读化数据结构。

它只规定“哪些内容应被抽取成结构化数据、每个数据集有哪些字段、字段从哪里来、如何校验”，不直接生成 CSV / JSON。

## 1. 阶段定位

v0.2 已经完成结构基础设施和 P0 治理层收口，包括：

- CP 编号索引；
- SB 编号索引；
- 公开前风险检查清单；
- Pending 强结论登记表；
- P0 收口审计。

P1 的目标是把这些 Markdown 文档逐步转化为机器可读数据，使后续 Codex、得到大脑、本地模型和外部脚本可以稳定读取、校验、引用和更新。

P1 不是继续 v0.3。  
P1 不是新增理论。  
P1 不是新增函数或案例。  
P1 是数据结构层。

## 2. P1 数据集总览

P1 规划以下数据集：

| 数据集 | 计划文件 | 来源文档 | 状态 |
|---|---|---|---|
| classic_problems_benchmark | `data/classic_problems_benchmark.json` / `.csv` | `docs/classic_problem_ids.md`、`docs/classic_problems_benchmark.md`、任务 G 原稿 | 待生成 |
| storytelling_backlog | `data/storytelling_backlog.json` / `.csv` | `docs/storytelling_backlog_ids.md`、`docs/storytelling_case_backlog.md`、任务 H 原稿 | 待生成 |
| pending_claims | `data/pending_claims.json` / `.csv` | `docs/pending_claims_register.md` | 待生成 |
| publication_risk_rules | `data/publication_risk_rules.json` / `.csv` | `docs/publication_risk_checklist.md` | 待生成 |
| failure_typology | `data/failure_typology.json` / `.csv` | `docs/failure_typology.md` | 待生成 |
| evidence_regimes | `data/evidence_regimes.json` / `.csv` | `docs/evidence_regime_library.md` | 待生成 |
| function_dependency | `data/function_dependency.json` / `.csv` | `docs/function_dependency_map.md` | 待生成 |

后续可以新增：

| 数据集 | 说明 |
|---|---|
| cross_reference_map | CP / SB / PEND / failure / evidence / function 之间的交叉引用 |
| public_release_checks | 对外材料的 PASS / REVISE / HOLD 检查记录 |
| getbrain_outputs_index | `outputs/getbrain/` 的机器可读索引 |

## 3. 目录规划

P1 完成后建议形成以下目录：

```txt
data/
  classic_problems_benchmark.json
  classic_problems_benchmark.csv
  storytelling_backlog.json
  storytelling_backlog.csv
  pending_claims.json
  pending_claims.csv
  publication_risk_rules.json
  publication_risk_rules.csv
  failure_typology.json
  failure_typology.csv
  evidence_regimes.json
  evidence_regimes.csv
  function_dependency.json
  function_dependency.csv

data/schemas/
  classic_problems_benchmark.schema.json
  storytelling_backlog.schema.json
  pending_claims.schema.json
  publication_risk_rules.schema.json
  failure_typology.schema.json
  evidence_regimes.schema.json
  function_dependency.schema.json

tools/
  validate_data.py
```

本任务不创建这些文件。  
本任务只创建本文档。

## 4. 全局字段规范

所有 JSON 数据集建议遵守以下通用字段规范。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 稳定编号，如 `CP-001`、`SB-001`、`PEND-001` |
| title | string | 是 | 条目标题 |
| source_files | array[string] | 是 | 来源 Markdown 文件 |
| source_lines | array[string] | 否 | 来源行号或行号范围 |
| status | string | 是 | `active` / `pending` / `deprecated` / `draft` |
| notes | string | 否 | 备注 |
| created_in | string | 是 | 首次出现阶段，如 `v0.2` |
| updated_in | string | 否 | 最近更新阶段 |
| tags | array[string] | 否 | 标签 |

## 5. classic_problems_benchmark 数据结构

### 5.1 目标文件

```txt
data/classic_problems_benchmark.json
data/classic_problems_benchmark.csv
data/schemas/classic_problems_benchmark.schema.json
```

### 5.2 来源文件

```txt
docs/classic_problem_ids.md
docs/classic_problems_benchmark.md
outputs/getbrain/classic-problems-benchmark-draft-20260706.md
outputs/getbrain/classic-problems-benchmark-supplement-20260707.md
```

### 5.3 编号范围

```txt
CP-001 至 CP-034
```

### 5.4 字段设计

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | CP 编号 |
| title | string | 是 | 经典问题标题 |
| source_file | string | 是 | 编号索引记录的来源文件 |
| source_line | integer | 是 | 编号索引记录的来源行号 |
| domain | string | 否 | 学科领域 |
| benchmark_type | string | 否 | 问题类型，如数学、物理、历史、AI、艺术等 |
| claim_level_max | string | 是 | 最高允许断言等级，建议 `L2` / `L3` / `pending` |
| pending_required | boolean | 是 | 是否必须 pending |
| related_pend_ids | array[string] | 否 | 关联 PEND 编号 |
| related_failure_types | array[string] | 否 | 关联失败类型 |
| related_evidence_regime | string | 否 | 关联证据制度 |
| public_safe | boolean | 否 | 是否适合公开展示 |
| notes | string | 否 | 备注 |

### 5.5 校验规则

1. 必须有 34 行；
2. id 必须从 `CP-001` 连续到 `CP-034`；
3. id 不得重复；
4. title 不得为空；
5. source_file 必须存在；
6. source_line 必须为正整数；
7. 如果 pending_required 为 true，则 claim_level_max 不得为 `L4` 或 `L5`；
8. related_pend_ids 如存在，必须能在 `pending_claims` 中找到。

## 6. storytelling_backlog 数据结构

### 6.1 目标文件

```txt
data/storytelling_backlog.json
data/storytelling_backlog.csv
data/schemas/storytelling_backlog.schema.json
```

### 6.2 来源文件

```txt
docs/storytelling_backlog_ids.md
docs/storytelling_case_backlog.md
outputs/getbrain/storytelling-case-backlog-draft-20260707.md
```

### 6.3 编号范围

```txt
SB-001 至 SB-030
```

### 6.4 字段设计

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | SB 编号 |
| priority | string | 是 | 高 / 中 / 暂缓 |
| title | string | 是 | 故事化案例名称 |
| source | string | 否 | 来源 |
| domain | string | 否 | 所属领域 |
| score | integer | 否 | 原始总分 |
| recommended_form | string | 否 | 推荐形式 |
| main_risk | string | 否 | 主要风险 |
| related_cp_ids | array[string] | 否 | 关联 CP 编号 |
| related_pend_ids | array[string] | 否 | 关联 PEND 编号 |
| publish_status | string | 是 | `draft` / `hold` / `ready` |
| notes | string | 否 | 备注 |

### 6.5 校验规则

1. 必须有 30 行；
2. id 必须从 `SB-001` 连续到 `SB-030`；
3. id 不得重复；
4. priority 必须是 `高`、`中`、`暂缓` 之一；
5. title 不得为空；
6. 如果 priority 是 `暂缓`，publish_status 默认应为 `hold`；
7. related_cp_ids 如存在，必须能在 CP 数据集中找到；
8. related_pend_ids 如存在，必须能在 PEND 数据集中找到。

## 7. pending_claims 数据结构

### 7.1 目标文件

```txt
data/pending_claims.json
data/pending_claims.csv
data/schemas/pending_claims.schema.json
```

### 7.2 来源文件

```txt
docs/pending_claims_register.md
```

### 7.3 编号范围

```txt
PEND-001 至 PEND-034
```

### 7.4 字段设计

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | PEND 编号 |
| domain | string | 是 | 领域 |
| claim | string | 是 | 问题 / 强结论 |
| allowed_level | string | 是 | 当前允许等级 |
| forbidden_wording | string | 是 | 禁止写法 |
| recommended_wording | string | 是 | 推荐写法 |
| handling | string | 是 | 后续处理 |
| default_decision | string | 是 | PASS / REVISE / HOLD / pending |
| related_cp_ids | array[string] | 否 | 关联 CP 编号 |
| related_sb_ids | array[string] | 否 | 关联 SB 编号 |
| notes | string | 否 | 备注 |

### 7.5 校验规则

1. 必须有 34 行；
2. id 必须从 `PEND-001` 连续到 `PEND-034`；
3. claim 不得为空；
4. forbidden_wording 不得为空；
5. recommended_wording 不得为空；
6. 医学、法律、金融类 default_decision 应为 `HOLD` 或等价保守状态。

## 8. publication_risk_rules 数据结构

### 8.1 目标文件

```txt
data/publication_risk_rules.json
data/publication_risk_rules.csv
data/schemas/publication_risk_rules.schema.json
```

### 8.2 来源文件

```txt
docs/publication_risk_checklist.md
```

### 8.3 字段设计

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 风险规则编号，如 `RISK-001` |
| category | string | 是 | 规则类别 |
| trigger | string | 是 | 触发条件 |
| required_action | string | 是 | 必须动作 |
| decision | string | 是 | PASS / REVISE / HOLD |
| related_failure_type | string | 否 | 关联失败类型 |
| related_pend_ids | array[string] | 否 | 关联 PEND 编号 |
| notes | string | 否 | 备注 |

### 8.4 校验规则

1. id 不得重复；
2. trigger 不得为空；
3. required_action 不得为空；
4. decision 必须是 PASS / REVISE / HOLD 之一。

## 9. failure_typology 数据结构

### 9.1 目标文件

```txt
data/failure_typology.json
data/failure_typology.csv
data/schemas/failure_typology.schema.json
```

### 9.2 来源文件

```txt
docs/failure_typology.md
```

### 9.3 字段设计

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 失败类型编号，如 `FAIL-001` |
| name | string | 是 | 失败类型名称 |
| description | string | 是 | 描述 |
| symptom | string | 否 | 表现 |
| correction | string | 否 | 修正方式 |
| related_risk_rules | array[string] | 否 | 关联风险规则 |
| related_pend_ids | array[string] | 否 | 关联 PEND 编号 |
| notes | string | 否 | 备注 |

### 9.4 校验规则

1. 至少应覆盖 v0.2 已定义的 12 种失败类型；
2. id 不得重复；
3. name 不得为空；
4. description 不得为空。

## 10. evidence_regimes 数据结构

### 10.1 目标文件

```txt
data/evidence_regimes.json
data/evidence_regimes.csv
data/schemas/evidence_regimes.schema.json
```

### 10.2 来源文件

```txt
docs/evidence_regime_library.md
```

### 10.3 字段设计

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 证据制度编号，如 `EVID-001` |
| domain | string | 是 | 学科 / 领域 |
| valid_claim_types | array[string] | 否 | 可成立的命题类型 |
| evidence_required | array[string] | 是 | 所需证据 |
| max_claim_level_without_external_evidence | string | 是 | 无外部证据时最高允许等级 |
| pending_conditions | array[string] | 否 | 必须 pending 的条件 |
| forbidden_claims | array[string] | 否 | 禁止断言 |
| notes | string | 否 | 备注 |

### 10.4 校验规则

1. 至少应覆盖 v0.2 已定义的 12 个领域；
2. domain 不得为空；
3. evidence_required 不得为空；
4. max_claim_level_without_external_evidence 不得高于 L3。

## 11. function_dependency 数据结构

### 11.1 目标文件

```txt
data/function_dependency.json
data/function_dependency.csv
data/schemas/function_dependency.schema.json
```

### 11.2 来源文件

```txt
docs/function_dependency_map.md
```

### 11.3 字段设计

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 函数或函数组编号 |
| name | string | 是 | 函数或函数组名称 |
| layer | string | 是 | L0-L6 层级 |
| role | string | 否 | 作用 |
| depends_on | array[string] | 否 | 依赖项 |
| used_by | array[string] | 否 | 被哪些函数使用 |
| status | string | 是 | active / review / pending / deprecated |
| notes | string | 否 | 备注 |

### 11.4 校验规则

1. layer 必须是 L0-L6 之一；
2. name 不得为空；
3. status 必须是 active / review / pending / deprecated 之一；
4. 不在 P1 中修改函数表，只从依赖图文档抽取结构。

## 12. 交叉引用规则

后续应逐步建立以下交叉引用：

| 来源 | 目标 | 说明 |
|---|---|---|
| CP | PEND | 某经典问题是否必须 pending |
| CP | evidence_regime | 某经典问题需要哪种证据制度 |
| CP | failure_typology | 某经典问题可能触发哪些失败类型 |
| SB | CP | 某故事化案例对应哪些 benchmark |
| SB | PEND | 某故事化案例是否涉及 pending 强结论 |
| publication_risk_rules | failure_typology | 风险规则对应的失败类型 |
| pending_claims | evidence_regime | pending 的证据制度原因 |
| function_dependency | CP / SB | 哪些函数被用于解释哪些问题或案例 |

P1 初期可以先保留空数组，不强制补齐所有交叉引用。

## 13. P1 执行顺序

建议后续按以下顺序执行：

### P1-1：抽取可行性审计

检查每个 Markdown 源文件是否能稳定抽取字段。  
输出审计报告，不生成数据。

### P1-1 状态

P1-1 抽取可行性审计已完成：

- `outputs/audit/p1-extraction-feasibility-audit-20260707.md`

下一步进入 P1-2：建立 JSON Schema。

### P1-2：建立 JSON Schema

创建：

```txt
data/schemas/*.schema.json
```

只建立 schema，不生成实际数据。

### P1-2 状态

P1-2 JSON Schema 已建立：

- `data/schemas/classic_problems_benchmark.schema.json`
- `data/schemas/storytelling_backlog.schema.json`
- `data/schemas/pending_claims.schema.json`
- `data/schemas/publication_risk_rules.schema.json`
- `data/schemas/failure_typology.schema.json`
- `data/schemas/evidence_regimes.schema.json`
- `data/schemas/function_dependency.schema.json`

下一步进入 P1-3：生成 CP / SB 数据。

### P1-3：生成 CP / SB 数据

创建：

```txt
data/classic_problems_benchmark.json
data/classic_problems_benchmark.csv
data/storytelling_backlog.json
data/storytelling_backlog.csv
```

### P1-4：生成 pending / risk / failure 数据

创建：

```txt
data/pending_claims.json
data/pending_claims.csv
data/publication_risk_rules.json
data/publication_risk_rules.csv
data/failure_typology.json
data/failure_typology.csv
```

### P1-5：生成 evidence / function dependency 数据

创建：

```txt
data/evidence_regimes.json
data/evidence_regimes.csv
data/function_dependency.json
data/function_dependency.csv
```

### P1-6：建立数据校验器

创建：

```txt
tools/validate_data.py
```

校验：

- JSON 是否符合 schema；
- CSV 行数是否与 JSON 一致；
- CP / SB / PEND 编号是否连续；
- 交叉引用是否存在；
- 必填字段是否缺失；
- 断言等级是否越界。

### P1-7：P1 数据完整性审计

创建：

```txt
outputs/audit/p1-machine-readable-data-audit-20260707.md
```

复核所有数据文件、schema 和校验器。

## 表达边界提醒

机器可读化数据不应把项目描述为"野心驱动的大一统理论"。相关公开表达应遵守：

- [动机与边界说明](author_motivation_and_boundary_note.md)
- [公开前风险检查清单](publication_risk_checklist.md)
- [Pending 强结论登记表](pending_claims_register.md)

## 14. P1 边界

P1 不做以下事情：

1. 不新增理论；
2. 不新增函数；
3. 不新增案例；
4. 不继续 v0.3；
5. 不改 getbrain 原始输出正文；
6. 不修改函数表或案例表；
7. 不把机器可读化数据当成最终理论；
8. 不自动发布；
9. 不自动打 tag。

P1 只把 v0.2 / P0 已经稳定的内容结构化。

## 15. 完成标准

P1 完整完成时，应满足：

1. 所有规划数据集都有 JSON；
2. 所有规划数据集都有 CSV；
3. 所有规划数据集都有 JSON Schema；
4. 所有数据可由 `tools/validate_data.py` 校验；
5. README 有机器可读数据入口；
6. `docs/v0.2_summary.md` 有机器可读数据入口；
7. `docs/v0.2_next_tasks.md` 标明 P1 已完成；
8. 有 P1 数据完整性审计报告；
9. 无断链；
10. 工作区干净，远端同步。
