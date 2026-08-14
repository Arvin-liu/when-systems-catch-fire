# 085: 084 Truth Status Correction

## 概述

本文件纠正 084 报告中对生成机制和命题真值的不准确描述。所有纠正基于 `084-max-decisions.jsonl` 的机器可读真值重算，不修改 084 原始文件。

## 1. 生成机制纠正

### 084 原始描述
> "353 条 GLM-5.2 max 独立语义裁决"
> "PRIMARY/ADVERSARIAL/RECONCILED 完整率 100%"

### 085 纠正
084 的 353 条记录 **100% 由 `process_084_batch.py` 的确定性规则代码分支生成**，具体机制：

| 生成环节 | 实际机制 | 是否涉及逐条模型推理 |
|----------|----------|---------------------|
| primary_verdict | 按 P1/P4/P5/P7/P8 分支 + 关键词命中 | 否 |
| adversarial_challenge | 关键词检测 scope drift / hidden premise / formalization gap / circularity / testability | 否 |
| reconciled_decision | 固定 downgrade_map 映射 | 否 |
| proof_obligation | 按 priority_label 选取固定模板 | 否 |
| evidence_obligation | 按 priority_label 选取固定模板 | 否 |
| counterexample_need | 按 reconciled_decision 选取固定模板 | 否 |
| allowed/forbidden_wording | 关键词命中 strong_terms | 否 |
| evidence_status | 关键词命中 known_evidence 中的"验证" | 否 |
| reasoning_level: max | 静态字符串，非推理证据 | 否 |
| primary + adversarial | 单函数单次调用内同步生成 | 否 |

**正确口径**：`DETERMINISTIC_RULE_BASED_HEURISTIC_GATE_OUTPUT`

**禁止表述**：
- ~~"353 条已完成最高模型独立裁决"~~
- ~~"353 条已完成真实双遍模型审查"~~
- ~~"架构真值层已经最终冻结"~~
- ~~"353 条命题已终审"~~

**允许表述**：
- "353 条高风险对象已完成规则化保守门控"
- "353 条均已生成 proof obligation；351 条生成 empirical obligation"
- "强标签在缺少 artifact/证据时被默认降级或设为未证明"
- "架构结构冻结候选已准备，命题真值仍为 provisional"

## 2. 模板簇统计

| 字段 | 唯一值数 | 最大簇大小 | 模板化率 |
|------|---------|-----------|---------|
| primary_reasoning | 6 / 353 | 173 (49.0%) | 100% |
| adversarial_reasoning | 3 / 353 | 348 (98.6%) | 100% |
| reconciled_reasoning | 5 / 353 | 184 (52.1%) | 100% |
| proof_obligation | 5 / 353 | 173 (49.0%) | 100% |
| evidence_obligation | 5 / 353 | 173 (49.0%) | 100% |
| counterexample_need | 3 / 353 | 186 (52.7%) | 100% |

所有 353 条记录的 primary_reasoning 均以 `P{1,4,5,7,8} check:` 开头，由固定代码分支决定。

## 3. 双遍审查纠正

084 的 `primary_verdict`、`adversarial_challenge`、`reconciled_decision` 三个字段在 `adjudicate_record()` 函数内同步生成，**不存在两次独立模型调用**。

- `dual_pass_independent_model_calls_exist = false`
- `dual_pass_generated_in_single_rule_pipeline = true`
- self_review 文件由 `build_self_review()` 函数从 decision 直接派生，不构成独立验证

## 4. T4 纠正

| 维度 | 084 报告 | JSONL 真值 | 085 纠正 |
|------|---------|-----------|---------|
| T4 reconciled_decision | DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE | RETAIN_FORMAL_PROPOSITION_UNPROVED | 确认 JSONL 真值 |

084 报告写 T4 被降级为自然语言候选，但实际数据中 T4 保留为未证明形式命题。

## 5. P8 纠正

084 报告写 P8 有 83 条降级、112 条保留，但 P8 总数为 122。83 + 112 = 195 ≠ 122。

### JSONL 真值重算

| P8 子类 | 数量 |
|---------|------|
| RETAIN_SCOPED_DEFINITION | 113 |
| DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE | 8 |
| DOWNGRADE_TO_STRUCTURAL_ANALOGY | 1 |
| **合计** | **122** |

084 报告中的 "83 条降级" 和 "112 条保留" 均不正确。

## 6. T18 evidence_status 纠正

T18 的 `evidence_status = EMPIRICAL_EVIDENCE_AVAILABLE` 由关键词匹配 `known_evidence` 中的 "验证" 文本生成。该"验证"为项目内部编号引用，不构成外部可独立验证的经验材料。

085 纠正：`evidence_status = NO_EMPIRICAL_EVIDENCE`

## 7. 执行时间

084 报告记录开始约 16:18、完成约 16:25，约 7 分钟生成 353 条"双遍对抗审查"。这与 `process_084_batch.py` 的脚本批量生成机制一致，不能作为独立模型推理的证据。

## 8. 权威状态

| 项目 | 值 |
|------|-----|
| 084_generation_method | DETERMINISTIC_RULE_BASED_HEURISTIC_GATE |
| 084_model_configuration | QCLAW_GLM_5_2_MAX_SESSION |
| 084_semantic_acceptance_status | NOT_INDEPENDENTLY_VERIFIED |
| 084_truth_status | PROVISIONAL_CONSERVATIVE_GATE_OUTPUT |
| 084_dual_pass_status | SINGLE_PIPELINE_GENERATED_PRIMARY_ADVERSARIAL_RECONCILED |

## 9. 所有汇总真值（从 JSONL 重算）

| 指标 | 值 |
|------|-----|
| 总记录数 | 353 |
| PROVED_ORIGINAL_CLAIM_WITH_ARTIFACT | 0 |
| REFUTED_ORIGINAL_CLAIM_WITH_COUNTEREXAMPLE | 0 |
| RETAIN_FORMAL_PROPOSITION_UNPROVED | 2 |
| RETAIN_SCOPED_DEFINITION | 113 |
| DOWNGRADE_TO_STRUCTURAL_ANALOGY | 1 |
| DOWNGRADE_TO_EMPIRICAL_ASSOCIATION | 53 |
| DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE | 184 |
| 汇总校验 | 353 ✅ |
| Strict isomorphism accepted | 0 |
| Causal identified | 0 |
| External empirical validated | 0 |
| Primary-adversarial consistent | 352 |
| Primary-adversarial inconsistent | 1 |
| Proof obligations | 353 |
| Evidence obligations | 351 |
