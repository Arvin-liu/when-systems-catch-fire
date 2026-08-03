# 005 来源与临床证据计划

本阶段只接受可定位的原始随机试验、监管原文、正式 HTA、系统综述和主动反方材料。SELECT 的新闻稿、厂商页面和 R1 报告只能作导航，不能独立承担科学结论。

承重来源：

1. SELECT 原始随机试验、ClinicalTrials.gov 注册结果和可得补充材料；提取人群、剂量、分析集、随访、MACE 组成、事件数和停药。
2. FDA Wegovy 处方信息和批准公告；核对适应证、事件率、剂量、安全性和警告。
3. NICE TA1152 正式 guidance 与公开委员会证据包；核对二级预防边界、糖尿病／近期事件外推和经济模型不确定性。
4. SELECT 安全性和 HbA1c 预设分析；分别作为安全层和机制边界层，不当作独立重复试验。
5. 2025 年 SELECT 体脂／腰围预设分析；审查“独立于减重”的机制语言和事后变量混杂。
6. 独立系统综述／荟萃分析；检查其他 GLP-1、双重／三重激动剂、短期试验和 SELECT 权重造成的来源依赖。

必须输出的字段：`population`、`diabetes_status`、`prior_cvd`、`bmi_cutoff`、`drug`、`dose`、`background_therapy`、`randomization`、`analysis_set`、`followup`、`mace_definition`、`events`、`event_rate`、`hazard_ratio`、`ci95`、`absolute_risk_difference`、`nnt_time_window`、`discontinuation`、`serious_adverse_events`、`common_adverse_events`、`funding`、`estimand`、`generalizability`。

NNT 只以同一随机试验、同一人群、同一观察窗和公开分母计算。由于 SELECT 报告的是时间到首次事件及累积事件比例，而非固定时点的简单二项风险，本轮将 `1 / (8,0% - 6,5%)` 标为“试验内观察窗的近似 NNT”，不把它写成恒定的长期或个人 NNT。
