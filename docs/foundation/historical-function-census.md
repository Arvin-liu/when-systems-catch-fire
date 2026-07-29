# 历史函数资产全量登记

任务 98 对 formal main 的全部 Git 跟踪文本源执行了确定性扫描。扫描范围包含函数与案例表、Foundation、theory kernels、投影矩阵、元函数、执行器、README/SUMMARY/USAGE、代码以及 JSON/YAML/CSV/Markdown 中的显式编号和隐式命名资产。

本页的计数由 `data/foundation/function-assets/census-summary.json` 生成；如与机器文件不一致，以同一提交中的机器文件和校验器为准。

## 快照结果

- 扫描文本文件：2,875
- 已注册 formal objects：622
- 发现但未定义的显式编号：139
- 无显式编号的命名候选：1,272
- 稳定 ID 去重后资产：2,033
- 按“资产 × 来源文件”合并后的发现记录：25,112
- 原始显式提及总数：59,191
- 去重提及：57,158
- 已声明依赖边：1,923
- 具有依赖的资产：541
- 本轮人工权威深审：12
- 待后续人工深审：2,021

这些数字不是“2,033 个真实函数”。它们是审计总体：包括严格对象、规则、关系、模型、隐喻、待证命题、伪函数、未定义引用和隐式候选。

## 数据产品

| 文件 | 作用 |
|---|---|
| `discovery.jsonl` | 每个稳定 ID 在每个来源文件中的定义/引用位置和提及数 |
| `census.jsonl` | 去重后的资产记录、候选身份、双轴、十门状态和来源证据 |
| `dependencies.jsonl` | 方向明确的 `consumer -> dependency` 边 |
| `audit-queue.jsonl` | 可恢复的风险队列和稳定 resume key |
| `corrections.jsonl` | 本轮 12 条人工权威纠偏覆盖 |
| `claim-ledger.jsonl` | 活跃、撤回和禁止回弹的断言状态 |
| `census-summary.json` | 可复算计数与最高反向依赖摘要 |

## 去重和权威边界

显式编号按稳定 ID 去重；隐式候选按“来源路径 + 归一化标题文本”的 SHA-256 前缀赋予稳定 ID。同一资产在不同页面出现时保留所有来源，不重复创建权威对象。引用不冒充定义；历史源、别名和冲突保留在来源证据中。

扫描器不做领域真值判定。自动身份、M/E 等级和门状态仅用于排队，不能覆盖 `corrections.jsonl` 或既有 Foundation 人工审定。
