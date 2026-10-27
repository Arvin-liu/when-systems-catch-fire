# P1 数据索引图（2026-07-08）

> 说明每个 P1 JSON 的关键字段、主键、可用于碰撞的字段。配合 `docs/p1-machine-data-collision-workflow-20260708.md` 使用。

## 总览

| 数据集 | 文件 | 条数 | 主键 | 主要碰撞用途 |
|---|---|---|---|---|
| 经典问题基准 | classic_problems_benchmark | 34 | `id` (CP-xxx) | 预筛是否落入经典问题 |
| 故事化 backlog | storytelling_backlog | 30 | `id` (SB-xxx) | 可写作方向 |
| pending 声明 | pending_claims | 34 | `id` (PEND-xxx) | 强制 pending 判断 |
| 发布风险规则 | publication_risk_rules | 8 | `id` (RISK-xxx) | PASS/REVISE/HOLD |
| 失败类型学 | failure_typology | 12 | `id` (FAIL-xxx) | 失败类型标记 |
| 证据制度 | evidence_regimes | 12 | `id` (EVID-xxx) | 证据/claim level 约束 |
| 函数依赖 | function_dependency | 13 | `id` (FUNC-xxx) | 新增函数挂接层级 |

## 各数据集字段

### classic_problems_benchmark
- 主键：`id`
- 可用于碰撞：`title`（匹配对象名）、`domain`、`claim_level_max`（最高可声明层级）、`pending_required`、`related_failure_types`、`related_evidence_regime`
- 输出映射：→ 输出模板「相关经典问题」

### storytelling_backlog
- 主键：`id`
- 可用于碰撞：`title`、`priority`、`recommended_form`、`main_risk`、`related_cp_ids`
- 输出映射：→ 输出模板「可写作方向」

### pending_claims
- 主键：`id`
- 可用于碰撞：`domain`、`claim`（对象名匹配）、`allowed_level`、`forbidden_wording`、`recommended_wording`、`default_decision`
- 输出映射：→ 输出模板「不采纳项 / pending 标注」

### publication_risk_rules
- 主键：`id`
- 可用于碰撞：`category`、`trigger`（触发条件文本匹配）、`required_action`、`decision`（PASS/REVISE/HOLD）、`related_failure_type`
- 输出映射：→ 输出模板「风险提示 / 不采纳项」

### failure_typology
- 主键：`id`
- 可用于碰撞：`name`、`description`、`symptom`（症状匹配）、`correction`、`related_risk_rules`
- 输出映射：→ 输出模板「风险与 failure typology」

### evidence_regimes
- 主键：`id`
- 可用于碰撞：`domain`、`valid_claim_types`、`max_claim_level_without_external_evidence`、`pending_conditions`、`forbidden_claims`
- 输出映射：→ 输出模板「证据制度约束」

### function_dependency
- 主键：`id`
- 可用于碰撞：`name`、`layer`、`role`、`depends_on`（上游）、`used_by`（下游）
- 输出映射：→ 新增函数候选的「函数层级 / 关联函数」建议

## 跨数据集关联键

- `related_cp_ids`：连接 pending_claims / storytelling_backlog → classic_problems_benchmark
- `related_failure_type` / `related_failure_types`：连接 publication_risk_rules ↔ failure_typology
- `related_pend_ids`：连接多个数据集 → pending_claims
- `related_evidence_regime`：连接 classic_problems_benchmark → evidence_regimes
- `domain`：跨 pending_claims / evidence_regimes 的学科桥接键

## 碰撞接入顺序建议

1. 输入概念拆解 → 用 `title`/`claim`/`domain` 在 classic_problems_benchmark、pending_claims 做名称/领域匹配。
2. 命中的 `related_*` 字段 → 顺着关联键拉出 failure_typology、evidence_regimes、publication_risk_rules。
3. 用 evidence_regimes 的 `max_claim_level_without_external_evidence` 约束输出 claim level。
4. 用 failure_typology 的 `symptom` 检查碰撞过程是否出现对应失败模式。
5. 新增函数候选用 function_dependency 的 `layer` / `depends_on` 决定挂接位置。
