# STEP03 blinded baseline versus governed replay

Status: COMPARISON_COMPLETE_WITHOUT_EXTERNAL_VALIDITY_UPGRADE

The comparison is between the independently frozen blinded baseline and the first governed pass. It asks what the governed process added to the research operation. It does not claim that the added process caused more true findings or that Pointfire is externally validated.

## Comparison table

| Dimension | Blinded baseline | Governed pass | Incremental result |
|---|---|---|---|
| Question framing | Answered the urban canopy question in ordinary research language and separated daytime, nighttime, LST, air temperature, and human exposure in prose | Locked the exact question, scope, endpoint definitions, source-family rule, causal ceiling, and outcome vocabulary before the pass | TRACEABILITY_ADDED |
| Source handling | Eight-source ledger with stable metadata, caveats, and retrieval date | Nine-family ledger with explicit family identity, evidence type, retrieval status, direct support, non-support, and access limits | SOURCE_BOUNDARY_ADDED |
| Measurement boundary | Warned that LST, air temperature, and human heat are not interchangeable | Made endpoint separation a machine-readable policy and typed claim-level dispositions | MEASUREMENT_BOUNDARY_ADDED |
| Causal reasoning | Listed confounding, selection, reverse selection, timing, spatial mismatch, common support, spillover, and model limits | Applied those limits to individual claims and retained NOT_IDENTIFIABLE for the universal causal question | CLAIM_CEILING_MADE_EXPLICIT |
| Contradictions and boundary cases | Identified humid, nighttime, low-wind, high-humidity, and non-transpiring exceptions in narrative | Recorded disputed or contradicted claims and linked them to boundary source families | CONTRADICTION_VISIBILITY_ADDED |
| Abstention | Concluded conditionally and stated when causality could not be inferred | Added typed outcomes such as DISPUTED, CONTRADICTED, PARTIALLY_SUPPORTED, and NOT_IDENTIFIABLE | ABSTENTION_TYPED |
| Reproducibility | Frozen baseline report and source ledger, but no shared claim machine ledger | Added source-ledger JSONL, claim-ledger JSONL, run manifest, and formal base tip | REPLAY_RECEIPT_ADDED |
| What was not added | No result showed that tree canopy has a universal, stable, causal effect across cities and endpoints | Same ceiling; no EPISTEMICALLY_ACCEPTED result and no external-validity claim | NO_EXTERNAL_VALIDITY_INCREMENT_PROVEN |

## Net assessment

The governed pass added a clearer audit surface, sharper endpoint separation, more visible contradictions, typed abstention, and a lower risk of silently pooling heterogeneous evidence. It did not add a causal estimate, a new source-independent fact, or a universal external-validity result. The strongest demonstrated increment is process and claim-boundary discipline.

The comparison also records a limitation: both passes rely primarily on observational studies, local monitoring, mechanistic modeling, and official guidance. The governed pass makes that limitation easier to see; it does not remove it.

## Decision

The replay may proceed to the next research phase after independent adversarial review of the initial governed pass. Any repair must update the source and claim ledgers without deleting the blinded baseline or rewriting a negative or boundary result. The status remains a candidate research artifact, not formal main, release, or acceptance.
