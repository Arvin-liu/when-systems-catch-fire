# 085: Architecture Structure Freeze Report

## 状态

`ARCHITECTURE_STRUCTURE_FROZEN_CLAIM_TRUTH_PROVISIONAL`

## 冻结内容

以下架构结构组件已冻结为 v1：

1. **正式对象类型系统** — strong_assertion_type 和 claim_type 的允许值
2. **七轴状态系统** — semantic / logic / formal / proof / evidence / scope / provenance
3. **强断言门控** — 每种强标签的门控要求
4. **来源/溯源/锚点/哈希 契约** — 每条记录的必需溯源字段
5. **Legacy overlay、迁移和回滚规则** — 084 原始保留，085 overlay 叠加
6. **Adjudication record schema** — 必需字段清单
7. **Proof artifact 与 evidence obligation 接口** — 输入/输出/要求
8. **验证器、CI、计数真值与失败门** — 检查项和失败条件
9. **分层记账规则** — GLM review / rule-based gate / machine proof / external evidence / cross-model acceptance
10. **禁止的记账行为** — 6 条禁止规则

## 不冻结内容

- 353 条具体命题的真值
- 351 条经验命题的真实性
- 任何尚无可重放 artifact 的定理
- 任何尚无外部证据的因果、严格同构或精确跨域结论
- 强标签的最终保留/降级（可被后续工作更新）

## 冻结文件清单

| 文件 | 类型 |
|------|------|
| `docs/foundation/architecture-structure-freeze-v1.md` | 人类可读冻结文档 |
| `data/foundation/architecture-structure-freeze-v1.json` | 机器可读冻结状态 |
| `data/foundation/project-state-085.json` | 项目权威状态 |

## 084 纠正摘要

| 纠正项 | 084 原始 | 085 纠正 |
|--------|---------|---------|
| 生成机制 | "GLM-5.2 max 独立语义裁决" | DETERMINISTIC_RULE_BASED_HEURISTIC_GATE |
| 双遍审查 | "完整双遍对抗审查" | SINGLE_PIPELINE_GENERATED |
| T4 | DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE | RETAIN_FORMAL_PROPOSITION_UNPROVED |
| P8 计数 | 83 降级 + 112 保留 | 9 降级 + 113 保留 + 1 结构类比 = 122 |
| T18 evidence | EMPIRICAL_EVIDENCE_AVAILABLE | NO_EMPIRICAL_EVIDENCE |
| 架构状态 | TRUTH_FREEZE_CANDIDATE | STRUCTURE_FROZEN_CLAIM_TRUTH_PROVISIONAL |

## 权威计数（从 JSONL 重算）

| 指标 | 值 |
|------|-----|
| 总记录 | 353 |
| PROVED | 0 |
| REFUTED | 0 |
| UNPROVED | 353 |
| Strict isomorphism accepted | 0 |
| Causal identified | 0 |
| External empirical validated | 0 |
| Primary-adversarial consistent | 352 |
| Primary-adversarial inconsistent | 1 |
| Proof obligations | 353 |
| Evidence obligations | 351 |
