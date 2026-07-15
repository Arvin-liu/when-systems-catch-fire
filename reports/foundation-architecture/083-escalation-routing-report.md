# 083 Escalation Routing Report

**Date:** 2026-07-13  
**Task:** IGNITION-20260709-083

## Overview

506 escalation records from 081 were re-classified in 083 using stricter criteria based on claim_type, proof_status, and logic_form.

## Classification Categories

| Category | Count | Criteria |
|----------|-------|----------|
| MAX_REQUIRED | 353 | Mathematical propositions, structural analogies, isomorphism/equivalence claims requiring max-level adjudication |
| GLM_HIGH_CAN_RESOLVE | 150 | Source scope, wording, definitions, ordinary hidden premises — resolvable by GLM-5.2 high |
| NO_ESCALATION_NEEDED | 3 | Keyword-triggered but conservative wording already sufficient |
| **Total** | **506** | |

## Comparison with 082 Original

| Category | 082 Original | 083 Recomputed | Delta |
|----------|-------------|---------------|-------|
| MAX_REQUIRED | 343 | 353 | +10 |
| GLM_HIGH_CAN_RESOLVE | 140 | 150 | +10 |
| NO_ESCALATION_NEEDED | 23 | 3 | -20 |
| **Total** | **506** | **506** | **0** |

## Rationale for Reclassification

1. **NO_ESCALATION_NEEDED reduction (-20):** 082 used loose criteria; many items classified as NO_ESCALATION_NEEDED still had scope ambiguities that warrant at least GLM_HIGH_CAN_RESOLVE processing.

2. **MAX_REQUIRED increase (+10):** Items with proof_status=REQUIRES_HIGHEST_MODEL_VERIFICATION or isomorphism/equivalence in logic_form were moved to MAX_REQUIRED.

3. **GLM_HIGH_CAN_RESOLVE increase (+10):** Items that were in NO_ESCALATION_NEEDED but needed at least scope clarification were moved here.

## GLM_HIGH_CAN_RESOLVE Processing

150 items processed with:
- Source-specific escalation reasons (replacing generic "Cross-domain unified theorem claim")
- Conservative wording adjustments to forbidden_wording
- Confidence recalibrated by claim type
- All marked as resolved by 083-GLM-5.2-high

## NO_ESCALATION_NEEDED Items

3 items confirmed as truly not needing escalation:
- Conservative wording already restricts scope to framework-internal
- Keyword triggered by source text terms, not by adjudication content

## Impact on 084

- 353 items require max-level adjudication
- 15 batches of ≤25 recommended
- Priority ordering ensures proof equivalence (P1) and isomorphism (P4) items are processed first
