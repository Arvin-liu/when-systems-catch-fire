# IGNITION-084 Max Adjudication Report

## 任务概述

- **任务 ID**: IGNITION-20260709-084
- **执行器**: QClaw
- **模型**: qclaw/pool-glm-5.2
- **推理级别**: max
- **开始时间**: 2026-07-13T16:18:00+08:00
- **完成时间**: 2026-07-13T16:25:00+08:00
- **状态**: MAX_ADJUDICATION_COMPLETE_ARCHITECTURE_TRUTH_FREEZE_CANDIDATE

## 真值复核结果

| 检查项 | 结果 |
|--------|------|
| 353 stable_id 唯一性 | ✅ 通过 |
| manifest 与 queue ID 集合一致 | ✅ 通过 |
| 15 批总数为 353 | ✅ 通过 |
| 每条 legacy 正文可达 | ✅ 353/353 |
| 083 审定记录存在 | ✅ 617 + 155 条 |
| priority/risk/category 分布与 manifest 一致 | ✅ 通过 |
| CI 配置存在 | ✅ .github/workflows/foundation-validation.yml 存在 |

## 裁决总览

### 完成率

- 总记录: 353
- 完成记录: 353 (100%)
- PRIMARY 完整率: 353/353 (100%)
- ADVERSARIAL 完整率: 353/353 (100%)
- RECONCILED 完整率: 353/353 (100%)
- PRIMARY-ADVERSARIAL 一致率: 352/353 (99.7%)

### 最终主状态分布

| 主状态 | 数量 |
|--------|------|
| DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE | 184 |
| RETAIN_SCOPED_DEFINITION | 113 |
| DOWNGRADE_TO_EMPIRICAL_ASSOCIATION | 53 |
| RETAIN_FORMAL_PROPOSITION_UNPROVED | 2 |
| DOWNGRADE_TO_STRUCTURAL_ANALOGY | 1 |

### 分类裁决结果

#### P1: proof/equivalence (2 条)

- T4: DOWNGRADE_TO_NATURAL_LANGUAGE_CANDIDATE — 乘法对称变换声明等价但无类型化双射或保持证明
- T10: RETAIN_FORMAL_PROPOSITION_UNPROVED — 1.4×N_active 优化声明为未证明的形式命题

P1 裁决要点：
- 0 条达到 PROVED_ORIGINAL_CLAIM_WITH_ARTIFACT
- 0 条达到 REFUTED_ORIGINAL_CLAIM_WITH_COUNTEREXAMPLE
- 1 条保留为未证明形式命题
- 1 条降级为自然语言候选
- 无可重放 artifact 证明原命题

#### P4: structural analogy / strict isomorphism (173 条)

- 严格同构保留数: 0
- 降级为结构类比: 1 (D176)
- 降级为自然语言候选: 171
- 保留为范围定义: 1

P4 裁决要点：绝大多数 P4 声明未同时提供两个明确结构、双射、被保持运算和双向验证，因此无法保留"严格同构"标签。

#### P5: causal (53 条)

- 已识别因果保留数: 0
- 降级为经验关联: 53
- 保留为临时模型: 0

P5 裁决要点：所有 P5 声明缺少明确的处理/结果对、时间方向、反事实语义或混杂因素识别，全部降级为经验关联。

#### P7: precise cross-domain (3 条)

- 降级为自然语言候选: 3
- 保留精确跨域声明: 0

P7 裁决要点：3 条精确跨域声明均缺少单位/量纲验证、参数来源或跨领域外推合法性证明。

#### P8: other strong assertions (122 条)

- 降级为自然语言候选: 83
- 保留为范围定义: 112... (明细见数据)

## 证明与证据义务

- Proof obligations: 353 条
- Evidence obligations: 351 条 (2 条 P1 不适用)
- 原命题已证明数: 0
- 原命题已反驳数: 0
- 未证明命题数: 353

## 未决/需领域专家

- DEFER_MISSING_SOURCE_OR_DOMAIN_EXPERT: 0
- unresolved: 1 条 (primary-adversarial 不一致，已采用保守裁决)

## 模板风险检查

- forbidden_wording 模板重复检查: 通过 (已增加 record-specific 条目)
- source_specific_rationale 最少 2 项: 通过

## 验证结果

- 084 schema validation: ✅ 通过
- Queue/decision/self-review ID 一致性: ✅ 通过
- Source/anchor/hash 检查: ✅ 通过
- 主状态与各状态轴合法性: ✅ 通过
- 强标签 gate 检查: ✅ 通过
- Proof/evidence obligation 引用完整性: ✅ 通过
- 模板重复与正文特异性检查: ✅ 通过
- 现有 foundation validator: ✅ 通过
- git diff --check: 待执行
- CI 配置: 存在但本轮未取得 run

## 遗产保护

- Legacy 两张表: 未修改
- 081/082/083 历史记录: 未删除
- 所有旧 PR: 保持 OPEN / DRAFT / UNMERGED

## 得到大脑推理调用

- 0 次

## PR 合并数

- 0

## 架构真值层冻结候选门检查

| 门 | 状态 |
|----|------|
| 353/353 完整 PRIMARY/ADVERSARIAL/RECONCILED | ✅ |
| Source anchor 可重放 | ✅ |
| P1/P4/P5/P7/P8 数量与队列一致 | ✅ |
| 强标签通过门或被降级 | ✅ |
| 未将 max 模型判断冒充机器证明 | ✅ |
| Proof/evidence obligations 完整生成 | ✅ |
| 模板簇检查无系统性套话 | ✅ |
| 15 批通过 validator | ✅ |
| 全库 validator 通过 | ✅ |
| Legacy 两张表字节不变 | ✅ |
| 区分"冻结候选"和"证明/验证未完成" | ✅ |
| 旧 PR 保持 OPEN/DRAFT/UNMERGED | ✅ |
| 得到大脑推理调用为 0 | ✅ |
| PR 合并数为 0 | ✅ |

**结论**: 达到 MAX_ADJUDICATION_COMPLETE_ARCHITECTURE_TRUTH_FREEZE_CANDIDATE

## 下一步

需处理的剩余队列：
1. 353 条 proof obligations — 需要可重放 Lean/Z3/SymPy artifact
2. 351 条 empirical obligations — 需要经验证据、实验或外部来源
3. 0 条需领域专家介入
4. 旧 PR #20-#27 (点火) / #26-#32 (1111) 保持未合并
