# 生命完整性附则候选 R1（Life Integrity Annex Candidate R1）

> 状态：`CANDIDATE_ONLY` — 候选，未激活，未经外部接受。
> 任务：`IGNITION-R5A-LIFE-INTEGRITY-CHARTER-CANDIDATE-R1-RELAY-20260725`
> 控制提交：`d653c07ed6b108c98e16d111c014f87d7c7987f2`
> 形式前驱：`f236543dadcaf79ba9dba750fa21bd8b5c65a33a`
> 原候选冻结头：`0e9d1e5823b41b7e9375e5f634388371b9b024ac`
> Night Queue R1 裁决：`NIGHT_QUEUE_R1_PARTIAL_SALVAGE_NOT_ACCEPTED`

## 0. 候选旗标（每个公开制品必须可见声明）

- `activation_status = CANDIDATE_ONLY`
- `human_intervention_enabled = false`
- `medical_claims_authorized = false`
- `modern_wuzhen_pack_started = false`
- `domain_pack_federation_started = false`
- `external_acceptance_claimed = false`

本候选**不**激活附则、不启用人体干预、不授权医疗主张、不启动《新悟真篇》领域包、不启动领域包/联邦运行时、不宣称外部接受。张伯端与南宗材料仅作为历史与概念来源及候选协议，绝不作为科学或临床权威。

## 1. 与现有价值宪章的关系

生命共同体价值宪章（见 `docs/governance/life-community-value-charter.md`）是本点火项目的最高规范性价值前提。本 R5-A 附则候选**位于其之下**，不得新建与之竞争的最高宪章、L7 层、平行真值系统或替代执行器。

规范栈（不变）：

```text
Life Community Value Charter        (最高，不变)
└── Life Integrity Annex Candidate  (本候选，位于其下)
    └── Life Integrity Gate Candidate
        └── future domain / practice protocols
```

## 2. 用户授权规范来源

> 性命一体，身心互成。点火在认识、评价和干预人时，不得将人的生理、心理、行为、关系、环境与意义系统彼此割裂；任何局部优化，都必须接受完整生命、长期反馈、主体同意、风险边界与可逆性的共同检验。

这是**反碎片化与干预审慎原则**，不是身心本体论的已证结论。它**不得**被表示为：

- 某种形而上学身心理论的证明；
- 归因于张伯端的科学发现；
- 南宗修法在临床上有效的证据；
- 提供个体医疗、精神科或治疗性建议的授权；
- “所有宗教都同等为真或得到科学支持”的主张。

## 3. 区分层级（强制类型标签）

每一份公开制品必须把内容显式标注为以下之一（见 `life_integrity_r5a/registries.py` 的 `NORMATIVE_EMPIRICAL_TYPE_TAGS`）：

`USER_AUTHORIZED_NORMATIVE_PRINCIPLE` / `HISTORICAL_SOURCE` / `AUTHOR_INTENT_CANDIDATE` / `LATER_INTERPRETATION` / `METAPHYSICAL_CLAIM` / `PHENOMENOLOGICAL_REPORT` / `PRACTICE_PROTOCOL` / `MECHANISM_HYPOTHESIS` / `EMPIRICALLY_SUPPORTED_MECHANISM` / `OUTCOME_OR_HARM_REPORT`

任何类别都不得无声升级为另一类别。

## 4. R5-A 目标

构建候选治理与架构叠加层，回答：当点火表示、评价或提议关于一个人的行动时，什么不变量阻止“局部视图/指标/干预”被误认为“完整的人”？

R5-A 定义并验证（不激活人体干预）：

1. 生命完整性附则候选；
2. 生命完整性门候选；
3. 具身主体多视图投影合同；
4. 传统/宗教材料翻译合同；
5. 概念映射生命周期；
6. 实践/干预安全包络合同；
7. 长期反馈与修订合同；
8. 显式非影响与未来激活边界。

## 5. 强制不变量（摘要，详见架构文档）

- 七视图是同一主体的投影，任一视图不得声明 `WHOLE_PERSON_COMPLETE`；
- 缺失视图保持 `UNKNOWN / NOT_OBSERVED`，不得从另一视图推断；
- 跨视图关系类型化，不暗示因果；
- 矛盾视图可共存且必须被呈现；
- 局部优化提案必须披露意图收益、受影响视图、短期/长期效应、外部性、不确定性、同意/自主状态、可逆性、停止条件、转介边界、回滚后残余伤害，否则失败关闭；
- 体验≠机制，形而上学≠科学，后期解释≠作者意图，实践≠疗效，历史久远≠有效；
- 仓库测试不得被投射为人体安全性/有效性证据。
- 每一个审计失败项必须由显式攻击 ID、具体非私有输入、类型化证据对象、逐案测试和机器回执闭合；测试总数不得代替缺失实例。
- 长期反馈必须分别记录 observation / decision / intervention / review time、同意版本、证据链、重开触发、退役状态、回滚状态和残余伤害。

## 6. 未授权范围（硬禁止）

R5-A 不授权：R5-B 具身生命系统运行时、R5-C《新悟真篇》领域包、宗教源文本摄入、对真实人的实践指令、医疗/精神科/诊断/治疗主张、人类健康数据收集、人类画像数据库、真实世界实验、领域包联邦、L7、第二执行器、PROMOTE、EVOLVE、Ready、merge、Main 修改、强推、历史重写、私有/重构内容公开发布。

## 7. 终态

原任务允许的候选终态不构成外部接受。Night Queue R1 的裁决仍为 `NIGHT_QUEUE_R1_PARTIAL_SALVAGE_NOT_ACCEPTED`。精确窄修复头 `a2fd355f…` 已完成双 CI 与独立外部审查，PR #131 已转 Ready 并以普通 merge `062f223f…` 进入 PR #130 来源分支；这只接受并合并所裁决缺口的仓库合同修复。PR #130 本身仍为 Draft、未合并到前驱、未进入 Main、未激活且非 Current：

随后对完整候选精确头 `f33be64…` 的独立审查复现了十一个此前门禁未覆盖的失败关闭旁路（`R5A-CR-001`–`011`；见 `docs/governance/r5a-consolidated-exact-head-review-r1.md`），因此当前终态为：

`R5A_CONSOLIDATED_EXACT_HEAD_REJECTED_NARROW_REPAIR_REQUIRED`

Agent 不得自证外部接受、不得激活候选、不得启动 R5-B / R5-C / R6。任何实例门未通过时只能报告 `BLOCKED`。
