# 只保留投影集合清理 — 合入 main

## 摘要

- **任务**: `projection_sets_only_main_merge`
- **决策**: 停止学术检索，只保留投影集合
- **状态**: ✅ 已合入 main

## 版本信息

| 字段 | 值 |
|--------|-------|
| main_before | `529eff7eb59f2420b12c225b9c329069c99c5578` |
| main_after | `be1fc8f867d01f776368f788adc1a8c6dab2ac94` |
| review_branch | `review/projection-sets-only-20260617-0227` |
| review_branch_head | `53df8e45b30ffd48b319559cd45277c67084820f` |
| force_push_used | false |

## 保留的文件

- `DISCOVERY_PROJECTION_SETS.md` — 投影集合入口
- `data/projection-sets/discovery-projection-sets.jsonl`
- `data/projection-sets/discovery-projection-sets.md`
- `data/projection-sets/projection-set-crosswalk.json`
- `data/projection-sets/projection-set-crosswalk.md`
- `data/projection-sets/analytic-solution-count-report.json`
- `data/projection-sets/analytic-solution-count-report.md`
- `data/reports/projection-sets-only-cleanup-report.json`
- `data/reports/projection-sets-only-cleanup-report.md`

## 已归档（不删除，移入 abandoned 目录）

- `data/reports/archived/scholarly-search-abandoned-20260617/scholarly-search-status.jsonl`
- `data/reports/archived/scholarly-search-abandoned-20260617/scholarly-search-status.md`
- `data/reports/archived/scholarly-search-abandoned-20260617/scholarly-search-pending.jsonl`
- `data/reports/archived/scholarly-search-abandoned-20260617/scholarly-search-batches.json`
- `data/reports/archived/scholarly-search-abandoned-20260617/scholarly-search-batches.md`

## Canonical 状态

| 检查项 | 状态 |
|--------|--------|
| 投影集合已保留 | ✅ |
| scholarly-search-status 已移除 | ✅ |
| scholarly-search-pending 已移除 | ✅ |
| scholarly-search-batches 已移除 | ✅ |
| coverage_complete_field 已移除 | ✅ |

## 安全

| 检查项 | 状态 |
|--------|--------|
| 无独家声明 | ✅ |
| 无 novelty_passed | ✅ |
| 无学术新颖性声明 | ✅ |
| 函数正文未修改 | ✅ |
| 案例正文未修改 | ✅ |
| 未检测到 secrets | ✅ |
| 禁止语未出现 | ✅ |

## 统一说明

> 此集合源于函数表与案例表交叉自举发现。

## 合并前校验

- ✅ 分支 HEAD 确认: `53df8e45b30ffd48b319559cd45277c67084820f`
- ✅ 必备文件完整性检查
- ✅ 无 canonical 学术检索文件
- ✅ 交叉自举说明存在于入口文件中
- ✅ 禁止语检查通过
- ✅ 函数/案例正文未修改
- ✅ 清理报告 JSON 校验通过
- ✅ 核心验证脚本通过 (validate_project_positioning_lock, validate_project_evaluation_output_lock, validate_no_function_case_entailment, validate_no_hardcoded_counts)
- ✅ 工作区无未提交变更（仅 data/rebuild/ 下 pre-existing 未跟踪文件）
