# AI Prompt Templates

## 冷启动

读取 AI-START-HERE.md、ARCHITECTURE.md、FOUNDATION.md、llms.txt、AI-HANDOFF.md 和 data/foundation/project-state.json。先报告远端、分支、HEAD、任务边界和验证状态，再执行当前命令。保持九状态轴独立，不修改 legacy 正文。

## 审计对象

对目标对象分别报告 source、controlled claim、formal object type、claim type、premises、inference rules、scope、proof obligations、evidence mappings、counterexample records 和九状态轴。缺失字段保持 pending，不生成伪公式。

## 验证强断言

对 THEOREM、AXIOM、ISOMORPHISM、CAUSAL 或 PROVED 逐项检查声明理论、形式命题、映射或 SCM、证明工件、外部证据、适用范围和可重放反例。门禁不通过时降级并保留 legacy wording。
