# P1 机器可读数据完整性审计

## 审计时间

2026-07-07

## 审计对象

本报告审计 P1 机器可读化阶段的全部产物，包括：

- 机器可读化数据结构规范；
- 抽取可行性审计；
- JSON Schema；
- JSON / CSV 数据文件；
- 数据校验器；
- README / CHANGELOG / docs 入口状态。

## 审计边界

本次审计只检查 P1 机器可读化数据完整性，不新增理论，不新增函数，不新增案例，不继续 v0.3。

## P1 阶段产物

| 阶段 | 产物 | 状态 |
|---|---|---|
| P1-0 | `docs/machine_readable_data_plan.md` | 通过 |
| P1-1 | `outputs/audit/p1-extraction-feasibility-audit-20260707.md` | 通过 |
| P1-2 | `data/schemas/*.schema.json` | 通过 |
| P1-3 | CP / SB JSON + CSV | 通过 |
| P1-4 | pending / risk / failure JSON + CSV | 通过 |
| P1-5 | evidence / function dependency JSON + CSV | 通过 |
| P1-6 | `tools/validate_data.py` | 通过 |
| P1-7 | 本审计报告 | 通过 |

## 数据文件统计

| 数据集 | JSON 行数 | CSV 行数 | 首个 ID | 末个 ID | 预期 |
|---|---:|---:|---|---|---:|
| classic_problems_benchmark | 34 | 34 | CP-001 | CP-034 | 34 |
| storytelling_backlog | 30 | 30 | SB-001 | SB-030 | 30 |
| pending_claims | 34 | 34 | PEND-001 | PEND-034 | 34 |
| publication_risk_rules | 8 | 8 | RISK-001 | RISK-008 | 8 |
| failure_typology | 12 | 12 | FAIL-001 | FAIL-012 | 12 |
| evidence_regimes | 12 | 12 | EVID-001 | EVID-012 | 12 |
| function_dependency | 13 | 13 | FUNC-L0-C | FUNC-L1-FAILURE | 13 |

## Schema 文件统计

| Schema | 状态 |
|---|---|
| `data/schemas/classic_problems_benchmark.schema.json` | 通过 |
| `data/schemas/storytelling_backlog.schema.json` | 通过 |
| `data/schemas/pending_claims.schema.json` | 通过 |
| `data/schemas/publication_risk_rules.schema.json` | 通过 |
| `data/schemas/failure_typology.schema.json` | 通过 |
| `data/schemas/evidence_regimes.schema.json` | 通过 |
| `data/schemas/function_dependency.schema.json` | 通过 |

## 校验器结果

运行：

```bash
python3 tools/validate_data.py
```

结果：

```txt
ALL_P1_DATA_VALID
```

## 已确认检查项

- JSON 文件均可解析；
- CSV 文件均可解析；
- JSON / CSV 行数一致；
- JSON / CSV id 顺序一致；
- CP 编号范围为 `CP-001` 至 `CP-034`；
- SB 编号范围为 `SB-001` 至 `SB-030`；
- PEND 编号范围为 `PEND-001` 至 `PEND-034`；
- RISK 编号范围为 `RISK-001` 至 `RISK-008`；
- FAIL 编号范围为 `FAIL-001` 至 `FAIL-012`;
- EVID 数据不少于 12 条；
- FUNC 数据不少于 13 条；
- schema 必填字段检查通过；
- 基础交叉引用检查通过；
- 本地 Markdown 链接检查通过。

## P1-6 修复记录

P1-6 中，校验器发现 P1-5 遗留的一个悬空引用：

```txt
FUNC-L0-GDELTA.used_by -> FUNC-L1-PENDING
```

处理方式：

- 删除该悬空引用；
- 不新增 `FUNC-L1-PENDING` 节点；
- 不新增函数族；
- 保持 function dependency 数据为 13 条；
- 修复后 `tools/validate_data.py` 通过。

该修复属于 P1 数据自洽性最小修复。

## 未做事项

本次审计未做以下事项：

- 未修改函数表；
- 未修改案例表；
- 未修改 getbrain 原始输出正文；
- 未新增理论；
- 未新增函数；
- 未新增案例；
- 未继续 v0.3；
- 未打 tag；
- 未创建 release。

## 结论

P1 机器可读化阶段已完成。

当前仓库已经具备：

1. 机器可读化数据规划；
2. 抽取可行性审计；
3. JSON Schema；
4. 七类机器可读数据集；
5. JSON / CSV 双格式输出；
6. 统一数据校验器；
7. 数据完整性审计报告。

下一步建议进入可选封版任务：

- 检查 README / docs 对 P1 的入口是否足够清晰；
- 打 `v0.2-p1-machine-readable-data` tag；
- 不创建 release，除非人类维护者明确要求。
