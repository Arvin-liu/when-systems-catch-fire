# 投影集合清理报告 / Projection Sets Only Cleanup Report

> 清理时间: 2026-06-17 02:27

## 指令

停止学术检索，只保留投影集合。

## 执行概要

从当前 main 分支新建审核分支，移除学术检索状态体系，只保留点火投影集合。

## 统一来源说明

```
此集合源于函数表与案例表交叉自举发现。
This collection is derived from cross-bootstrap findings between the function table and the case table.
```

## 已保留文件

- `DISCOVERY_PROJECTION_SETS.md`
- `data/projection-sets/discovery-projection-sets.jsonl`
- `data/projection-sets/discovery-projection-sets.md`
- `data/projection-sets/projection-set-crosswalk.json`
- `data/projection-sets/projection-set-crosswalk.md`
- `data/projection-sets/analytic-solution-count-report.json`
- `data/projection-sets/analytic-solution-count-report.md`

## 已移除文件（移入归档）

以下学术检索文件从 canonical 路径移至 `data/reports/archived/scholarly-search-abandoned-20260617/`：

- `scholarly-search-status.jsonl`
- `scholarly-search-status.md`
- `scholarly-search-pending.jsonl`
- `scholarly-search-batches.json`
- `scholarly-search-batches.md`

## 已更新文件

| 文件 | 变更 |
|------|------|
| `DISCOVERY_PROJECTION_SETS.md` | 移除学术搜索引用，加入统一来源说明 |
| `data/projection-sets/discovery-projection-sets.jsonl` | 移除 academic_novelty/scholarly_search_status/notes 等字段，加入 source_statement |
| `data/projection-sets/discovery-projection-sets.md` | 替换"学术搜索"为"来源说明：交叉自举发现" |
| `data/projection-sets/analytic-solution-count-report.json` | 注释改为"解析解数量是内部条目分类问题" |
| `data/projection-sets/analytic-solution-count-report.md` | 头部加入内部条目分类说明 |
| `README.md` | 移除学术搜索状态引用，加入投影集合来源说明 |

## 未修改文件

- `FUNCTIONS.md`（未修改正文）
- `CASES.md`（未修改正文）

## 禁止语自检结果

无违规。

## 安全确认

- main_push_executed: false
- no_exclusive_claim: true
- no_novelty_passed: true
- no_scholarly_novelty_claim: true
- no_function_body_modified: true
- no_case_body_modified: true
- secrets_detected: false

## 当前审核分支

`review/projection-sets-only-20260617-0227`
