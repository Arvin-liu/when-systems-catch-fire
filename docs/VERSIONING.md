# 版本说明（VERSIONING）

## 点火项目版本阶段
- **v0.1**：早期函数/案例积累期（历史）。
- **v0.2**：结构层升级与机器可读化期（历史阶段，见 README「v0.2 路线图（历史阶段）」）。
- **2026-07-09 元协议生成层版本（当前）**：项目本体从「元函数判定框架」升级为「元协议生成框架」。新增 12 元协议生成层、64 组合理论空间、22 本书候选暂存；Ψ₀ 保留；两张表未改。

## 什么算版本升级
版本升级 = 项目本体形态变化 + 全量文档/导航/入口刷新 + 红线制度化。例如本次：第 0 层形成双结构、新增生成层、README/SUMMARY/llms.txt/架构/使用/Agent/得到大脑/版本说明统一升级。

## 什么只是候选增量
候选增量 = 向候选层追加材料（如新的书籍碰撞、新的学科碰撞），不改变正式架构与两张表。例如 22 本书候选暂存。

## 版本升级时必须更新哪些文件
- `README.md`（架构总览、快速入口、边界、红线）
- `SUMMARY.md`、`llms.txt`
- `docs/PROJECT-ARCHITECTURE.md`、`docs/USAGE.md`、`docs/AGENT-GUIDE.md`、`docs/GET-BRAIN-WORKFLOW.md`、`docs/VERSIONING.md`
- `docs/versions/YYYY-MM-DD-*.md`
- `CHANGELOG.md`
- 相关 `docs/meta-protocols/`、`outputs/audit/`

## 审计要求
每次版本升级须在 `outputs/audit/` 写审计，核对：是否改 Ψ₀、是否改两张表、是否改 data/functions|cases|rebuild、12/64/22 校验、git diff --stat、commit hash、PR 链接、pending 清单。
