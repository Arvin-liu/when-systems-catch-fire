# 104 外部证据状态阶梯（Evidence Tier Schema）

## 状态定义

| 状态 | 含义 | 允许的来源 |
|------|------|-----------|
| `LEAD_DISCOVERED` | 仅由 anysearch 或其他检索工具发现线索 | anysearch, web search, bibliography browsing |
| `IDENTIFIER_RESOLVED` | DOI/ISBN/arXiv/PubMed 等标识符已解析且格式正确 | Crossref API, arXiv API, PubMed API, ISBN resolver |
| `METADATA_VERIFIED` | 标题、作者、年份、期刊/出版社与权威元数据源一致 | Crossref metadata, publisher page, library catalog |
| `ABSTRACT_REVIEWED` | 摘要已实际读取并记录内容锚点 | Abstract text from publisher/Crossref/semantic scholar |
| `FULLTEXT_REVIEWED` | 全文或足够方法/结论段落已实际读取 | Open access full text, author manuscript, institutional repository |
| `CLAIM_SUPPORT_CONFIRMED` | 来源内容确实支持指定投影或接口字段 | Full text or sufficient methods/conclusions section read |
| `CLAIM_SUPPORT_PARTIAL` | 仅支持部分字段或边界 | Content read but coverage incomplete |
| `CONTRADICTORY_EVIDENCE` | 来源与补丁假设冲突 | Content read and found to contradict |
| `RETRACTED_OR_CORRECTED` | 存在撤稿、重大更正或可信度警报 | Retraction Watch, publisher notice, Expression of Concern |
| `UNAVAILABLE_FOR_CONTENT_REVIEW` | 只能核验元数据，不能读取支持内容 | Paywalled, lost, restricted access |

## 状态转换规则

```
LEAD_DISCOVERED → IDENTIFIER_RESOLVED (DOI/format check passes)
IDENTIFIER_RESOLVED → METADATA_VERIFIED (Crossref/publisher metadata match)
METADATA_VERIFIED → ABSTRACT_REVIEWED (Abstract actually read)
ABSTRACT_REVIEWED → FULLTEXT_REVIEWED (Full text or key sections read)
FULLTEXT_REVIEWED → CLAIM_SUPPORT_CONFIRMED (Content supports patch claim)
FULLTEXT_REVIEWED → CLAIM_SUPPORT_PARTIAL (Content partially supports)
FULLTEXT_REVIEWED → CONTRADICTORY_EVIDENCE (Content contradicts)
METADATA_VERIFIED → UNAVAILABLE_FOR_CONTENT_REVIEW (Cannot access content)
Any state → RETRACTED_OR_CORRECTED (Retraction/correction detected)
```

## 硬规则

1. **Crossref 成功只允许提升至 `METADATA_VERIFIED`**，绝不能直接提升至 `CLAIM_SUPPORT_CONFIRMED`。
2. **DOI 存在 ≠ 同行评审** ≠ 论文真实支持补丁 ≠ 论文结论正确。
3. 书评、社论、预印本、会议摘要、数据集、专著章节必须分别标注，不得统一当作原始同行评审研究。
4. 最新论文、奠基文献、综述、方法论文、负结果与反例必须分开记账。
5. 没有读到内容时必须停在 `METADATA_VERIFIED` 或 `UNAVAILABLE_FOR_CONTENT_REVIEW`，不能凭标题推断。

## 088 来源初始批量评定

基于 088-B v3 atlas 的 117 条来源，按严格标准重新评定：

- 所有 117 条有 DOI 且 Crossref 元数据匹配 → 至少 `METADATA_VERIFIED`
- 所有 117 条有 `abstract_or_official_summary` 字段 → 可提升至 `ABSTRACT_REVIEWED`（但需验证摘要是否为实际读取而非模型生成）
- 0 条有全文读取记录 → 不能提升至 `FULLTEXT_REVIEWED`
- 0 条有 `CLAIM_SUPPORT_CONFIRMED`（需全文内容验证）
- 0 条有 `CONTRADICTORY_EVIDENCE` 标记
- 0 条有 `RETRACTED_OR_CORRECTED` 标记
- `retraction_or_correction_status` 字段全部为空/none，但未主动查询 Retraction Watch

### 批量状态分布（初步）

| 状态 | 数量 |
|------|------|
| METADATA_VERIFIED | 117 |
| ABSTRACT_REVIEWED | 0 (pending verification of abstract source) |
| FULLTEXT_REVIEWED | 0 |
| CLAIM_SUPPORT_CONFIRMED | 0 |
| CLAIM_SUPPORT_PARTIAL | 0 |
| CONTRADICTORY_EVIDENCE | 0 |
| RETRACTED_OR_CORRECTED | 0 |
| UNAVAILABLE_FOR_CONTENT_REVIEW | 0 (not yet assessed) |
