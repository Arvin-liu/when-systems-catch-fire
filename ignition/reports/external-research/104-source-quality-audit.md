# 104 来源质量审计

## 总量
- 088-B v3 atlas 总计：117 条
- 去重后唯一来源：116 条（1 个 DOI 重复：GAP002-01/GAP002-08）

## 按缺口分布

| 缺口 | 来源数 | 类型 |
|------|--------|------|
| GAP-001 干预与控制 | 8 | HIGH |
| GAP-002 层级尺度 | 8 | HIGH |
| GAP-003 时间动态 | 12 | HIGH |
| GAP-004 随机不确定性 | 8 | HIGH |
| GAP-005 优化权衡 | 8 | HIGH |
| GAP-006 路径依赖与历史 | 13 | HIGH |
| GAP-007 表示语言 | 9 | HIGH |
| GAP-008 计算复杂度 | 8 | HIGH |
| GAP-009 不完备性 | 10 | MEDIUM |
| GAP-010 测量与可观测性 | 12 | MEDIUM |
| GAP-011 本体论 | 4 | MEDIUM (稀缺) |
| GAP-012 因果识别 | 5 | MEDIUM |
| GAP-013 证据制度 | 8 | MEDIUM |
| GAP-014 反例与失败 | 4 | MEDIUM (稀缺) |

## 来源类型分布（原始）

| source_type | 数量 |
|-------------|------|
| ARTICLE | 56 |
| journal_article | 21 |
| BOOK | 9 |
| BOOK_CHAPTER | 14 |
| journal-article | 9 |
| monograph | 3 |
| REVIEW | 2 |
| PEER_REVIEW | 2 |
| dataset_codebook | 1 |

**问题**：大小写不一致（ARTICLE vs journal_article vs journal-article），需标准化。

## 同行评审状态分布（原始）

| peer_review_status | 数量 |
|---------------------|------|
| PEER_REVIEWED | 83 |
| peer_reviewed | 30 |
| peer_reviewed_press | 3 |
| institutional_reviewed | 1 |

**问题**：大小写不一致，需标准化。

## 完整性检查

| 字段 | 完整率 |
|------|--------|
| DOI | 117/117 (100%) |
| 标题 | 117/117 (100%) |
| 作者 | 117/117 (100%) |
| 出版日期 | 117/117 (100%) |
| 期刊/出版社 | 117/117 (100%) |
| 摘要/官方摘要 | 117/117 (100%) |
| exact_claim_used | 117/117 (100%) |
| method | 117/117 (100%) |
| limitations | 117/117 (100%) |
| what_it_cannot_support | 117/117 (100%) |
| crossref_verified | 117/117 (100%) |
| retraction_or_correction_status | 117/117 (但全部为空/none，未主动查询) |

## 完整性警示

1. **DOI 重复**：GAP002-01 和 GAP002-08 共享 `10.1016/s0070-2153(07)81015-5`
2. **Retraction 未检查**：所有来源的 retraction_status 为空，088-B 未查询 Retraction Watch
3. **摘要来源未验证**：abstract 字段可能为模型生成而非出版商摘要
4. **全文未读取**：0/117 有全文审阅记录
5. **来源类型需标准化**：9 种不同值需映射到受控词汇
6. **来源稀缺缺口**：GAP-011 (4条) 和 GAP-014 (4条) 需优先补齐

## Crossref 验证状态

所有 117 条 DOI 均标记 crossref_verified=true。但 Crossref 验证仅确认：
- DOI 在 Crossref 数据库中存在
- 标题和年份与 Crossref 记录匹配

Crossref 验证 **不** 确认：
- 论文内容是否支持点火补丁
- 论文是否经过同行评审（Crossref 元数据可能不准确）
- 论文是否被撤稿（需要单独查询）
- 论文结论是否正确
