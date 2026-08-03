# R2 八项深度研究 campaign 终稿

## 最终状态

`COMPLETE_AWAITING_GPT_OWNER_ADJUDICATION`

八项均已按固定顺序完成 `freeze → evidence → analysis → challenge → final`，每项达到允许的研究终止状态。所有结果只是待审研究候选，不自动进入点火正式认识。

## 八项结果

- **004 清洁电力**：在指定 Ember/IEA 版本和全球年度电力口径下，低碳增量覆盖新增电力增长，`SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`；不外推小时匹配、区域可靠性或全能源系统。
- **006 AI 编程**：METR 锁定数据重算呈现约 18.84% 时间增加；Microsoft、GitHub 与 METR 是竞争 estimand，`CONTEXT_DEPENDENT_COMPETING_ESTIMANDS`。
- **005 GLP-1**：SELECT 特定二级预防人群、剂量和三点 MACE 复合终点保留窄支持；一级预防、BMI<27、类效应和独立机制不支持或证据不足。
- **003 高温行动计划**：102 地点研究的模型内保护性方向未被公开输出重算推翻，但因果和实际执行效果仍有限，`SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`。
- **002 手写与键盘**：结果依赖即时/延迟、复习、笔记策略和学习者；不支持普遍设备赢家，`CONTEXT_DEPENDENT_COMPETING_ESTIMANDS`。
- **001 AI 天气**：HRES 只在 Zhang 指定纪录超越 benchmark 中占优；跨 benchmark `CONTEXT_DEPENDENT_COMPETING_BENCHMARKS`，不支持运营替代结论。
- **007 电动车火灾**：仅保留部分北欧官方统计在各自辖区呈现较低每车观测频率；跨辖区、年龄调整、每公里、全寿命和全球结论不支持。
- **008 微塑料**：斑块组织富集有方法范围内支持，S1 队列内事件关联保留，但污染/基质有效性和独立临床事件复制不足；一般人群因果为 `INSUFFICIENT_EVIDENCE_FOR_CAUSAL_CLAIM`。

## 交付与安全边界

详细入口在 `README.md`、`R1-TO-R2-VERDICT-MATRIX.md`、`CROSS-TRACK-SOURCE-DEPENDENCE.md` 和 `CAMPAIGN-LESSONS.md`。每项轨道保留五阶段产物、来源审计、哈希/访问边界、分析、反方审查和 R1→R2 变化记录。

本 campaign 仅写入隔离研究分支 `research/eight-track-deep-validation-20260803-r2` 的结果目录；没有修改 `relay/current`、任务 114、正式 `main`、项目 Foundation/规划器/生命周期，没有创建 PR 或 tag。最终判断等待 GPT/owner 逐项查证。
