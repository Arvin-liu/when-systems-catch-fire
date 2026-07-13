# 120 — Source Quality and Template Risk Audit

## IGNITION-20260709-120
**Date**: 2026-07-13  
**Executor**: QClaw (qclaw/pool-glm-5.2-night, reasoning: high)

---

## 1. Source Quality Assessment

### 1.1 Overall Statistics

| Metric | Value |
|--------|-------|
| Total sources | 84 |
| Unique source IDs | 84 |
| Crossref-verified DOIs | 11/13 attempted (84.6%) |
| Abstract-reviewed | 17 (20.2%) |
| Fulltext-reviewed | 0 (0%) |
| Peer-reviewed (via Crossref) | 11 |
| Preprints (arXiv) | ~50+ |
| Unknown review status | ~23 |

### 1.2 Quality Concerns

1. **High preprint ratio**: Over 60% of sources are arXiv preprints with unknown peer review status. While preprints are valuable for identifying paradigms, they cannot be treated as verified conclusions.

2. **Zero fulltext access**: No full text was read for any source. All claim_support_status is at most SUPPORTED_BY_ABSTRACT. This is the single largest quality limitation.

3. **Abstract source**: Abstracts were sourced from anysearch API snippets, not directly from publisher pages. Snippets may be truncated or altered by the search index.

4. **2026 preprints**: Several sources (S120-031, S120-033, S120-036, S120-037, etc.) are 2026 arXiv preprints that are very recent and may not have undergone community validation.

5. **DOI gaps**: Many arXiv preprints do not have registered DOIs, limiting Crossref verification. Only 13 DOI verifications were attempted.

### 1.3 Quality Strengths

1. **Source diversity**: 10 distinct source families ensure paradigm coverage breadth
2. **Crossref verification**: 11/13 DOIs verified successfully, confirming metadata accuracy for published works
3. **Honest tier assignment**: No source was promoted beyond its evidence level
4. **No key leakage**: Comprehensive API key scan found zero leaks

## 2. Template Risk Assessment

### 2.1 What is Template Risk?

Template risk refers to the danger that paradigm card fields were filled with template/generic values rather than source-specific content. This is a significant risk when processing 84 sources with limited per-source reading.

### 2.2 Template Risk Analysis

| Field | Template Risk | Mitigation |
|-------|---------------|------------|
| function_definition | HIGH - family-level template | Documented as family-level pattern |
| function_order | HIGH - family-level template | Documented as family-level pattern |
| input_domain | HIGH - family-level template | Documented as family-level pattern |
| output_domain | HIGH - family-level template | Documented as family-level pattern |
| carrier_type | MEDIUM - family-level template | Documented as family-level pattern |
| specification_language | MEDIUM - family-level template | Documented as family-level pattern |
| compiler_or_generator | MEDIUM - family-level template | Documented as family-level pattern |
| interpreter_or_runtime | MEDIUM - family-level template | Documented as family-level pattern |
| state_and_side_effects | MEDIUM - family-level template | Documented as family-level pattern |
| uncertainty_model | LOW - binary field | Simple classification |
| composition_rule | MEDIUM - family-level template | Documented as family-level pattern |
| equivalence_criterion | MEDIUM - family-level template | Documented as family-level pattern |
| validation_regime | LOW - simple classification | Clear per-family pattern |
| execution_trace | LOW - simple description | Clear per-family pattern |
| failure_boundary | LOW - simple description | Clear per-family pattern |
| version_and_provenance | LOW - simple description | Clear per-family pattern |
| what_the_paper_supports | MEDIUM - family-level template | Based on family pattern, not per-source reading |
| what_the_paper_does_not_support | MEDIUM - family-level template | Based on family pattern |
| abstract_snippet | LOW - actual content | 17 sources have real snippets |
| claim_support_status | LOW - derived from tier | Automatically computed |

### 2.3 Template Risk Summary

- **HIGH risk fields**: 3 (function_definition, function_order, input_domain, output_domain)
- **MEDIUM risk fields**: 8
- **LOW risk fields**: 9

The HIGH risk fields are explicitly documented as family-level patterns. This means that all sources within the same family share the same values for these fields. This is a deliberate design choice given the 84-source scale and 0 fulltext reviews, but it means that per-source differentiation is limited.

### 2.4 Recommendations

1. **IGNITION-121**: Fulltext review of top 20 sources should update all paradigm card fields with source-specific content
2. **Per-source differentiation**: Future runs should not use family-level templates for function_definition, function_order, input_domain, output_domain
3. **Abstract expansion**: More abstracts should be retrieved to increase ABSTRACT_REVIEWED count beyond 17

## 3. Forbidden Wording Compliance

12 forbidden phrases were defined and all output files were checked against them. No violations found.

Key forbidden patterns verified:
- No "weight similarity implies function equivalence"
- No "behavioral approximation proves equivalence"
- No "performance close enough to be equivalent"
- No "this paper's function corresponds to ignition function X"
- No "the paper concludes that" (without fulltext review)
- No "DOI exists therefore peer-reviewed"
- No "citation count indicates quality"
- No "model-generated summary of the paper"

## 4. Red Line Compliance

| Red Line | Status |
|----------|--------|
| Ψ₀ unmodified | ✅ Verified (SHA256 match) |
| 085 frozen v1 unmodified | ✅ Verified (SHA256 match) |
| No new function numbers | ✅ No new numbers added |
| No table modifications | ✅ Tables unchanged |
| No external function projection | ✅ All projections marked EXTERNAL_PARADIGM |
| No title-as-content-support | ✅ All claims require ABSTRACT_REVIEWED+ |
| No weight-similarity-as-equivalence | ✅ Equivalence axis enforced |
| No model-summary-as-conclusion | ✅ All abstracts marked as snippets |
| No PR merges/closes | ✅ No PRs touched |
| No API key leaks | ✅ All files scanned |

## 5. Overall Risk Rating

**MODERATE RISK** — The source collection is broad (84 sources, 10 families) but shallow (0 fulltext reviews, 17 abstract reviews). Template risk is high for paradigm card fields. The gap adjudications are appropriately conservative (all FIELD_ENHANCEMENT_ONLY) given the evidence limitations.
