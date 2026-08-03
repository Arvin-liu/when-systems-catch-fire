# R1 → R2 裁定矩阵

R1 的统一身份是 `UNVERIFIED_RAPID_EVIDENCE_SCANS`。下表把 R1 的候选叙述与 R2 重新核验后的最低可支持命题分开；R2 仍不是正式知识，全部等待 GPT/owner 逐项审定。

| 顺序/主题 | R1 检索线索 | R2 研究身份与关键改变 | R2 终局裁定 | 五阶段提交 |
|---|---|---|---|---|
| 004 清洁电力 | 全球清洁电力增量覆盖新增需求、煤电下降 | `REPRODUCIBLE_DATA_RECONCILIATION`；实际重算 Ember 当前 CSV 与 IEA 图表，区分 clean/renewable/low-emissions 与年度电力口径 | `SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`；仅限指定版本的全球年度电力，不外推小时匹配、区域可靠性或全能源因果 | `a863584b → f3b6a6f9 → f8549b12 → 469d4879 → 5cab41fa` |
| 006 AI 编程 | METR 约 19% 减速、Microsoft 26.08% 增长、GitHub 55.8% 加速并列 | `DATA_REANALYSIS_AND_HETEROGENEITY_STUDY`；锁定 METR 数据/代码并重算，拆开三种任务、采用和完成者 estimand，保留公开数据差异 | METR 窄主张 `SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`；跨研究 `CONTEXT_DEPENDENT_COMPETING_ESTIMANDS` | `e68720ee → 2d4eaa03 → 90d325aa → 5d073d52 → 16be95dd` |
| 005 GLP-1 | GLP-1/减重药具有普遍心血管保护方向 | `HIGH_STAKES_CLINICAL_EVIDENCE_REVIEW`；锁定 SELECT 人群、剂量、终点、绝对风险、粗略 in-trial NNT、停药与监管边界 | SELECT 窄主张 `SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`；一级预防、BMI<27、类效应和独立机制不支持/证据不足 | `4ee1ef05 → 367dc0c1 → 3b838cac → 088391e7 → fb76381d` |
| 003 高温行动计划 | 有行动计划可减少约 25.2% 热归因死亡 | `CAUSAL_POLICY_EVALUATION`；审计 102 地点模型、公开输出、100/1000 模拟差异、德国 DID 与实际执行边界 | `SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`；保留模型内观察性/反事实方向，不写固定因果效果或单元素归因 | `3814adf5 → 0c98b1b2 → 008a1413 → 50479178 → 6ff57031` |
| 002 手写与键盘 | 手写促进学习、键盘损害学习的单一候选方向 | `MULTI_OUTCOME_EVIDENCE_SYNTHESIS`；拆开 EEG、即时、延迟、复习、笔记策略、熟练度/可及性，并加入直接复现 | `SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`；跨结果 `CONTEXT_DEPENDENT_COMPETING_ESTIMANDS`，不支持普遍赢家 | `2798a0eb → 670012e1 → 22b7c5d7 → d6ef3cdb → 05ad776b` |
| 001 AI 天气 | AI 极端天气能力弱于物理模型 | `BENCHMARK_AND_METHOD_AUDIT`；核对模型、训练期、真值、极端定义并做 WeatherBench2 粗复算，加入不同 benchmark 竞争证据 | `SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`；只支持 Zhang 指定纪录超越 benchmark，跨 benchmark `CONTEXT_DEPENDENT_COMPETING_BENCHMARKS` | `ba1a1500 → cd3c8840 → e9f2ae02 → d58fd5b3 → 7b326474` |
| 007 电动车火灾 | 现有证据偏向电动车起火率较低 | `DENOMINATOR_DEFINITION_AND_AGE_AUDIT`；重算丹麦/瑞典官方分子分母，审计车龄、类别、自由文本和起火定义 | `SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`；只保留部分北欧辖区限定的每车观测频率；跨辖区 `NONCOMPARABLE_CROSS_JURISDICTION_EVIDENCE` | `a358cac1 → f98f7d76 → 31e15507 → 096a96b3 → 3600efa0` |
| 008 微塑料 | 斑块 MNP 与事件强相关但证据不足 | `CAUSAL_CONTAMINATION_AND_REPLICATION_AUDIT`；完整核对 S1 队列，审查手术室/基质污染、选择、事件模型和独立组织/事件复制 | `BOUNDED_NULL_OR_INSUFFICIENT_RESULT_COMPLETE`；一般人群因果 `INSUFFICIENT_EVIDENCE_FOR_CAUSAL_CLAIM`，仅保留队列内关联和方法范围内组织富集 | `d601d9a6 → cc3693e0 → d78f6daf → 5522c8c6 → d9054c73` |

说明：各轨道另有普通的阶段元数据校正提交；矩阵中的五项是对应阶段内容提交，不以提交数量代替研究深度。008 的 evidence/analysis/challenge/final 校正和早期冻结元数据亦保留在该轨道 `TRACK_STATE.json` 中。
