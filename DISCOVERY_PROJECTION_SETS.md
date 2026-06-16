# 点火类发现投影集合 / Projection Sets

这是一个人类在好奇心的驱动下，借助 AI 做出的发现。

本文件定义了从统一函数总表（FUNCTIONS.md）中投影出来的四类函数子集：

1. **发现投影集合 (Discovery Projection Set)** — 具有框架新解释或新机制的函数
2. **预测投影集合 (Prediction Projection Set)** — 构成可检验推论的函数
3. **新答案投影集合 (New Answer Projection Set)** — 构成新答案理论基础的函数
4. **解析解投影集合 (Analytic Solution Projection Set)** — 具有明确闭式解析解的函数

一个函数可以出现在多个投影集合中。

---

## 统计概览

| 投影集合 | 函数数量 |
|---------|---------|
| 发现投影集合 | 55 |
| 预测投影集合 | 31 |
| 新答案投影集合 | 30 |
| 解析解投影集合 | 1 |
| **去重总计** | **104** |

## 学术搜索状态

所有类发现函数已标注学术搜索状态。目前全部标记为"学术搜索暂未检索到"（scholarly_search_not_found_yet）。

> 这是一次有限范围的学术搜索结果，不构成排他性原创声明。

## 解析解确认

当前确认解析解数量：**1**
- SOL-0001: σ_opt=√e (来自 T20)

## 机器可读数据

- 投影集合: `data/projection-sets/discovery-projection-sets.jsonl`
- 学术搜索状态: `data/projection-sets/scholarly-search-status.jsonl`
- 解析解确认报告: `data/projection-sets/analytic-solution-count-report.json`
- 交叉引用表: `data/projection-sets/projection-set-crosswalk.json`

## 人类可读报告

- 投影集合详情: `data/projection-sets/discovery-projection-sets.md`
- 学术搜索详情: `data/projection-sets/scholarly-search-status.md`
- 解析解确认详情: `data/projection-sets/analytic-solution-count-report.md`
- 交叉引用详情: `data/projection-sets/projection-set-crosswalk.md`
- 构建报告: `data/reports/build-projection-sets-report.md`

---

*生成时间: 2026-06-16*
