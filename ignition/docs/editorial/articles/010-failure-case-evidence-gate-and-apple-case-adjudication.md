# 失败案例不是缺陷证据：从牛顿苹果叙事到可复现门禁

> 之元方法文章 · 任务 111。本文讨论失败案例如何获得证据资格，不把历史故事升级为科学因果结论。

## 目录名不能替代运行证据

`case_failures/` 目录的原始用途是保存与现实不对齐、冲突或被外部材料推翻的案例。任务 109/110 把其中三个示例统一标成 `IMPLEMENTATION_DEFECT`，并按分数推荐了牛顿苹果案例。这个分类保存了一个值得检查的治理假设，但它没有记录 target commit、精确输入、实际输出、run ID、trace、oracle 或回归测试。

苹果文件的预测写的是“系统可能会输出 `true`”，不是某次执行的观察结果。它的 Outcome 也只是未附来源的叙事。于是，任务 111 不能把文件存在、目录名称或一段可能性描述直接转成“系统已经复现缺陷”。

## 历史来源支持什么

Newton Project 的 Stukeley 文本记录了一个后来的回忆：Newton 把观察苹果落下与想到 gravitation 联系起来；Conduitt 的早期 memoir copy 也保留了相近叙述。Stukeley 自己同时提醒读者，材料混合了亲知与听闻。Newton Project 的时间线还把这则晚出的叙述与之后多年的研究、通信和《Principia》发表分开。

这组材料足以支持一个有边界的 provenance 句子：后来的 memoir sources 报告 Newton 曾把落苹果与 gravitation 的思考联系起来。它不能证明苹果砸中 Newton，也不能证明一个瞬间单独造成了完整理论，更不能反过来证明整则故事必然是虚构。任务 111 因此把历史证据标为 `EVIDENCE_PARTIAL_OR_DISPUTED`，而不是把它当作 Function OS 的真假 oracle。

完整来源、检索时间、摘录和限制见 [`EVIDENCE_DOSSIER.md`](../../../data/operations/iterations/111/historical/EVIDENCE_DOSSIER.md) 与 [`SOURCES.jsonl`](../../../data/operations/iterations/111/historical/SOURCES.jsonl)。

## Function OS 的边界也必须保留

Function OS v0.1/v0.2 是有界的符号函数流水线。N5 可以执行声明的前置条件、表达式和后置条件，N6 可以留下内部 trace，N7 可以检查规格、制品和 trace 的一致性；这些都不能把一个内部 `PASS` 变成历史事实或因果证明。当前仓库没有苹果案例 runner、历史语料 oracle 或 `C(apple_fall, gravitational_theory)` 的可执行接口。

因此本轮没有为了“得到一个结果”而临时发明 target。审计结论是：`EXECUTABLE_TARGET_ABSENT`；关系记号缺少事件时间窗、反事实、因果判据、输入输出语义和外部裁决器，形式化是 `FORMALIZATION_UNDERSPECIFIED`；复现是 `NO_REPRODUCTION_POSSIBLE_WITH_CURRENT_TARGET`。这不是任务阻断，也不是“未来永远不能有 target”的断言。

## 最小门禁

一个未来案例只有在门禁字段齐全时才可以声称 `REPRODUCED_IMPLEMENTATION_DEFECT`：

- 可定位的 repository executable、完整冻结 commit 和与 case ID 的语义绑定；
- 精确输入/规格、实际输出、原始 trace、run ID 和至少两次重复失败；
- 明确的 oracle 或 adjudication basis 与 claim ceiling；
- 保留首次失败的路径、哈希和时间；
- 形式化在运行前冻结，并有可执行的 regression guard。

缺任何一项，门禁只允许叙事、待定义、未复现或 target 缺失状态。对抗固件还会拒绝 LLM 输出冒充 target、错误语义 target、无外部证据、改变形式化、删除首次失败和仅凭目录位置的记录。

## 队列与结论

任务 111 保留 109/110 的原始排名和分数，只在 task-111 投影中叠加证据资格。三个案例仍可被历史检索，但因 target 或证据前置条件未满足，不再以“已知实现缺陷”进入 active queue；C-03 的 task-110 `COMPLETED_PARTIAL` 也从队列排除。下一候选是 `arn-gap-001`，这只是冻结模型下的规划结果，不是任务 112 的创建或授权。

本轮真正建立的是一条可审计的缺陷资格门槛。它提升了记录的可复现性，不提升苹果故事、点火物理、Function OS 的外部真理等级，也不把任何内部测试当作现实因果证据。
