# 006 来源依赖审查

## 目的

本审查单独回答“看到了几份网页”与“有几条独立证据链”是否被混淆。来源之间的作者、数据、机构和原始文件关系必须保留；同一 CSV 的论文、GitHub 仓库和 CMU 镜像不能算三次复制。

## 依赖关系

| 来源 | 依赖关系 | 可承担的任务 | 不能承担的任务 |
|---|---|---|---|
| METR 论文 PDF、arXiv 版本、METR GitHub 仓库 | 同一研究团队；论文版本之间也不是独立研究 | 设计、原始主张、代码和数据的内部一致性检查 | 独立外部复制；论文与代码的同源一致不等于客观确认 |
| CMU S&DS 数据页和 `metr-ai.csv` | 下载 CSV 的 SHA-256 与 METR `data_complete.csv` 完全相同 | 数据入口和字段说明的独立网页呈现 | 独立数据采集或独立结果复制 |
| METR 2026 方法更新 | 同一组织的后续研究反思 | 选择偏差、任务选择、工具时代和测量困难的反方材料 | 对早期 246 个任务结果的独立再估计 |
| Microsoft 三企业论文与 Microsoft Research 项目页 | 项目页是论文摘要和机构页面；数据由企业协作产生 | 正文方法、三项实验和质量代理审计 | 把摘要页当作独立实验证据 |
| Microsoft 论文与 GitHub Copilot 论文／GitHub 博客 | 有共同的 Microsoft/GitHub 工具和作者／组织链，样本与任务不同 | 竞争设计和结果层审计 | 视为与产业方完全无关的独立复制 |
| Microsoft 期刊 supplemental / replication files | 同一论文的附录和数据包；数据下载页受复现政策约束 | 继续核验 ITT、W-IV 和附录方法；目前已读到公开附录 PDF | 未勾选协议、未提交姓名／机构／邮箱之前，不声称取得或重算受限数据 |

## Microsoft 数据访问检查

Management Science 文章页明确指向 supplemental material 和 replication files。公开 replication 页面在 2026-08-03 打开后显示：下载文件仅限“使用同一数据和模型验证论文主要结果”，并要求点击同意、填写 first name、last name、organization、email；该页面还声明其他使用需要作者明确许可或第三方数据源许可。入口和字段可在 [INFORMS replication files page](https://services.informs.org/dataset/mnsc/download.php?doi=mnsc.2025.00535) 的网页行 11–27 复核。

本轮没有提交外部表单，也没有绕过该访问条件，因此 Microsoft 原始 developer-week 数据重算状态为：

`BOUNDED_RESEARCH_BLOCKED_WITH_VERIFIABLE_EVIDENCE`

这只适用于“Microsoft 原始数据重算”这一子任务，不阻断 006 对论文全文、公开附录和方法的审计。公开附录仍提供了重要的反方事实：在控制组开放前的早期窗口，Microsoft 与 Accenture 的 pooled ITT pull-request 估计为 `+4.66% (SE 3.56%)`，对应 IV 为 `+20.16% (SE 14.37%)`；因此 `+26.08%` 不是唯一无条件的处理效果表达。

## 来源独立性结论

本轮真正的独立动作有三类：

1. 在 METR 精确 commit 上对公开 CSV 运行官方代码；
2. 用独立脚本、同一锁定输入重建主回归、敏感性和交互模型；
3. 用不同论文和企业实验的完整正文比较它们的 estimand、依从性和质量指标。

这三类动作提高了内部可复核性，但仍不等于存在一项外部研究对 METR 原始任务的独立复制。最终报告必须把 `SUPPORTED_WITH_SCOPE` 和 `EXTERNAL_INDEPENDENT_REPLICATION_NOT_FOUND` 同时写出。
