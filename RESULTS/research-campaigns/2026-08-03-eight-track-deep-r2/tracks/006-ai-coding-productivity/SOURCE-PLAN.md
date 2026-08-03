# 006 来源与数据计划

## 一手承重来源

1. METR：论文 PDF `https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf`、arXiv `https://arxiv.org/abs/2507.09089`、公开分析／数据仓库 `https://github.com/METR/Measuring-Early-2025-AI-on-Exp-OSS-Devs`（若重定向或仓库变更，以论文正式链接和实际 commit 为准）。需定位随机化、任务选择、依从性、时间定义、模型、删失、质量和附录。
2. Microsoft Research：项目页 `https://www.microsoft.com/en-us/research/publication/the-effects-of-generative-ai-on-high-skilled-work-evidence-from-three-field-experiments-with-software-developers/` 及其论文／预印本链接。必须拿到可合法阅读的正文和补充材料，分别记录三项企业实验，不把合并百分比当作同一实验。
3. GitHub/Microsoft 控制实验：论文 `https://arxiv.org/abs/2302.06590`、GitHub 研究说明 `https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/`。论文是承重来源，博客只作来源链和自报指标审计。
4. 独立数据／方法入口：CMU 数据页 `https://cmustatistics.github.io/data-repository/technology/metr-ai.html`、METR 2026 方法更新 `https://metr.org/blog/2026-02-24-uplift-update/`，并主动搜索相反结果、复制研究和方法批评。

## 统一比较字段

`study_id`、任务类型与复杂度、仓库熟悉度、开发者经验、工具／模型版本、随机分配和依从性、样本、时间窗、结果定义、质量、返工、维护、主观体验、分析模型、利益关系、可得数据／代码和限制。

## 重算交付

`reproducibility/` 保存 METR 输入下载 URL、精确 commit、合法文件哈希、环境、脚本、样本筛选和输出。只有当实际运行输出与论文的核心 estimand 对齐，才可标记 `recomputed`; 不可得时记录命令、HTTP／权限结果和替代路径。

## 停止与竞争证据

先完成 METR 数据路径和论文方法，再读 Microsoft/GitHub 正文；主动检索任务难度、经验、工具代际、依从性、质量和返工的相反解释。新闻只触发问题，不进入核心科学证明。
