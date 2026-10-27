# Architecture Structure Freeze v1

## 状态

`ARCHITECTURE_STRUCTURE_FROZEN_CLAIM_TRUTH_PROVISIONAL`

## 含义

- **冻结对象**：Schema、状态轴、来源链、门控规则、迁移层、回滚机制、验证器接口、proof/evidence backlog 接口
- **不冻结对象**：未经证明的命题、未经验证的经验结论、严格同构、已识别因果、精确跨域、唯一性、不可能性、必要充分条件

架构结构已冻结，命题真值保持 provisional。

## 1. 正式对象类型系统

允许的对象类型：

| 类型 | 允许值 |
|------|--------|
| strong_assertion_type | mathematical_proof, structural_isomorphism, causal_identification, precise_cross_domain, other_strong |
| claim_type | P1_proof_equivalence, P4_structural_isomorphism, P5_causal, P7_precise_cross_domain, P8_other_strong |

## 2. 七轴状态系统

| 轴 | 允许值 |
|----|--------|
| semantic_status | INTERPRETED, AMBIGUOUS |
| logic_status | WELL_FORMED, UNDER_SPECIFIED |
| formal_status | FORMALIZED_COMPLETE, FORMALIZED_PARTIAL, UNFORMALIZED |
| proof_status | PROVED_WITH_ARTIFACT, REFUTED, UNPROVED, PENDING, NOT_APPLICABLE |
| evidence_status | EMPIRICAL_EVIDENCE_AVAILABLE, NO_EMPIRICAL_EVIDENCE, INTERNAL_REFERENCE_ONLY |
| scope_status | FRAMEWORK_INTERNAL, DOMAIN_SCOPED, UNSCOPED |
| provenance_status | LEGACY_TRACEABLE, LEGACY_PATH_ONLY |

## 3. 强断言门控 (Strong-Claim Gates)

| 强标签 | 门控要求 |
|--------|---------|
| PROVED_ORIGINAL_CLAIM_WITH_ARTIFACT | 必须有可重放 Lean/Z3/SymPy artifact |
| REFUTED_ORIGINAL_CLAIM_WITH_COUNTEREXAMPLE | 必须有构造性反例 |
| RETAIN_SCOPED_DEFINITION (for P4) | 必须同时有双射、两个结构、保持运算、双向验证 |
| RETAIN_PROVISIONAL_MODEL (for P5) | 必须有处理/结果对、时间方向、反事实/混杂因素识别 |
| RETAIN_SCOPED_DEFINITION (for P7) | 必须有单位、数值精度、显式映射 |
| STRICT_ISOMORPHISM | 必须有结构、双射、保持运算、双向验证 |
| CAUSAL_IDENTIFIED | 必须有识别假设和证据 |
| EMPIRICALLY_VALIDATED | 必须有外部来源或实验记录 |

## 4. 来源/溯源/锚点/哈希 契约

每条 adjudication record 必须包含：
- `source_anchor`: 文件路径 + 行号范围 + excerpt_sha256 前 16 位
- `legacy_path`: 原始文件路径
- `source_quote`: 原文摘录（≤ 500 字符）
- `stable_id`: 唯一标识符
- `record_id`: 记录 ID

## 5. Legacy Overlay、迁移和回滚规则

- 084 原始文件保留，不删除、不覆盖
- 085 overlay 与 084 ID 集一致
- 085 overlay 不修改 084 原始记录
- 后续 Agent 通过 overlay 层读取权威状态
- 如需回滚：删除 overlay 文件，回到 084 原始状态

## 6. Adjudication Record Schema

冻结的必需字段：
- stable_id, legacy_path, record_id, batch_id, batch_index
- source_quote, source_anchor, controlled_restatement
- object_type, claim_type, quantifiers, domain
- premises, conclusion, strong_terms
- primary_verdict, primary_reasoning
- adversarial_challenge, adversarial_reasoning
- reconciled_decision, reconciled_reasoning
- primary_adversarial_consistent
- allowed_wording, forbidden_wording
- counterexample_need
- proof_obligation, evidence_obligation
- semantic_status, logic_status, formal_status
- proof_status, evidence_status, scope_status, provenance_status
- source_specific_rationale (≥ 2 项)
- model, reasoning_level, timestamp

## 7. Proof Artifact 与 Evidence Obligation 接口

### Proof Artifact 接口
- 输入：stable_id + formal_statement
- 输出：artifact_type (Lean/Z3/SymPy) + proof_script + type_check_output
- 要求：证明原命题，不允许证明弱化版本

### Evidence Obligation 接口
- 输入：stable_id + empirical_claim
- 输出：source_type (external_paper / experiment / dataset) + source_reference + verification_record
- 要求：外部可独立验证，不接受内部编号引用

## 8. 验证器、CI、计数真值与失败门

### 验证器检查项
1. 084 原始文件仍完整存在
2. 085 overlay 与 084 ID 集一致或明确记录差集
3. 所有汇总总和一致（= 353）
4. T4/P8 已消除矛盾
5. 任何 PROVED 必须有可重放 artifact
6. 任何 EMPIRICALLY_VALIDATED 必须有外部来源
7. 任何 STRICT_ISOMORPHISM 必须有结构、双射、保持运算、双向验证
8. 任何 CAUSAL_IDENTIFIED 必须有识别假设与证据
9. 架构冻结状态必须精确为 `ARCHITECTURE_STRUCTURE_FROZEN_CLAIM_TRUTH_PROVISIONAL`
10. legacy 两张表字节不变
11. 所有旧 PR 仍 OPEN/DRAFT/UNMERGED

### CI 失败门
- 任何 PROVED 记录缺少 artifact → CI FAIL
- 任何 EMPIRICAL_EVIDENCE_AVAILABLE 缺少外部来源 → CI FAIL
- 任何 STRICT_ISOMORPHISM 缺少双射验证 → CI FAIL
- 任何汇总不一致 → CI FAIL

## 9. 分层记账规则

| 层级 | 含义 | 记账方式 |
|------|------|---------|
| GLM review | 模型生成的推理记录 | 标记 model + reasoning_level，不等同证明 |
| Rule-based gate | 确定性规则门控输出 | 标记 DETERMINISTIC_RULE_BASED |
| Machine proof | 机器验证的证明 | 必须有 artifact + type_check |
| External evidence | 外部经验证据 | 必须有外部来源引用 |
| Cross-model acceptance | 跨模型验收 | 必须有不同模型的独立验证记录 |

## 10. 禁止的记账行为

后续 Agent 不得：
- 把覆盖率写成真值接受率
- 把读取率写成完成率
- 把规则门控率写成语义裁决率
- 把 obligation 生成写成 obligation 履行
- 把 internal verification ID 写成 external empirical evidence
- 把 model config 中的 reasoning_level=max 写成逐条 max 推理证据

## 不冻结清单

以下内容在 085 中保持 provisional，不因架构结构冻结而冻结：

1. 353 条具体命题的真值
2. 351 条经验命题的真实性
3. 任何尚无可重放 artifact 的定理
4. 任何尚无外部证据的因果、严格同构或精确跨域结论
5. 强标签的最终保留/降级（可被后续 proof/evidence/cross-model 工作更新）
