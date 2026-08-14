# Chapter 06 Evidence Binder：Crossref 与 OpenAlex 两次外部证据试验

## 章节核心问题

当研究系统把 DOI 交给外部服务时，它究竟获得了什么？Crossref 与 OpenAlex 的价值不是给点火的跨域主张盖章，而是把“来源能不能被找到”“元数据是否一致”“论文内容是否被读过”拆成三个不同问题，并让 null、partial 和字段修正可见。

## 可支持的认识

1. Crossref 预注册试验针对固定 DOI 集合和固定字段，117/117 解析题名与年份，修正 5 个年份，保留 1 个有意重复，未出现 retraction signal。
2. Crossref 结果只支持外部 API 在协议范围内返回/解析元数据；报告明确 0 fulltext、0 claim support。
3. 任务 104 将原先过强的来源状态从 `INJECTED_VERIFIED` 降到 `METADATA_VERIFIED`，并列出 14 个缺口；088-A/C 未执行，不能被写成完成。
4. OpenAlex 针对 116 个 unique primary DOI 返回 HTTP 200；101 supported、8 partial、7 null、0 contradicted。
5. OpenAlex 的 null 被继续拆成 4 个 multi exact DOI 和 3 个 no exact，partial 受 online/print、版本或字段歧义影响。
6. 两个试验共同证明的是来源索引和元数据管线可以被预注册、重跑和审计；它们没有核验论文论点、实验结果、物理内容或点火架构。

## 不可支持的强说法

* 不能说 117/117 代表 117 篇文献的内容已读或已支持。
* 不能说 101 OpenAlex supported 代表 101 篇论文支持某个理论。
* 不能说没有 retraction signal 等于论文可靠。
* 不能用 DOI 可解析性推断历史、物理或机制命题。
* 不能把 7 个 null 在没有人工核验前解释成文献不存在或研究无效。

## 来源与提交

* `evidence-program/preregistration` 中 Crossref protocol — 基线 `9b15d359c54694d851c38df6ab3c7ae42544a51b`。
* Crossref run/result artifacts — 任务 103 merge `1b999a221`，固定基线可见。
* `reports/external-research/104-source-quality-audit.md`、`104-dual-088-reconciliation.md` — 任务 104，`16f640045` 附近的结果。
* `reports/external-research/110-openalex-result.md`、`RESULTS/OPEN-QUESTIONS.md` — 任务 110，固定基线可见。

## 相互冲突的历史版本

|旧表述|审计结果|当前表述|
|---|---|---|
|来源已 verified|只请求/解析 metadata，未读全文|metadata verified only|
|117 条来源全部支持研究|0 claim support|117 条元数据记录可回收|
|第二源消除了不确定性|OpenAlex 有 8 partial、7 null|第二源增加了缺口可见性|
|没有 retraction signal 等于可靠|retraction 字段并不等于质量/内容审查|只记录未见该信号|

## 关键数字

* Crossref：117/117 title/year；5 年份修正；1 intentional duplicate；0 fulltext；0 claim support。
* OpenAlex：116 unique primary；101 supported（87.069%）、8 partial（6.897%）、7 null（6.0345%）、0 contradicted。
* OpenAlex null：4 multi exact DOI、3 no exact DOI。
* Function paradigm 相关回收：84 sources，第一轮 0 fulltext；后续 30 张全文证据卡均为 partial，作为同一“找到来源不等于支持内容”的背景。

## 反例

* DOI 正确、题名正确、年份正确的论文，可能仍与正文所用命题无关。
* 一篇文章有 online 版和 print 版时，两个 API 的不同记录不一定是矛盾，也不应自动去重。
* API null 可能来自标识、版本或覆盖范围，而不是来源本身不存在。

## 开放问题

* 如何从 metadata-only 安全推进到全文可核查的 claim support？
* 谁来判断一篇全文是否真的支持某个跨域主张？
* 如何处理 DOI、版本、预印本、撤回、修订和引用关系的时间变化？
* 多个外部源不一致时，何种人工 adjudication 才足够公开？

## Claim ceiling

本章达到 `metadata_verified`、`field_corrected`、`null_exposed` 和部分 `workflow_passed`。它不达到 `fulltext_supported`、`claim_supported`、`mechanism_plausible` 或任何领域真理。最诚实的成果是：两次试验同时提高了“找到什么”和“不知道什么”的可见度。

## 可进入正文的材料

用两次试验构成镜像转折：第一次成功地找到很多记录，却被迫承认没有读内容；第二次增加了一个来源，却暴露了 8 个 partial 和 7 个 null。读者最终应记住，外部接口的意义不只是带回答案，更是带回可定位的未知。

## 只能放附录的工程信息

DOI 列表、HTTP 状态、字段 JSON、请求重试、API URL、年份修正表、exact DOI 匹配规则和 run hash 放附录。正文只保留能改变读者判断的数字和边界。

