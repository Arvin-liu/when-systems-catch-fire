# 验证与项目审计指南

Version: `0.1.0`

## 两种门，不能互相冒充

结构化门检查已登记的事实：对象版本是否存在、四个配置是否覆盖十二维、证据 ID 是否可回链、来源／目标框架值的每一处变化是否进入差异账本、认识相关变化是否得到处置、L0—L6 与规定对抗类别是否都有样例。

人工门检查机器无法可靠判断的部分：自然中文是否真正成句，省略能否在上下文恢复，长短句是否保留思想压力，文学反常是否有收益，语体是否尊重来源，译文是否在现实阅读中改变了立场。人工门必须读上下文并朗读，不能只搜被动词、`的` 或连接词。

运行结构化门：

```bash
python3 tools/language_thought/validate_language_thought.py
python3 -m unittest tests.test_language_thought_plane
```

验证器会输出 fixture 的 TP、TN、FP、FN、precision、recall 与 unsupported 数量。这里的正类是“这条结构化转换应被门拒绝”，不是“机器理解了语言”。高指标只说明样例合同的实现一致，不能外推到任意散文。

## 对抗样例范围

当前 fixture 必须覆盖：意外事件施事化、进行／完成／终点变化、话题链、零照应歧义、凭空因果连接、证据来源丢失或发明、名词化抽象与事件化成句、合法长短句、应保留的有意标记句法、词面回译相似但框架改变，以及 L0—L6 每层实例。

通过样例用于防止过度修正，拒绝样例用于证明静默差异会失败关闭。`unsupported` 样例明确暴露自动门没有能力裁定的类别，例如只凭文本判断文学收益；它们必须进入人类审查，不能被算作通过。

## 有界项目审计

本轮审计人口在 [`project-audit-population.json`](../../data/language-thought/project-audit-population.json) 中预先列出：公共前门、架构与当前状态、研究入口、之元写作法、两个当前作品、成果书架以及生成的人类阅读表面。它不是对仓库每个历史文件、每句话或所有语言的穷尽扫描。

每项发现只能使用以下 disposition 分类：

- `meaning_or_claim_changed`
- `agency_or_causality_changed`
- `uncertainty_changed`
- `discourse_logic_changed`
- `naturalness_or_style_only`
- `allowed_marked_syntax`
- `no_action`

高价值修复优先于全库文风清洗。历史版本与接受哈希不回填；新版本通过 revision lineage 指向旧版本。机器投影因当前构件变化而重生成，不等于把历史文本重写。

## 假阳性、假阴性与停手规则

- **假阳性：** 看到被动、长句、名词化或省略就判错。防线是允许样例、上下文复核和 `allowed_marked_syntax`。
- **假阴性：** 词面都保留便认为保真。防线是源／目标框架值比较和回译对抗。
- **不支持类别：** 韵律收益、讽刺、作者声音、复杂指称等不能由结构标注自动判定。系统必须说“不知道”。
- **停手：** 改动只会统一作者声音、没有可说明的信息或认识收益时，不改；若反常句法承担明确视角／节奏压力，保留并记录。

审计结果见 [`audit-findings.jsonl`](../../data/language-thought/audit-findings.jsonl) 和任务 114 的人类审计报告。四类角色分离复核在冻结候选后进行，所有意见都有 disposition；开放科学争议保持开放。
