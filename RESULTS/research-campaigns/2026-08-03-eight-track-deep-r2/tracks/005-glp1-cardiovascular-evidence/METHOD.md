# 005 方法与临床 estimand

先冻结 SELECT 的入组（无糖尿病、年龄≥45、BMI≥27、既有 ASCVD）、剂量策略、首次三点 MACE 和观察窗，再分别核对随机试验、FDA/NICE 监管与指南、同队列衍生分析和系统综述。用公开事件数重算 ARR 与粗略 in-trial NNT，但不把它伪装成固定时间或个体 NNT；停药和 ITT 作为治疗策略效果保留。一级预防、BMI<27、糖尿病直接外推、类效应和减重外机制单独降级。脚本和输出在 `select_absolute_risk.py` 与 `reproducibility/`。
