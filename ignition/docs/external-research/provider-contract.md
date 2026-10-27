# 104 Provider Contract

## Provider 接口定义

### 1. Lead Search Provider
- **Role**: 发现检索线索（LEAD_DISCOVERED）
- **Current Implementation**: anysearch_client.py (free-key, `POST https://api.anysearch.com/v1/search`)
- **Authority Level**: LOW — 仅作为线索来源，不得作为论文存在或内容支持的权威
- **Output**: title, url, snippet, content (raw text for DOI extraction)
- **Post-Processing**: Extract DOI → send to Metadata Resolver

### 2. Metadata Resolver
- **Role**: 验证 DOI/ISBN/arXiv/PubMed 等标识符并获取元数据（IDENTIFIER_RESOLVED → METADATA_VERIFIED）
- **Current Implementation**: Crossref API (`https://api.crossref.org/works/{doi}`)
- **Authority Level**: MEDIUM — Crossref 是 DOI 注册权威，元数据可信
- **Output**: title, authors, year, venue, publisher, type, ISSN
- **Limitation**: 只能验证元数据，不能验证论文内容

### 3. Content Retriever
- **Role**: 获取摘要或全文（ABSTRACT_REVIEWED / FULLTEXT_REVIEWED）
- **Current Implementation**: NOT_CONFIGURED — 088-B 使用模型知识填充摘要，未从出版商页面获取
- **Required**: Open access full text, publisher API, institutional repository
- **Authority Level**: HIGH（for content support claims）
- **Status**: ADAPTER_NOT_CONFIGURED

### 4. Retraction/Correction Checker
- **Role**: 检查撤稿、更正或可信度警报（RETRACTED_OR_CORRECTED）
- **Current Implementation**: NOT_CONFIGURED — 088-B 未主动查询 Retraction Watch
- **Required**: Retraction Watch API (`https://api.crossref.org/works?filter=type:retraction`)
- **Authority Level**: HIGH
- **Status**: ADAPTER_NOT_CONFIGURED

### 5. Citation Formatter
- **Role**: 标准化引用格式
- **Current Implementation**: NOT_CONFIGURED — 088-B 手动格式化
- **Required**: CSL (Citation Style Language) processor
- **Authority Level**: LOW (formatting only)
- **Status**: ADAPTER_NOT_CONFIGURED

## Provider Capability Matrix

| Provider | Status | Endpoint | Auth Required | Rate Limit | Replayable |
|----------|--------|----------|---------------|------------|------------|
| Lead Search | ACTIVE | api.anysearch.com/v1/search | No | Unknown | Yes (free-key) |
| Metadata Resolver | ACTIVE | api.crossref.org/works/{doi} | No (polite email recommended) | ~50 req/s | Yes |
| Content Retriever | NOT_CONFIGURED | N/A | N/A | N/A | N/A |
| Retraction Checker | NOT_CONFIGURED | N/A | N/A | N/A | N/A |
| Citation Formatter | NOT_CONFIGURED | N/A | N/A | N/A | N/A |

## 安全规则
- API key 不得写入代码、配置文件或 Git
- key 通过环境变量配置
- key 缺失时安全降级，不得伪造结果
- NOT_CONFIGURED 的 provider 只允许建立明确占位适配器，不得假装可用
