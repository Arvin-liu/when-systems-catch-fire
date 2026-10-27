# IGNITION-106: 105 证据纠错报告

## 执行环境
- 执行器: QClaw
- 模型: qclaw/pool-glm-5.2
- 推理级别: max (adaptive)
- 未切换模型, 无 fallback

## 纠错背景
GPT 查证发现 105 存在两个确定性缺陷：
1. 虚假 18/18 覆盖：4 个学科 source_count=0
2. 验证器未读取覆盖矩阵，"10/10 PASS"不成立

## 纠错结果

### 阶段1: 确定性计数与矛盾登记
- 来源总数: 25→31 (补充6条)
- 唯一DOI: 31, 重复: 0
- 矛盾登记: 3条 (CONTRADICTION-001虚假覆盖, CONTRADICTION-002验证器假通过, CONTRADICTION-003 claim support膨胀)

### 阶段2: 8条全文审阅记录审计
| Source | 旧层级 | 新层级 | Claim Support | 状态 |
|--------|--------|--------|---------------|------|
| S20 Shpitser 2023 | FULLTEXT | FULLTEXT | CONFIRMED | ✅保留 |
| S21 Deliorman 2024 | FULLTEXT | FULLTEXT | CONFIRMED | ✅保留 |
| S16 Wang 2024 | FULLTEXT | FULLTEXT | CONFIRMED | ✅保留 |
| S10 Pearl 1995 | FULLTEXT | ABSTRACT | UNRESOLVED | ⚠️降级 |
| S13 Angrist 2001 | FULLTEXT | ABSTRACT | UNRESOLVED | ⚠️降级 |
| S15 Dudík 2014 | FULLTEXT | FULLTEXT | CONFIRMED | ✅保留 |
| S18 Webster-Clark 2025 | FULLTEXT | FULLTEXT | CONFIRMED | ✅保留 |
| S22 CONSORT 2010 | FULLTEXT | FULLTEXT | CONFIRMED | ✅保留 |

保留: 6条 | 降级: 2条 (S10 PDF编码失败, S13 AEA需JS)
CONFIRMED: 6条 | UNRESOLVED: 2条

### 阶段3: 4个零来源学科补充
| 学科 | 新增来源 | 干预/控制含义 |
|------|----------|--------------|
| Environmental Science | S26, S27 | 政策/技术部署的环境因果影响评估 |
| Finance | S28, S29 | 政策/市场干预的因果效应(IV方法) |
| Ecology | S30 | 生态管理行动的因果效应 |
| Agricultural Science | S31 | 管理实践(施肥/PGR)对作物产量的因果效应 |

### 阶段4: 接口方案重新裁决
Option C 保持推荐，但标记为 PROVISIONAL_INTERFACE_RECOMMENDATION_PENDING_CONSTITUTIONAL_REVIEW

### 阶段5: 验证器重写
新验证器 106-validator.py: 14项检查, 14/14 PASS
- 真实读取覆盖矩阵
- 交叉验证 source_id
- 检查全文证据卡必填字段
- 独立判定 claim_support_status
- 不硬编码 redline 结果

### 阶段6: 队列重排
原 106-118 → 107-119 (14项, 非破坏性)

## 五种覆盖口径（纠正后）
| 口径 | 数值 |
|------|------|
| ENUMERATED | 18/18 |
| SOURCE_PRESENT | 18/18 |
| ABSTRACT_SUPPORTED | 16/18 |
| FULLTEXT_SUPPORTED | 7/18 |
| CLAIM_SUPPORT_CONFIRMED | 7/18 |

## 红线状态
全部通过: Ψ₀/085 frozen v1/两张表/main/PR 均未修改
