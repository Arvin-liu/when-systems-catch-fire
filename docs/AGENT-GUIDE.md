# Agent 执行指南

> 当前版本：2026-07-12 数学与逻辑双地基七层架构版本（IGNITION-20260709-076）。

## 1. 执行前阅读顺序

1. README.md
2. docs/project-current-state.md
3. ARCHITECTURE.md
3. FOUNDATION.md
4. llms.txt 与本文
5. 任务对应的 1111/agent-commands/IGNITION-*.md
6. data/foundation/registry-manifest.json 与 project-state.json
7. 任务涉及的 schema、来源和历史材料

只有任务实际涉及元协议时，才继续读取相关 docs/meta-protocols/ 和 data/meta-protocols/。

## 2. 区分权威、兼容源与候选

- 状态权威：data/foundation/ 下的 formal-objects、claims、arguments、sources、evidence、mappings、proofs、validations、migrations，以及 task-100 `nonfunction-claims/` 中的十三门、证据谱系、依赖、处置与公开上限。
- 函数类资产还必须读取 `data/foundation/function-assets/identity-cards.jsonl`、义务、依赖和 quarantine；自动 census 只负责发现，registry closure 不代表数学或外部真实性完成。
- Legacy source / compatibility view：统一函数总表、统一案例总表和 views。保留旧 ID 与正文，不可删除、重编号、不可逆覆盖或独立生长。
- 候选：book collisions、candidate_only、pending 和未完成形式化的材料。候选不得冒充权威、证明或正式案例。

## 3. 使用 1111 中转

- 从 Arvin-liu/1111 的 agent-commands 读取原始指令。
- 持续写入匹配任务 ID 的 progress，完整结果写入 result。
- 通过任务分支和 Draft PR 中转；除非命令明确授权，不合并、关闭或改 Ready。
- 路径、远端、分支和 HEAD 必须在冷启动时重新核验。

## 4. 审计要求

每次审计记录输入来源、去重键、统计范围、生成脚本、修改与未修改文件、九状态轴、强术语门禁、counterexample 重放记录、验证结果、diff、commit、PR 和 blocker。

文件数、索引行数、对象数、案例数、问题命中、字段错误和真实反例必须分开。汇总数字不能推出真值。

## 5. Get 笔记边界

Get 笔记可作为只读来源与同步渠道，不是数学推理、逻辑审定、函数改写或架构决策工具。其输出默认是候选材料，必须经过来源、类型、论证、证据和状态审查。

## 6. 提交前验证

~~~bash
python3 tools/foundation/migrate_legacy.py --check
python3 tools/foundation/validate_foundation.py --strict
python3 tools/foundation/run_benchmarks.py --check
python3 -m unittest discover -s tests/foundation -p "test_*.py"
python3 tools/validate_meta_protocols.py
python3 tools/validate_data.py
~~~

检查 diff，确认 legacy 正文没有人工或不可逆覆盖，生成的 registry/view 与脚本一致，且没有凭据写入。

## 7. 强制边界

- Ψ₀ 在新架构中是 workflow orchestrator / algorithm protocol；旧乘积式只作 legacy source。
- J+ / J- 只作内部审议通道。
- THEOREM、AXIOM、ISOMORPHISM、CAUSAL、PROVED 必须过门禁。
- converged 或 workflow closed 不代表数学真、逻辑有效或经验真实。
- 未定义、缺来源、缺字段和关键词命中都不是 counterexample。
- 不给 book candidate 分配 C ID，不新增或删除函数/案例，不自动合并 PR。

## 8. 完成汇报

报告必须引用 project-state、migration-summary、验证输出和 unresolved obligations。聊天窗口按任务规定保持简短，详细证据留在仓库。
