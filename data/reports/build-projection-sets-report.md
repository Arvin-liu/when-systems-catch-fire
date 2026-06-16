# 构建点火类发现投影集合报告 / Build Projection Sets Report

生成时间: 2026-06-16T15:52:26Z

## 模式

- 模式: review_branch_only
- main_push_executed: False

## 投影集合统计

| 投影集合 | 数量 |
|---------|------|
| 发现投影集合 (discovery_projection_set) | 55 |
| 预测投影集合 (prediction_projection_set) | 31 |
| 新答案投影集合 (new_answer_projection_set) | 30 |
| 解析解投影集合 (analytic_solution_projection_set) | 1 |

## 学术搜索状态

- 总检查函数数: 104
- 学术搜索暂未检索到: 104
- 学术搜索已找到: 0
- exclusive_claim_used: False

## 解析解确认

- 确认解析解数: 1
- 当前解析解: SOL-0001 (σ_opt=√e, from T20)
- 需人工复核: False
- 说明: 唯一解析解为 SOL-0001 (T20, σ_opt=√e)。D307 正文提及同一结果但非独立条目；ANS-0010 标题含'解析解'但为 Answer 条目。

## 安全校验

- no_exclusive_claim: True
- no_novelty_passed: True
- no_main_push: True
- no_function_body_modified: True
- no_case_body_modified: True
- secrets_detected: False

## 输出文件

- DISCOVERY_PROJECTION_SETS.md
- data/projection-sets/discovery-projection-sets.jsonl
- data/projection-sets/discovery-projection-sets.md
- data/projection-sets/scholarly-search-status.jsonl
- data/projection-sets/scholarly-search-status.md
- data/projection-sets/analytic-solution-count-report.json
- data/projection-sets/analytic-solution-count-report.md
- data/projection-sets/projection-set-crosswalk.json
- data/projection-sets/projection-set-crosswalk.md
- data/reports/build-projection-sets-report.json
- data/reports/build-projection-sets-report.md
