# P1 机器数据接入碰撞工作流 · Smoke Test 审计（2026-07-08）

## 输入目录

`inputs/collisions/20260708-smoke-test/`
- `task.md`（P1 接入烟雾测试任务说明）

## 输出目录

`outputs/collisions/20260708-smoke-test/`
- `collision-report.md`
- `new-functions.md`
- `new-cases.md`
- `notes.md`
- `expanded-notes.md`
- `rejected.md`
- `backfill-plan.md`
- `source-snapshot.md`

## 使用了哪些 P1 数据

全部七类（加载并轻量索引）：
- classic_problems_benchmark（34 条）— 无标题命中，验证未命中正常输出
- storytelling_backlog（30 条）— 未做写作方向判定（smoke test）
- pending_claims（34 条）— 未触发 pending（输入非学科声明）
- publication_risk_rules（8 条）— 未触发风险决策
- failure_typology（12 条）— 轻量命中 FAIL-001/003/010 作流程风险提示
- evidence_regimes（12 条）— 确认工程学证据制度范围
- function_dependency（13 条）— 提取 L0 入口组件作挂接参考

## 是否运行校验器

是。`python3 tools/validate_data.py` 输出 `ALL_P1_DATA_VALID`。

## 是否修改两张表

否。`统一函数总表/` 与 `统一案例总表/` 未被读取全量正文，更未被修改。

## 是否产生回填

否。本轮明确「不得新增函数/案例/回填」。backfill-plan.md 写明「本轮无回填」。

## 结论

**流程可运行。**

验证点：
1. 输入目录 + 任务模板可创建并读取；
2. P1 七类数据可加载并做轻量索引；
3. 两张表目录存在性可确认（轻量模式不读全量）；
4. 八类输出文件可按模板生成；
5. 五类输出（新增函数/案例/注释/扩展注释/不采纳）结构正确，且能明确表达「本轮无增量」；
6. 审计记录可生成。

## 下一步建议

- 本 smoke test 通过，流程可运行。
- 下一步：选一个**真实小材料**（如一段具体的学科文本、一个得到笔记片段、或一条新闻）做首个正式碰撞。
- 正式碰撞仍建议从小规模开始：先 P1 预筛 → 再按需深入两张表 → 评估是否小批量回填。
- 不直接上 UNESCO 大规模碰撞，不启动得到笔记大规模任务。
