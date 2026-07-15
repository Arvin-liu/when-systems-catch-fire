# 120 — Provider and Tool Audit

## Task
IGNITION-20260709-120: Function Paradigm Atlas and Function OS Architecture Candidates

## Date
2026-07-13

## Executor
QClaw (qclaw/pool-glm-5.2-night, reasoning: high)

## Tools Used

### 1. anysearch API
- **Status**: Available ✓
- **API Key**: Loaded from `~/.zshrc` (`ANYSEARCH_API_KEY`)
- **Endpoint**: `https://api.anysearch.com/v1/search`
- **Usage**: Searched all 10 source families + supplementary queries
- **Key prefix**: `as_sk_15...` (no full key exposed in any output file)
- **Limitation**: Results returned without DOI fields in most cases; DOI verification required separate Crossref calls

### 2. Crossref API
- **Status**: Available ✓
- **Endpoint**: `https://api.crossref.org/works/{DOI}`
- **Usage**: Verified 13 DOIs, 11 successful (84.6% success rate)
- **Failures**: 
  - `10.1145/3406088.3406091` (404 - DOI format may differ)
  - `10.1017/S0956796815000120` (404 - Cambridge journal DOI format issue)
- **Rate limiting**: 0.5s delay between requests, no rate limit hits

### 3. web_search
- **Status**: Available ✓
- **Provider**: yuanbao
- **Usage**: Supplementary search for source families
- **Limitation**: Results include non-academic content (blog posts, tutorials); less useful than anysearch for academic sources

### 4. web_fetch
- **Status**: PARTIALLY BLOCKED ✗
- **Issue**: `arxiv.org` URLs are blocked ("resolves to private/internal/special-use IP address")
- **Impact**: Could not fetch arXiv abstract pages directly; relied on anysearch snippets for abstract content
- **Workaround**: Used anysearch snippet text as proxy for abstract content

### 5. 104 Evidence Tier Schema
- **Status**: Available ✓
- **Path**: `data/external-research/104-evidence-tier-schema.md`
- **Usage**: Applied tier definitions (LEAD_DISCOVERED → METADATA_VERIFIED → ABSTRACT_REVIEWED → FULLTEXT_REVIEWED → CLAIM_SUPPORT_CONFIRMED)

### 6. 106 Validator
- **Status**: Available ✓
- **Path**: `data/external-research/106-105-correction/106-validator.py`
- **Usage**: Referenced for validator design patterns

## Evidence Tier Distribution

| Tier | Count | Percentage |
|------|-------|-----------|
| ABSTRACT_REVIEWED | 17 | 20.2% |
| METADATA_VERIFIED | 67 | 79.8% |
| FULLTEXT_REVIEWED | 0 | 0% |
| CLAIM_SUPPORT_CONFIRMED | 0 | 0% |

## Key Limitations

1. **No fulltext access**: arXiv blocked by web_fetch, publisher pages require institutional access
2. **Abstract sources**: Abstracts sourced from anysearch snippets, not directly from publisher pages
3. **DOI coverage**: Many arXiv preprints do not have registered DOIs; Crossref verification limited to published works
4. **Currency**: Several sources are 2026 preprints that may not have completed peer review

## Security

- No API keys, tokens, or credentials appear in any output file
- API key loaded via `source ~/.zshrc` and referenced only by environment variable
- All output files scanned with regex patterns for common API key formats
