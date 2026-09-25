# Agent D — Measurement and preregistration proposal

Read-only proposal. No repository files were changed.

## Case endpoint

For each evaluator, condition, case family, and conversation replicate, score METHOD_DEPENDENCY_SUCCESS as binary. Freeze per case the allowed target decision/disposition, candidate/action, required method-link IDs, boundary/precondition, discriminating observation or measurement, and forbidden claims.

Score true only when the visible answer states an allowed decision, connects the required links to that decision with source locators, respects the target boundary, states the target observation/interpretation/disposition, and avoids forbidden claims and all critical errors. Otherwise score false. Score the observable answer and source use only; do not require hidden reasoning.

Preserve FACTUAL_FIDELITY, EVIDENCE_BOUNDARY, DECISION_QUALITY, and REFERENCE_INTEGRATION on their existing 0–2 scales. Keep lineage, material use, and critical flags as secondary measures.

## Replication and thresholds

Conversation is the independent unit; six cases are nested. For each evaluator and family-by-replicate cell, let M, L, F, and S be binary endpoint results for METHOD, LINKLESS, FACTS, and SKILL:

- METHOD_LINKLESS_WIN = M and not L.
- METHOD_CONTRAST_SUCCESS = M and not L and (not F or not S).
- A family is replicated when METHOD_CONTRAST_SUCCESS appears in at least two of three conversations.

Apply the command's thresholds separately to each evaluator: SUPPORTED requires M success at least 16/18, at least five replicated families, at least four families with all three METHOD-over-LINKLESS wins, and zero listed METHOD critical errors across 18 records. PARTIAL requires M success at least 14/18, at least three replicated families, and at least 10/18 matched primary contrasts. Otherwise NOT_SUPPORTED. Report all raw conversation vectors and matched outcomes; do not call 18 contrasts independent replicates or run significance tests.

## Ambiguity to resolve before freeze

PARTIAL's phrase “METHOD outperforms LINKLESS” can mean METHOD_LINKLESS_WIN or the stricter METHOD_CONTRAST_SUCCESS. Resolve this before freeze, name the count explicitly, and report the other count too. Define the zero-critical-error denominator as the 18 METHOD records per evaluator.

## Evidence boundary

Task216 generic scores and bounded successes were near ceiling; METHOD had no stable advantage over its link-broken comparison. Runtime attestations were unavailable. The primary endpoint must therefore be method-dependency-specific, with no causal claim.
