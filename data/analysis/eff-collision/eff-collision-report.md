# EFF/Q 推论 vs normalized-jsonl 碰撞分析报告

- 输入基线 commit / Input baseline commit: `fbb8a54`
- 分析运行 commit / Analysis run commit: `9184eb4`
- This is a collision analysis, not a final classification.
- This is an inference, not a conclusion.
- Migration must be performed in a separate task.
- Active status requires academic search and dual-channel bootstrap verification.
- 本轮不执行迁移、不删除、不晋级 active。

## 输入 / Inputs

- effect-leads analyzed: 36
- functions compared: 713
- cases compared: 710
- effects compared: 36
- discoveries compared: 83
- answers compared: 12
- analytic solutions compared: 1

## 输出摘要 / Output Summary

- function_candidates: 4
- effect_candidates: 31
- discovery_candidates: 1
- answer_candidates: 0
- analytic_solution_candidates: 0
- supplement_note_candidates: 0
- needs_human_review: 0
- near_duplicates: 13

## Likely Function Candidates

- `EFF-0011` → `function_candidate` (medium)
- `EFF-0012` → `function_candidate` (medium)
- `EFF-0015` → `function_candidate` (medium)
- `EFF-0024` → `function_candidate` (medium)

## Likely Effect Candidates

- `EFF-0001` → `effect_candidate` (high)
- `EFF-0002` → `effect_candidate` (high)
- `EFF-0003` → `effect_candidate` (high)
- `EFF-0004` → `effect_candidate` (high)
- `EFF-0005` → `effect_candidate` (high)
- `EFF-0006` → `effect_candidate` (high)
- `EFF-0007` → `effect_candidate` (high)
- `EFF-0008` → `effect_candidate` (high)
- `EFF-0009` → `effect_candidate` (high)
- `EFF-0010` → `effect_candidate` (high)
- `EFF-0013` → `effect_candidate` (high)
- `EFF-0014` → `effect_candidate` (high)
- `EFF-0016` → `effect_candidate` (high)
- `EFF-0017` → `effect_candidate` (high)
- `EFF-0018` → `effect_candidate` (high)
- `EFF-0019` → `effect_candidate` (high)
- `EFF-0020` → `effect_candidate` (high)
- `EFF-0021` → `effect_candidate` (medium)
- `EFF-0022` → `effect_candidate` (high)
- `EFF-0023` → `effect_candidate` (medium)
- `EFF-0025` → `effect_candidate` (high)
- `EFF-0026` → `effect_candidate` (high)
- `EFF-0027` → `effect_candidate` (high)
- `EFF-0028` → `effect_candidate` (medium)
- `EFF-0029` → `effect_candidate` (medium)
- `EFF-0030` → `effect_candidate` (medium)
- `EFF-0031` → `effect_candidate` (high)
- `EFF-0032` → `effect_candidate` (high)
- `EFF-0034` → `effect_candidate` (high)
- `EFF-0035` → `effect_candidate` (high)
- `EFF-0036` → `effect_candidate` (high)

## Likely Discovery / Answer / Analytic Solution Candidates

- `EFF-0033` → `discovery_candidate` (high)

## 与已有函数高度重合 / High Function Overlap

- None

## 与已有案例的推论映射 / Case-Side Inference Mappings

- None

## EFF 内部重复或近似重复 / Internal Similarity Groups

- `EFF-0001` ↔ `EFF-0003` `same_mechanism_different_name` score=0.519
- `EFF-0001` ↔ `EFF-0009` `same_mechanism_different_name` score=0.5
- `EFF-0001` ↔ `EFF-0013` `same_mechanism_different_name` score=0.5115
- `EFF-0001` ↔ `EFF-0021` `same_mechanism_different_name` score=0.5023
- `EFF-0001` ↔ `EFF-0027` `same_mechanism_different_name` score=0.5023
- `EFF-0002` ↔ `EFF-0009` `parent_child_relation` score=0.4887
- `EFF-0003` ↔ `EFF-0021` `same_mechanism_different_name` score=0.5
- `EFF-0006` ↔ `EFF-0009` `same_mechanism_different_name` score=0.5294
- `EFF-0006` ↔ `EFF-0025` `same_mechanism_different_name` score=0.5
- `EFF-0007` ↔ `EFF-0020` `same_mechanism_different_name` score=0.5087
- `EFF-0011` ↔ `EFF-0024` `same_mechanism_different_name` score=0.5062
- `EFF-0017` ↔ `EFF-0018` `same_mechanism_different_name` score=0.525
- `EFF-0025` ↔ `EFF-0034` `same_mechanism_different_name` score=0.567

## Needs Human Review

- None

## 不执行迁移声明 / No-Migration Statement

- migration_executed: false
- academic_search_executed: false
- novelty_passed_generated: false
- active_promotion_executed: false
- full_bootstrap_executed: false
- 所有建议均为 inference_not_conclusion=true。

## 下一步建议 / Next Steps

- 另开迁移任务处理 `function_candidate`、`discovery_candidate` 或需要合并的对象。
- 迁移前先人工复核高相似函数、案例映射和内部重复组。
- 任何进入 active 的对象必须先通过学术搜索与正反自举验证。
