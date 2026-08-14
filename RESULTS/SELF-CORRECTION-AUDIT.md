# 自我纠错审计

规则是仓库启发式和结构门禁，不是外部真理裁判。`BLOCK` 阻止 CI；`REVIEW` 要求人工核对；受边界说明保护的历史/纠正性提及不作为回弹。

|规则|状态|匹配数|
|---|---|---:|
|`proof_obligation`|`REVIEW`|78|
|`empirical_obligation`|`REVIEW`|15|
|`cross_domain_mapping`|`REVIEW`|71|
|`quantifier_inflation`|`REVIEW`|194|
|`circular_reasoning`|`PASS`|0|
|`analogy_as_isomorphism`|`PASS`|1|
|`model_failure_to_universal_impossibility`|`PASS`|15|
|`conclusion_rebound`|`PASS`|25|
|`hidden_essential_content`|`PASS`|0|
|`retired_pages_surface`|`PASS`|0|

## 整改计划

- 无阻断项；保留 REVIEW 项供精确 Head 人工审查。

## 历史保留

撤回、降级、隔离与修订通过 Git 历史、现行 supersession lineage 和本目录 `history.jsonl` 追加记录保留；生成器不删除历史证据，也不改写 Git 历史。
