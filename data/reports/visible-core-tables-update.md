# 可见核心表更新报告 / Visible Core Tables Update Report

生成时间: 2026-06-17 02:56 Asia/Shanghai

## 任务说明

根据用户指令「更新现有可见表」，更新 when-systems-catch-fire 仓库核心可见表。

本操作仅在审核分支进行，不推送 main。

## 数据来源

- 函数表：Arvin-liu/1111 -> 统一函数总表.516版.2026.06.16.14.34.md（515 条）
- 案例表：Arvin-liu/1111 -> 统一案例总表.654版.2026.06.16.14.35.md（654 条）
- 发现投影集合：已有（55 条）
- 预测投影集合：已有（31 条）
- 新答案投影集合：已有（30 条）
- 解析解投影集合：已有（1 条）

## 已更新表

| 文件 | 操作 |
|---|---|
| README.md | 入口表改为当前状态显示（D515 / C-0654 / 投影集合） |
| FUNCTIONS.md | 顶部补充"最近增量 D476-D515（40 条）" |
| CASES.md | 顶部补充"最近增量 C-0595-C-0654（60 个）"；末尾追加 60 条案例 |
| DISCOVERIES.md | 从"待重建"改为"发现投影集合入口" |
| PREDICTIONS.md | 顶部加入投影集合状态 |
| ANSWERS.md | 移除"学术搜索独有性检查"表述，加入投影状态 |
| ANALYTIC_SOLUTIONS.md | 加入投影集合状态，D307/ANS-0010 保留复核 |
| DISCOVERY_PROJECTION_SETS.md | 补充"最近增量来源"节 |
| data/projection-sets/discovery-projection-sets.md | 顶部加入当前状态概览 |

## 增量可见性

- functions_visible: D476-D515（40 条）
- cases_visible: C-0595-C-0654（60 个）

## 统一说明

此集合源于函数表与案例表交叉自举发现。
