# 006 AI 编程生产率：数据重分析与异质性研究

## 最终裁定

**窄主张：`SUPPORTED_WITH_SCOPE_AFTER_DEEP_REVIEW`。** 在 METR 精确公开数据版本、官方代码和原研究主模型下，AI 允许任务的总实现时间估计增加约 18.84%；这一方向在初始实现时间、完整审查案例、极端审查时间填补和多种标准误规格下没有被推翻。

**跨研究主张：`CONTEXT_DEPENDENT_COMPETING_ESTIMANDS`。** Microsoft 的 `+26.08%` 是三项企业现场实验 weekly pull request 数的精度加权 W-IV，GitHub 的 `55.8%` 是单一 JavaScript HTTP server 任务中 70 名完成者的条件完成时间差异；两者都不能与 METR 的熟悉大型仓库 issue 总时间合并成“AI 编程生产率平均提高／降低多少”。本项研究完成，但所有结论仍等待外部审定。

## 研究范围与实际复算

R2 研究身份为 `DATA_REANALYSIS_AND_HETEROGENEITY_STUDY`。METR 数据锁定在公开仓库 commit `7ff2d7670235f531dff77eff58355bd77392f396`，输入 `data_complete.csv` SHA-256 为 `1493fc46dc379b15d2c39273fa7a7ee98767ff0d90dea113f300d7338f165746`。数据包含 246 个 issue、16 名开发者，AI 不允许 110、AI 允许 136。官方 `regression.py` 与独立脚本均已运行，环境为 Python 3.12.13、`statsmodels==0.14.4`、`scipy==1.15.2`，完整哈希、命令和输出在 `reproducibility/`。

主模型为 `log(total_implementation_time) ~ ai_treatment + log(predicted_time_no_ai)`；总时间由初始实现与审查后修订组成，缺失审查时间按处理组均值填补。官方输出为同方差 `[+1.3%, +39.5%]`、HC3 `[+1.3%, +39.4%]`、开发者聚类 `[+1.6%, +39.0%]` 的 18.8% 时间增加。独立脚本未四舍五入估计为 18.84%。

## 重分析结果

初始实现时间单独估计约 19.83%；保留有审查后时间的 230 个 issue 约 20.12%；论文所述两个极端缺失填补约为 22.94% 和 14.20%；加入开发者固定效应并按开发者聚类约 14.93%，其区间跨零；简单均值比值为 33.67%，说明结果尺度和长尾会显著影响百分比。因此应报告“在多种规格下方向仍为正、精度和数值有边界”，而不是把 18.84% 当作稳定常数。

异质性分析只使用 159 个有字段的 issue。高 `Prior Task Exposure` 组估计约 40.91% 减速，低暴露组约 14.11%；低 `External Resource Needs` 组约 35.66%，高外部资源需要组约 8.66%。两项交互 p 值约 0.313 和 0.334，故最终只保留“方向性候选”，不写成强异质性因果结论。

## 竞争实验审计

METR 测的是熟悉大型开源仓库中的 issue 总实现时间，AI 允许不强制使用，结果包含审查后修订。Microsoft 测的是企业开发者周级 PR、commit、build 和 build-success，主结果用访问分配作为采用的工具变量，估计采用者 LATE；公开附录早期窗口 pooled ITT 为 `+4.66% (SE 3.56%)`，对应 IV 为 `+20.16% (SE 14.37%)`，与首选 `+26.08%` 属于不同 estimand。Microsoft 的 approval rate 代理方向为正，但评论、冲突和 PR 完成时间不显著，Accenture build-success 方向为负，不能推出质量和维护无代价。

GitHub 论文随机分配 95 人（45 处理、50 对照），但最终每组只有 35 人完成；主要时间均值为 71.17 对 160.89 分钟，55.8% 差异条件化于完成者。任务是同一 JavaScript HTTP server，成功标准为首次提交通过 12 项测试；论文明确没有测代码质量、返工和长期维护。因此它是标准化短任务的强计时证据，不是一般真实软件工程的总效果。

这三项研究的方向差异可由结果单位、任务熟悉度和复杂度、工具代际、采用依从性、完成者选择及质量测量不同解释为竞争证据；证据不支持把它们合并为单一总效果。

## 不能抹平的限制

锁定 CSV 的 `post_review_implementation_time` 缺失 16 行，但 METR 论文站点版和 arXiv 版都写 27 个未审查 issue；该论文—数据版本差异没有在公开材料中消解。字段 `external_resource_needs_1_to_3` 还出现一行值 5，排除后主方向只由 18.84% 变为 19.08%，但降低了该字段异质性解释的上限。

METR 论文、arXiv、METR 仓库和 CMU 数据页不是独立复制；CMU CSV 与 METR CSV SHA-256 完全相同。Microsoft 的期刊 replication files 入口可以公开打开，但要求同意复现政策并填写姓名、机构和邮箱；本轮未提交表单，也没有把受限数据重算写成已完成。因而 Microsoft 子任务是 `BOUNDED_RESEARCH_BLOCKED_WITH_VERIFIABLE_EVIDENCE`，不影响对公开正文和附录的审计。

## 结论上限

本报告只支持：在早期 2025 年、16 名有经验开发者、熟悉大型开源仓库、该 AI 工具和该时间定义下，METR 公开数据呈现约 19% 的任务时间增加；在其他两类实验中，标准化短任务时间或企业 weekly PR 产出呈现相反方向。它不支持“AI 普遍让程序员变慢／变快”、长期缺陷或安全结论、所有开发者采购建议，亦不进入正式知识或项目生命周期。
