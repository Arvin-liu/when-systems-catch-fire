# 版本说明：2026-07-09 元协议生成层版本

## 摘要
点火项目本体从「元函数判定框架」升级为「元协议生成框架」。这是版本升级，不是小修小补。

## 为什么发生版本升级
第二步元协议生成层维护（commit `974b121e`）已落地 12 元协议、64 组合、22 候选的数据/文档/模板/校验器，但项目入口与整体说明仍停留在旧口径。用户要求把使用说明、项目本体说明、整体入口、Agent 说明等全部做版本升级。

## 新增结构
- `README.md` 整体升级（架构总览、快速入口、边界、红线）。
- `SUMMARY.md`、`llms.txt` 新建（人类/AI 双入口）。
- `docs/PROJECT-ARCHITECTURE.md`、`USAGE.md`、`AGENT-GUIDE.md`、`GET-BRAIN-WORKFLOW.md`、`VERSIONING.md` 新建。
- `docs/versions/2026-07-09-meta-protocol-generation-layer.md` 新建。
- `CHANGELOG.md` 追加 2026-07-09 条目。
- `outputs/audit/project-body-version-upgrade-audit-20260709.md` 新建。

## 未改动内容
- Ψ₀ 数学定义未改写；Ψ₀ 保留为判定与收敛框架。
- 统一函数总表（617）/ 统一案例总表（804）未改；INDEX 与正文均未动。
- `data/functions/`、`data/cases/`、`data/rebuild/` 未改。
- 22 本书候选未入表；12 元协议未计入函数总数。

## 红线
- 不删除/替换/改写 Ψ₀；不改两张表；不给候选分配 C 编号；不把元协议计入函数总数；不声称外部证明；不经验穷尽；不删 pending；不直接合并 main；不强推。

## 后续任务（待 GPT 指令）
1. 是否合并 `version/meta-protocols-20260709` 到 main。
2. 是否逐本复核 22 候选并分配 C 编号入表。
3. 是否将 12 元协议正式写入第 0 层函数表。
4. 是否更新 DOCX 两张表索引。
5. 是否通知得到大脑新版本口径。
