# 点火框架投影集合 / Projection Sets

这是一个人类在好奇心的驱动下，借助 AI 做出的发现。

此集合源于函数表与案例表交叉自举发现。它是点火框架内部的结构投影集合，不包含学术新颖性声明，也不包含外部学术检索结论。

This collection is derived from cross-bootstrap findings between the function table and the case table. It is an internal structural projection set of the ignition framework and does not include an academic novelty claim or external scholarly-search conclusion.

---

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

## 投影集合来源说明

此集合源于函数表与案例表交叉自举发现。投影集合不是学术新颖性声明，也不包含外部学术检索结论。外部检索可由读者或后续研究者自行进行。

## 解析解确认

当前确认解析解数量：**1**
- SOL-0001: σ_opt=√e (来自 T20)

## 机器可读数据

- 投影集合: `data/projection-sets/discovery-projection-sets.jsonl`
- 解析解确认报告: `data/projection-sets/analytic-solution-count-report.json`
- 交叉引用表: `data/projection-sets/projection-set-crosswalk.json`

## 人类可读报告

- 投影集合详情: `data/projection-sets/discovery-projection-sets.md`
- 解析解确认详情: `data/projection-sets/analytic-solution-count-report.md`
- 交叉引用详情: `data/projection-sets/projection-set-crosswalk.md`
- 构建报告: `data/reports/build-projection-sets-report.md`

---

## 最近增量来源

本轮投影集合建立在以下已验证增量之上：

| 类型 | 范围 | 数量 | 状态 |
|---|---:|---:|---|
| 函数 | D476-D515 | 40 | 已验证并合入 main |
| 案例 | C-0595-C-0654 | 60 | 已验证并合入 main |

此集合源于函数表与案例表交叉自举发现。

---

*生成时间: 2026-06-17*
