# 088 阶段1：087 计数与分母审计

- 执行器：QClaw | 模型：GLM-5.2 | 推理：max
- 审计时间：2026-07-13T19:24:13.091825+08:00
- 方法：从 087 三个原始 jsonl 逐文件独立重算，不复制任何报告数字

## 权威口径（唯一）
- UNESCO 四位学科唯一总数：**250**（registry/kernel/matrix 三集一致，0 重复）
- 24 大类计数总和：250
- 缺口注册表：14（8 HIGH / 6 MEDIUM）
- 三文件 discipline_code 集合完全一致：True

## 重算轴覆盖（与执行报告一致，证实 250 分母正确）
| 轴 | MISSING | PARTIAL | total |
|---|---|---|---|
| intervention_control | 250 | 0 | 250 |
| level_scale | 206 | 44 | 250 |
| temporal_dynamics | 222 | 28 | 250 |
| stochastic_uncertainty | 0 | 0 | 0 |
| optimization_tradeoff | 242 | 8 | 250 |
| path_dependence_history | 234 | 16 | 250 |
| representation_language | 168 | 82 | 250 |
| computational_complexity | 212 | 38 | 250 |
| incompleteness_undecidability | 104 | 146 | 250 |
| measurement_observability | 116 | 134 | 250 |
| ontology | 0 | 250 | 250 |
| causal_identification | 0 | 250 | 250 |
| evidence_regime | 0 | 250 | 250 |
| counterexample_failure | 0 | 250 | 250 |

## 矛盾清单
### C1-denominator-143-vs-250 [HIGH]
087-v1-1-overlay.md 全程使用分母 143（如 143/143、124/143、123/143 等共9处），但 087 全部数据文件权威学科总数为 250，且投影矩阵中 NOT_APPLICABLE=0（无学科被排除）。143 在 087 任何数据文件中均无对应子集来源，属旧口径错误残留。

**证据：**
- 087-v1-1-overlay.md 含 9 处 X/143 分母
- 087-discipline-registry.jsonl 唯一学科=250
- 087-projection-matrix.jsonl 中 disciplines_with_any_NA=0

**处置：** 088 以 250 为唯一权威分母；overlay 的 143 分母在 088 correction overlay 中标为 INVALID_OLD_DENOMINATOR，不沿用。

### C2-181-252-unknown-source [MEDIUM]
用户阶段摘要出现 181/252，但 087 全部产物中：权威学科总数=250（非252），且无任何 181 计数或 252 分母字段。252 可能为另一份 UNESCO 总表口径，181 在 087 内无对应物。

**证据：**
- 重算确认 087 学科总数=250
- 087 无 252 分母、无 181 计数字段

**处置：** 088 不把 181/252 当作 087 真实结果；标记为 USER_SUMMARY_UNMATCHED，需 GPT/用户确认 181/252 出处。

### C3-projection-mislabeled-external-research [HIGH]
087 执行报告将 250/250 描述为'GLM-5.2 max 逐学科语义分析''理论核全量生成'，并暗示外部研究已补齐架构。但所有 250 条 current_assertion_level=SOURCE_DERIVED_PROVISIONAL，未接入任何真实论文/DOI/综述/方法论文/失败证据。此为定性错误：087 只完成'学科投影初稿'，不等于'外部研究已补齐架构'。

**证据：**
- 087-theory-kernels-final.jsonl 每行 current_assertion_level=SOURCE_DERIVED_PROVISIONAL
- 087 产物无 doi/paper/reference 字段
- 用户 087 纠正消息：只能接受为'学科投影初稿完成'

**处置：** 088 将 087 定性降级为'外部来源未接入学科学投影初稿'，并在阶段2-4建立真实外部来源层。

## 结论
- 087 学科计数（250）与缺口计数（14/8 HIGH）经独立重算成立；
- overlay 的 143 分母为错误残留，088 以 250 为唯一权威分母；
- 181/252 在 087 产物中无对应，需 GPT 确认出处；
- 087 定性上只是'学科学投影初稿'，未接入真实外部研究，由 088 阶段2-4补齐。