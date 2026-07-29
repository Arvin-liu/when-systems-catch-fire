# RESULTS：人类可读结果层

`RESULTS/` 把机器注册表、报告和历史资产投影为可直接阅读的结果。它不复制或提高证据权限；每个结论仍受来源、成熟度、处置和 claim ceiling 约束。

- [LATEST.md](./LATEST.md)：当前最重要的结论与状态。
- [CORRECTIONS.md](./CORRECTIONS.md)：撤回、降级、隔离与修订。
- [OPEN-QUESTIONS.md](./OPEN-QUESTIONS.md)：未解决问题、所需证据和停止条件。
- [ADJUDICATION-SUMMARY.md](./ADJUDICATION-SUMMARY.md)：函数与非函数断言裁决的计数、主题、例子和入口。
- [RESEARCH-AND-ARTICLES.md](./RESEARCH-AND-ARTICLES.md)：研究、复算、文章和审计主线。
- [CHRONOLOGY.md](./CHRONOLOGY.md)：从仓库报告恢复的完整时间/路径台账；由生成器维护。
- [CLAIM-DELTA.md](./CLAIM-DELTA.md)：本轮新增或修改的知识资产与关联断言。
- [IMPACT-ANALYSIS.md](./IMPACT-ANALYSIS.md)：依赖传播和受影响范围。
- [EVIDENCE-LINEAGE.md](./EVIDENCE-LINEAGE.md)：证据谱系变化。
- [SELF-CORRECTION-AUDIT.md](./SELF-CORRECTION-AUDIT.md)：自动规则的发现、阻断与整改计划。

机器对应物位于 `data/governance/human-results/` 与 `data/governance/self-correction/`。CI 同时检查两层；缺任一层即失败。
