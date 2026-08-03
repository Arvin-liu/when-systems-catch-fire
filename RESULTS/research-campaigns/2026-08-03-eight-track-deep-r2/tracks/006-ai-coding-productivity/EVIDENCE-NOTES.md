# 006 证据阶段记录：AI 编程生产率

## 阶段边界

本文件只记录逐项阅读、数据入口、字段和可复核结果；不把任何一项来源的宣传摘要当作独立证据，也不把三个实验的百分比平均成一个“AI 编程生产率”。R1 的身份是 `UNVERIFIED_RAPID_EVIDENCE_SCANS`，R1 报告只作为检索线索。

证据阶段开始于 2026-08-03 10:59 Asia/Shanghai。完整阅读了 METR 论文 50 页、Microsoft 现场实验论文 38 页、GitHub Copilot 控制实验论文 19 页，并打开 CMU 数据页、METR 2026 方法更新、Microsoft Research 项目页和 GitHub 第一方说明页。页码以下均指对应下载 PDF 的 PDF 页码；网页用行号定位。

## METR：论文、公开仓库与输入

### 论文正文定位

- [METR 论文](https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf)，下载文件 SHA-256：`b6d4a8e7d8aeed20cc9a4545e485fdc5496b5cc48470338d2d7662b1953e5765`。
- PDF p.1：随机对照试验；16 名开发者；246 个 issue；AI 允许与不允许随机分配；论文摘要报告实际完成时间增加约 19%，并区分开发者事前预测与事后估计。
- PDF pp.2、4–6：任务来自参与者熟悉的大型开源仓库；平均约 5 年相关经验；开发者先提交任务与无 AI 预测，随后随机决定 AI 是否允许；AI 允许条件不强制使用；实现时间由初始实现和代码审查后的修订时间组成。
- PDF p.8：AI 允许 136 个 issue、AI 不允许 110 个 issue；原始完成时间比值较回归结果更大；主要回归调整无 AI 预测时间。
- PDF pp.10–12：论文将仓库熟悉度、规模／复杂度和 AI 输出审查视为解释异质性的候选；对 20 个因素分为有证据、混合／不清楚和反证三类；这些是设置内解释，不是对所有开发工作的总体因果结论。
- PDF pp.18–19：`Prior Task Exposure` 高于 3 被定义为高暴露；`External Resource Needs` 不高于 2 被定义为低外部资源需要；论文报告两项都显示“中等证据”的更大减速，但不是强确认。
- PDF p.26：论文称有 27 个未完成审查的 issue，并报告极端填补下约 14% 和 23% 的减速；同页还报告以屏幕录制总时长为结果时约 25% 减速。
- PDF pp.27–30：主模型为 `log(total_time) ~ ai_treatment + log(predicted_time_no_ai)`；总时间包含初始实现和审查后时间，缺失审查时间按处理组均值填补；异质性以 `AI × subgroup` 交互项估计；比例估计量作为敏感性检查。
- PDF p.27：论文说明不通常加入开发者固定效应，因为在控制预测时间后其解释力有限；本轮仍把开发者固定效应作为挑战性敏感性分析运行。
- PDF p.30：论文报告开发者任务级处理分配为 AI 允许 136、AI 不允许 110，并讨论预测与结果的关系。

### 精确公开数据和代码

