# 点火投影集合审核修正报告

> 生成时间: 2026-06-17 00:59:49
> 审核分支: `review/build-projection-sets-20260616-2350`

---

## 修正摘要

本轮修正了上一轮投影集合构建中的两个审核阻塞问题：

### 问题1：批量学术搜索状态

**发现**: 上一轮将104个函数统一标注为"学术搜索暂未检索到"，但报告同时写明"web_search全覆盖不现实"。实际检查发现每行都有查询记录，但查询仅为"函数名+ignition framework"模式匹配，非真实学术搜索（缺乏英文文献、数学公式、核心变量检索）。

**修正**:
1. 将原 `scholarly-search-status.jsonl` 的104行全部移至 `scholarly-search-pending.jsonl`
2. 正式文件清空后重新填充——仅保留已执行真实搜索的函数
3. 已执行 T20 和 D307 的真实学术搜索（各3组query，覆盖多个学术来源）
4. 建立7批搜索计划（每批15个，按优先级排序）

### 问题2：解析解报告人工复核矛盾

**发现**: 原报告同时写 `needs_human_review=false` 和 "需人工判断"，存在轻微矛盾。

**修正**:
- 采用方案B：`needs_human_review=true`
- `ambiguous_candidates = ["D307", "ANS-0010"]`

---

## 学术搜索状态

| 指标 | 数值 |
|------|------|
| 投影函数总数 | 104 |
| 已实际学术搜索 | **2** |
| 学术搜索已找到 | 0 |
| 学术搜索暂未检索到 | 2 (T20, D307) |
| 待搜索 | 102 (7批计划) |
| 覆盖率完成 | false |

## 解析解

| 项目 | 数值 |
|------|------|
| 解析解数 | 1 (SOL-0001) |
| 需要人工复核 | true |
| 待复核候选 | D307, ANS-0010 |

## 安全校验

| 项目 | 状态 |
|------|------|
| main未推送 | ✅ |
| 未用排他性声明 | ✅ |
| FUNCTIONS.md未修改 | ✅ |
| CASES.md未修改 | ✅ |
| 敏感信息检查 | ✅ 通过 |

## 输出文件

| 文件 | 用途 |
|------|------|
| `data/projection-sets/scholarly-search-status.jsonl` | 正式学术搜索状态（2条，已真实搜索） |
| `data/projection-sets/scholarly-search-pending.jsonl` | 待搜索函数（102条） |
| `data/projection-sets/scholarly-search-batches.json` | 批次计划（7批） |
| `data/projection-sets/scholarly-search-batches.md` | 批次计划可读版 |
| `data/projection-sets/analytic-solution-count-report.json` | 解析解报告（已修正） |
| `data/projection-sets/analytic-solution-count-report.md` | 解析解报告可读版 |
| `data/reports/build-projection-sets-report.json` | 构建报告（已修正） |
| `data/reports/build-projection-sets-report.md` | 构建报告可读版 |
| `data/reports/projection-set-audit-fix-report.json` | 本报告 |
| `data/reports/projection-set-audit-fix-report.md` | 本报告可读版 |

## 下一步

1. 将此修正报告发给ChatGPT复审
2. 继续执行SSB-001~SSB-007的逐条学术搜索
3. 完成全量搜索后更新coverage_complete=true
