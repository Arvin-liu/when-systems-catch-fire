# AI HANDOFF

## 当前版本

2026-07-12 数学与逻辑双地基七层架构版本（IGNITION-20260709-076）。

## 权威链

- 架构：ARCHITECTURE.md
- 双地基：FOUNDATION.md
- 类型与状态：data/foundation/
- 机器计数：data/foundation/project-state.json 与 migration-summary.json
- 任务边界：1111 中对应的 IGNITION command、progress 与 result

## 兼容链

统一函数总表和统一案例总表保留为 legacy source / compatibility view。不得删除、重编号、不可逆覆盖或独立生长。views/ 是从新 registry 生成的兼容视图。

## 交接规则

新 Agent 必须重新核验远端、分支、HEAD、开放 PR 和验证结果，不得把聊天记忆当权威。统计必须写出去重键、范围、单位和生成脚本。缺字段、缺来源、不可形式化、反模型和真实 counterexample 分别记录。

当前架构状态只能是 ARCHITECTURE_COMPLETE_PENDING_CONTENT_PROOFS；不得改写成全量数学证明完成。
