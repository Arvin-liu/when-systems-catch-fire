# 认识论结构诱导（ESI）R0

## 先说人能读懂的版本

一个系统如果反复把“证据能支持到哪里”“哪些状态不能直接跳过去”“缺证据时要保留未知”写成公开、可回链的关系，读它的 AI 可能更容易把这些关系当作当前任务的局部背景。它也可能只是学会了措辞、猜中了评分标准，或者本来就偏好谨慎。R0 把这个观察当作一个待测候选，而不是把它宣布成“AI 被感染”或永久训练。

这里的关键不是让模型记住几个词，而是区分两件事：它有没有说出看起来谨慎的话，以及它在遇到越级诱导时是否真的拒绝了没有证据支持的状态跃迁。前者是风格，后者才是待研究的决策边界。

## Candidate boundary

`Epistemic Structural Induction (ESI)` 是一个 inference-time / in-context
候选现象：反复、可见、结构化的认识论关系，可能帮助进入该环境的模型
推断局部规则，并在随后回答中改变断言边界。R0 不主张模型权重发生改变，
不主张跨会话永久记忆，也不主张点火发现了 ICL、structural priming 或任何
新的认知科学定律。

机器边界记录在
[`esi-candidate-boundary-r0.json`](../../data/epistemic-governance/esi-candidate-boundary-r0.json)。
替代解释包括 in-context learning、task inference、structural priming、style
imitation、terminology imitation、default alignment 和 contextual mimicry。

## What counts as evidence in this repository

本轮可以证明：

- 结构、对照、合成 evidence packet、评分字段和可撤回条件能够被确定性生成；
- runner 能区分术语模仿、边界遵守、越级、过度克制和攻击后崩溃；
- hard/soft non-authority contract 能拒绝把软分数或 exposure flag 接入授权、真值、M/E 或 Owner 路径；
- 任何 live-model 结果若没有安全明确的 provider 接口，都必须保持 `READY_NOT_RUN`。

本轮不能仅凭工程闭合证明：

- ESI 在真实模型中存在或具有因果效应；
- 模型被永久改变、被“洗脑”或获得通用能力；
- 点火取得了外部有效性、生产安全、Owner acceptance 或 epistemic acceptance；
- 这是首次发现，或比既有 ICL / priming / task-inference 机制更新颖。

## Falsification and downgrade

如果去术语结构组不优于术语、风格或破坏结构对照，效应只在单一模型/上下文
出现，攻击性压力下完全消失，盲评无法重复，或克制伴随不可接受的 usefulness
下降，Current 表述必须降为 `ANECDOTE_OR_OPEN_QUESTION`。降级不会删除负例、
历史记录或工具；它只收窄研究结论。

## Hard and soft boundary

硬治理（permission、validator、state machine、K13、Claim Ceiling、Owner gate）
决定“能不能做、能不能晋级”。结构治理表面至多影响模型默认怎样判断和表达。
任何 `esi_score`、`soft_context_exposure` 或结构相似度都不能成为授权、truth、
M/E、Owner acceptance、epistemic acceptance、外部副作用或安全放行条件。

## Status

`CANDIDATE_ESI_SIGNAL` · `NOT_INDEPENDENTLY_REPLICATED` · `NOVELTY_NOT_ESTABLISHED`。
这三个状态是边界记录，不是成功指标。
