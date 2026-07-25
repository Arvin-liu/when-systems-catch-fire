# 传统/宗教材料翻译管线 R5-A R1（Tradition Translation Pipeline R1）

> 候选。把进入点火的传统/宗教材料分类、标注 provenance、并失败关闭地阻止无声类别升级。

## 1. 封闭 claim-class 注册表（恰好 8 类）

- `HISTORICAL_SOURCE`
- `NORMATIVE_CLAIM`
- `METAPHYSICAL_CLAIM`
- `PHENOMENOLOGICAL_REPORT`
- `PRACTICE_PROTOCOL`
- `MECHANISM_HYPOTHESIS`
- `RITUAL_SOCIAL_TECHNOLOGY`
- `OUTCOME_OR_HARM_REPORT`

## 2. 每条翻译 claim 必须携带

来源 provenance、源语言/翻译状态、说话者/作者/归属状态、claim class、字面文本引用或非公开摘要引用、解释层、证据等级、机制状态、适用边界、权利边界、置信度与 UNKNOWNs、禁止升级、修订历史。

## 3. 失败关闭的禁止升级（无独立证据与审查不得跨越）

- `PHENOMENOLOGICAL_REPORT -> EMPIRICALLY_SUPPORTED_MECHANISM`
- `METAPHYSICAL_CLAIM -> SCIENTIFIC_FACT`
- `PRACTICE_PROTOCOL -> CLINICAL_EFFICACY`
- `LATER_INTERPRETATION -> AUTHOR_INTENT`
- `HISTORICAL_LONGEVITY -> EFFECTIVENESS`

## 4. 边界

- 体验有效，仅作为“体验的报告”，不自动成为机制；
- 传统解释不自动成为经验机制；
- 机制假设不等于临床疗效；
- 个体改善不等于普遍有效性；
- 传统的重复、古老或声望不构成独立佐证；
- 不得在无证据时把科学语言 retrofitted 到传统术语。

## 5. 历史解释边界

原典、作者意图候选、后世注疏与现代重构必须分别版本化；现代解释不得覆盖原典记录；作者意图证据缺失保持 `UNKNOWN`；“古人已发现现代科学”的映射在无显式标准证明前失败关闭。