锁定的 METR 公开仓库为 [Measuring-Early-2025-AI-on-Exp-OSS-Devs](https://github.com/METR/Measuring-Early-2025-AI-on-Exp-OSS-Devs)，精确 commit：`7ff2d7670235f531dff77eff58355bd77392f396`。该 commit 的 `README.md` 明确给出复算命令和预期输出，`data_complete.csv` 是匿名任务级输入，`regression.py` 是主回归代码。

- `data_complete.csv`：246 行数据、9 个字段；SHA-256 `1493fc46dc379b15d2c39273fa7a7ee98767ff0d90dea113f300d7338f165746`。
- `regression.py`：SHA-256 `41307fa0b2f617eb815fdaaf41ee18c04fb7332eab118e86c1556154f496afd6`。
- `README.md`：SHA-256 `8d9ce0ac356c12606299a7f2f3a5ccad4b0ce2e344759e837bc65d4542541dd4`。
- 数据字段实际为：`dev_id`、`issue_id`、`predicted_time_no_ai`、`predicted_time_ai_allowed`、`prior_task_exposure_1_to_5`、`external_resource_needs_1_to_3`、`ai_treatment`、`initial_implementation_time`、`post_review_implementation_time`。
- 数据复核得到 16 名开发者、246 个 issue；AI 不允许 110、AI 允许 136；`post_review_implementation_time` 缺失 16 行，其中 AI 不允许 7、AI 允许 9；两组分别按可观测审查时间均值 9.708738 和 14.944882 分钟填补。
- `external_resource_needs_1_to_3` 的非缺失值为 1、2、3 和一个 5；这与字段名和论文的 1–3 描述不一致。该行是 `dev_id=26, issue_id=46`，AI 允许，初始实现 27 分钟、审查后 0 分钟。它不改变主回归的估计（排除后由 18.8400% 变为 19.0801%），但降低了该字段异质性解释的清晰度。
- 论文 PDF p.26 写的是 27 个未审查 issue，而锁定仓库的可见 CSV 只有 16 个缺失审查时间。两者都能与公开主回归方向相容，但这是一个必须保留的“论文叙述—当前数据版本”差异，不能默认为同一计数。

### 实际运行与失败尝试

第一次依赖安装使用本机 Python 3.14，执行 METR README 指定的 `statsmodels==0.14.4 scipy==1.15.2` 安装时，arm64 没有适用的 SciPy wheel，源码构建因缺少 `gfortran`／`flang` 等 Fortran 编译器失败。该失败被保留为环境记录，不被写成“已复现”。随后使用本机 Python 3.12.13 arm64 虚拟环境完成运行，实际包版本锁定于 `reproducibility/requirements.lock.txt`。

执行的官方命令等价于：

```text
python regression.py --input-data data_complete.csv
```

官方脚本的实际输出已固定在 `reproducibility/output/official_regression.txt`：

```text
Regression calculated speedup of:          0.188
CI calculed with stderr=Homoskedastic:     (0.013, 0.395)
CI calculed with stderr=Robust (HC3):      (0.013, 0.394)
CI calculed with stderr=Clustered By Dev:  (0.016, 0.39)
```

`reproducibility/recompute_metr_006.py` 是本轮独立复核脚本，除逐项复制主模型外，额外输出初始实现时间、完整审查案例、极端填补、开发者固定效应、均值比值以及两个预先定义的交互异质性分析。所有输入和输出都在 `reproducibility/` 保存，避免只留下文字结论。

## Microsoft：三项现场实验的正文审计

承重正文为 [Microsoft Research 项目页](https://www.microsoft.com/en-us/research/publication/the-effects-of-generative-ai-on-high-skilled-work-evidence-from-three-field-experiments-with-software-developers/) 及作者公开 PDF；项目页标为 2025 年 6 月，PDF 38 页，SHA-256 `932bdd4ef1c75391935d759b1b7d918b073c86b6c654a5f40d6e18f258459cd4`。

- PDF pp.1、5–6：Microsoft、Accenture 和匿名 Fortune 100 企业三个现场实验；表 1 的样本规模分别为 1,746、320、3,054 名开发者。Microsoft 同时有个人级和团队级分配，Accenture 为个人级，匿名企业为随机错峰 rollout。
- PDF pp.5–6：Microsoft 实验约 2022-09 至 2023-04，控制组后来提前获得 Copilot；Accenture 约 2023-07 至 2023-12，有邮件、培训和管理者鼓励；匿名企业用 2023-09 至 2023-10 的随机邀请时间。三个实验的实际干预时长、鼓励方式和控制污染不相同。
- PDF pp.7–8：主要结果是开发者周级 pull request 数量、commits、builds 和 build success rate；大量周级观测为零，标准差通常大于均值，论文明确说这限制了实验回归的统计功效。Microsoft 另有审查通过率、评论、冲突和 PR 合并时间等质量代理；匿名企业没有同样的质量指标。
- PDF pp.9–12：实际采用率不等于随机获得访问权。论文用处理分配作为采用的工具变量，估计的是服从鼓励而采用者的 LATE；控制组最终获得访问权，所以采用差异随时间衰减，作者用开发者与周固定效应以及按采用差异加权的 IV。
- PDF p.12 Table 3：合并的加权 IV 是每周 pull request 数 `+26.08% (SE 10.3%)`；该列是三个不同设计结果的精度加权平均，不是一个统一的开发者级随机实验，也不是完成时间百分比。
- PDF pp.13–14 Table 4：Microsoft 质量代理中 approval rate 的加权 IV 为约 `+9.88% (SE 3.28%)`；评论、冲突和 PR 完成时间结果不显著。Accenture 的 build success rate 加权 IV 为 `-17.40% (SE 7.12%)`，所以“产出增加”不能直接替代“质量不变”。论文自己把这种跨企业质量差异称为可能的异质性，并提醒估计嘈杂。
- PDF pp.24–25：数据清理并非零成本。Microsoft 从 1,746 人缩到 1,521 人；Accenture 从 369 缩到 316；匿名企业从 3,054 缩到 3,030。控制组提前采用者仍被保留。论文还说明实验未预注册，且分析者没有收集原始实验数据。
- PDF pp.28–31：作者明确列出企业工作流、任务类型、鼓励机制、控制组开放时间和 Copilot 版本更新等异质性来源，并承认只有三个企业，不能系统估计这些异质性。
- PDF p.32：一项被裁员冲击的 Accenture 早期实验因采用数据缺失而使用控制组采用时间的保守填补；任务数估计 `-39.18% (SE 36.78%)`，不确定性很大，不能当作正式合并结果。
- 当前没有与论文配套的公开原始 developer-week 数据和可独立运行的分析仓库入口；因此本轮不声称“复算了 Microsoft 26.08%”，只做正文方法、分母和结果层审计。

## GitHub Copilot：控制实验正文审计

承重正文为 [arXiv:2302.06590](https://arxiv.org/abs/2302.06590) 的 v1 PDF，19 页，SHA-256 `60d9bbb58e67a3ba5c5df28926227994086baa9767c0b0f4bc61b11035c15a9c`。

- PDF pp.1–5：2022-05-15 至 2022-06-20；通过 Upwork 招募 95 名开发者，随机分为处理 45、控制 50；任务是 JavaScript HTTP server；两组都可用互联网和 Stack Overflow，处理组可用 Copilot 并观看简短教学。
- PDF p.4：每人获得相同模板仓库和 12 个测试；完成时间定义为仓库创建到第一次提交并通过全部 12 个测试的时间。该结果是一个固定短任务的测试通过计时，不含真实项目审查、维护或长期缺陷。
- PDF p.5：95 名中只有处理和控制各 35 人完成任务和问卷；论文的主要时间比较是在这 70 名“完成者”上，均值为处理 71.17 分钟、控制 160.89 分钟，报告 `55.8%` 更快和 p=`0.0017`。因此不能把 55.8% 当作 95 人全体的无条件平均效果。
- PDF p.5：完成率差异为 7 个百分点，95% 区间为 `[-0.11, 0.25]`，不显著；另有 4 个超过 300 分钟的离群点，全部在控制组。
- PDF p.6：异质性模型报告较少编程经验、较高日编程时长和 25–44 岁组更可能受益，但样本来自单一标准任务；论文没有把交互结果扩展为所有任务或职业层面的结论。
- PDF pp.7–8：论文明确承认没有测量代码质量，且标准化任务和 JavaScript 环境的外推需要更多研究。
- [GitHub 第一方说明](https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/) 只作来源链和自报体验审计，不作科学结论的独立证明；其网页更新至 2024-05-21，行 480–488 重述随机分组、95 人、70 名完成者、完成率 78% 对 70% 和约 55% 更快。

## 竞争结果的可比性字段（证据层）

| 研究 | 处理单位和工具 | 核心结果单位 | 依从性／选择 | 质量或返工 |
|---|---|---|---|---|
| METR | 熟悉开源仓库 issue；AI 允许／不允许随机；Cursor Pro 与多种当时模型 | 单 issue 总实现时间；主模型为日志时间 | AI 允许不强制使用；16 个任务级缺失审查时间按组均值填补；论文还报告开发者预期与真实结果方向相反 | 有审查后时间，但不是客户缺陷、安全或长期维护指标 |
| Microsoft | 企业开发者周级工作流；Copilot 访问分配／随机错峰；三种企业设计 | 每周 PR、commits、builds、build success；合并结果为精度加权 W-IV | 访问分配与采用不一致；控制组后来开放；主结果是 LATE，且三企业工具、时间窗、鼓励方式不同 | Microsoft 有审查代理；Accenture build success 方向相反；长期产品价值未直接测量 |
| GitHub | 单一 JavaScript HTTP server；Copilot 访问随机 | 通过 12 项测试的完成时间；主要分析为完成者条件样本 | 95 随机但仅 70 完成；5 名处理者未完成注册；完成率差异不显著 | 只测测试通过和时间；论文明确没有代码质量、返工或维护结果 |

这张表只固定比较字段，不把 `+18.8% 时间`、`+26.08% PR 数` 和 `-55.8% 单任务时间` 变换成同一个总效果。

## 当前证据阶段结论上限

1. METR 的公开数据和官方脚本在锁定 commit 上真实重算成功，主回归得到 `+18.84%` 总实现时间，三种标准误区间与 README 预期一致；这支持“该特定实验与数据版本中的任务时间增加”这一窄主张。
2. METR 的当前公开 CSV 与论文“27 个未审查 issue”计数不一致，且有一个外部资源字段越界值；这两个差异进入挑战阶段，不能用“复算成功”抹平。
3. Microsoft 的 `+26.08%` 是三种现场设计的周级任务代理的精度加权 LATE，不是完成时间，也不是同一实验；质量代理并非全都正向，原始数据未公开，因此本轮仅审计正文。
4. GitHub 的 `55.8%` 是单一固定任务、70 名完成者条件样本的完成时间差异；论文没有代码质量或长期维护结果，不能外推为一般软件工程生产率。
