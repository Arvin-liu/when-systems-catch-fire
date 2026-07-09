# Agent 执行指南（AI / Agent）

> 当前版本：2026-07-09 元协议生成层版本。Agent 执行任何点火维护任务前必读。

## 1. 执行任务前必须读
- `README.md`（架构总览、快速入口、红线）
- `docs/AGENT-GUIDE.md`（本文）
- `docs/PROJECT-ARCHITECTURE.md`
- `docs/VERSIONING.md`
- 任务对应的 `1111/agent-commands/IGNITION-*.md` 指令文件
- `llms.txt`（机器可读入口）
- 相关 `docs/meta-protocols/` 与 `data/meta-protocols/`

## 2. 区分正式表与候选文件
- 正式：`统一函数总表/`、`统一案例总表/`、`data/functions/`、`data/cases/`、`data/rebuild/`。**非显式任务不得改。**
- 候选：`outputs/book-collisions/`、`docs/meta-protocols/book-validation-22-cases-20260709.md`、`data/meta-protocols/book-validation-cases-20260709.json`。

## 3. 如何使用 1111 作中转仓库
- 读取指令：`Arvin-liu/1111/agent-commands/IGNITION-*.md`
- 写回结果：`Arvin-liu/1111/agent-results/IGNITION-*-result.md`
- 本地 1111 clone 若 SSH 不通或工作树脏，用 `gh api` / GitHub Contents API，不要折腾本地 clone。

## 4. 如何写审计
每次维护在 `outputs/audit/` 写审计：输入来源、新增/修改/未修改文件清单、是否改 Ψ₀、是否改两张表、校验结果、git diff --stat、commit hash、PR 链接、pending 清单。

## 5. 如何处理 Get 笔记 / 得到大脑输出
得到大脑输出是候选材料，不是结论。须经 `1111` 中转、主仓库审核、补齐字段、标 pending 后才可能入表。禁止直接把得到大脑原文写成正式结论。

## 6. 如何验证数据
提交前必跑：
```bash
python3 tools/validate_meta_protocols.py   # 期望 ALL_META_PROTOCOL_DATA_VALID
python3 tools/validate_data.py             # 期望 ALL_P1_DATA_VALID
```
git diff 中不得出现 `统一函数总表/`、`统一案例总表/`、`data/functions/`、`data/cases/`、`data/rebuild/`，否则停止，不提交。

## 7. 禁止事项
- 删除/替换/改写 Ψ₀ 数学定义。
- 修改正式两张表。
- 给 22 本书候选分配 C 编号。
- 把 12 元协议计入函数总数。
- 声称点火已外部证明科学/数学定理。
- 直接合并 main 或强推。

## 8. 完成后如何汇报
按指令文件的汇报格式；多数 IGNITION 指令要求只回短句（如「IGNITION-xxxx 已执行完成，请 GPT 查证」），并把详细结果写入 1111 结果文件。
