# Blind evaluator rubric R0

## Frozen scoring sources

Score each response against the complete frozen Task225 R0.1 target criteria and the Task227 transfer scoring contract. The source bytes are fixed:

- Task225 criteria: `ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1/evaluator/criteria.md`, SHA-256 `9cc185aaf688cd2649a321c80051b8cc69e78a0b93edb3deac5cea3abd86cbcf`.
- Task225 target schema: `.../evaluator/schema.json`, SHA-256 `5be015a0568a830ed753ff8ef65a3909d0cfb99dff03f9ed39cb48719850ef6d`.
- Task227 transfer rubric: `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/transfer/evaluator-criteria.md`, SHA-256 `880ce3bc42d4bf122babbbd349f8b4a4360f8e238e1338c72765efbe114e3874`.
- Task227 transfer evaluator schema: `.../transfer/evaluator-schema.json`, SHA-256 `665fbee30e02a8761044cd94bfd2a9528aae16fefa5bafaed604efbcc54b3eac`.

The Task225 evaluator criteria file is not copied, edited, paraphrased, or relaxed in this preregistration. The evaluators receive the original frozen criteria and cases only after the opening gate passes.

## Scoring instructions

For each opaque response packet, score the case's complete outcome using the exact frozen criteria. Return one boolean success value for that case and a short criterion reference, using `blind-evaluation-schema.json`. Do not infer missing values or actions. Do not infer a condition, lineage, policy, session order, or sibling relationship. Do not use any external source or tool.

Each evaluator independently scores all 54 case packets (18 sessions × A/B/C). Packet order and response IDs differ between evaluators. A missing or invalid score is recorded false for that evaluator and target. Preserve the raw score sheet. Do not discuss or reconcile scores; no third evaluator is authorized.
