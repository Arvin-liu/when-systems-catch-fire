# Canonical Protocol Data Model (022 frozen)

generated_at: 2026-07-10T21:45:00+08:00

本模型冻结 12 个协议统一字段。每个字段定义见 `canonical/data/canonical-field-registry.json`。
状态五层分离：source_status / structure_status / machine_validation_status / semantic_review_status / governance_status。

## 核心派生字段
- content_machine_eligible：机器+半自动硬门槛（G01–G32，G33 除外）全部 PASS/NOT_APPLICABLE。
- ratification_ready：content_machine_eligible 且 semantic_review_status=approved 且 governance_status≠approved。
- formal_protocol：仅治理批准且源仓库完成可追踪更新后成立；本任务不写回。
