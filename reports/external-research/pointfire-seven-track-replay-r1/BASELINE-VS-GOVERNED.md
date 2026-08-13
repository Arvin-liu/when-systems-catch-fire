# STEP03 blinded baseline versus governed replay

Status: COMPARISON_REPAIRED_PENDING_FRESH_ROLE_C_REVIEW

The comparison is between the independently frozen blinded baseline and the first governed pass. It asks what the governed process added to the research operation. It does not claim that the added process caused more true findings or that Pointfire is externally validated.

## Comparison table

| Dimension | Blinded baseline | Governed pass | Incremental result |
|---|---|---|---|
| Question framing | Answered the urban canopy question in ordinary research language and separated daytime, nighttime, LST, air temperature, and human exposure in prose | Locked the exact question, scope, endpoint definitions, source-family rule, causal ceiling, and outcome vocabulary before the pass | TRACEABILITY_ADDED |
| Source handling | Eight-source ledger with stable metadata, caveats, and retrieval date | Nine-family ledger with explicit family identity, evidence type, retrieval status, direct support, non-support, and access limits | SOURCE_BOUNDARY_ADDED |
| Measurement boundary | Already warned that LST, air temperature, and human exposure are not interchangeable and that canopy cover, volume, shade, presence, and generic vegetation differ | Reinforced the same boundary in a machine-readable policy, split canopy-cover claims, and added an explicit ABSTAIN record for mixed exposure substitution | MEASUREMENT_BOUNDARY_REINFORCED_NOT_UNIQUE |
| Causal reasoning | Already listed confounding, selection, reverse selection, timing, spatial mismatch, common support, spillover, and model limits | Added per-source causal-audit fields and retained NOT_IDENTIFIABLE for the universal causal question | CAUSAL_AUDIT_ADDED; CEILING_INCREMENT_UNDERDETERMINED |
| Contradictions and boundary cases | Already identified humid, nighttime, low-wind, high-humidity, and non-transpiring exceptions in narrative | Linked those conditions to source-specific records, added Tacoma day/night heterogeneity, and kept the stable-cross-setting claim DISPUTED | CONTRADICTION_TRACEABILITY_ADDED |
| Abstention | Already concluded conditionally and stated when causality could not be inferred | Used only preregistered outcomes and added actual ABSTAIN and SOURCE_NOT_RECOVERED claim rows | ABSTENTION_RECEIPT_ADDED |
| Reproducibility | Frozen baseline report and source ledger, but no shared claim machine ledger | Added source-ledger JSONL, claim-ledger JSONL, run manifest, and formal base tip | REPLAY_RECEIPT_ADDED |
| What was not added | No result showed that tree canopy has a universal, stable, causal effect across cities and endpoints | Same ceiling; no EPISTEMICALLY_ACCEPTED result and no external-validity claim | NO_EXTERNAL_VALIDITY_INCREMENT_PROVEN |

## Net assessment

The repaired governed pass added source-family role labels, per-source causal-audit fields, exposure-specific claim rows, a preregistration-aligned abstention receipt, and more recoverable provenance. Endpoint separation, alternative explanations, and the broad causal ceiling were already present in the blinded baseline. The architecture-level value is therefore MIXED_VALUE_WITH_COST or UNDERDETERMINED until a matched cost and information audit is completed. The pass did not add a causal estimate, a new source-independent fact, or a universal external-validity result.

The comparison also records a limitation: both passes rely primarily on observational studies, local monitoring, mechanistic modeling, and official guidance. The governed pass makes some limits more traceable; it does not remove them. Its contextual WMO and CDC records are not counted as substantive canopy source families.

## Decision

The replay may proceed to the next research phase after independent adversarial review of the initial governed pass. Any repair must update the source and claim ledgers without deleting the blinded baseline or rewriting a negative or boundary result. The status remains a candidate research artifact, not formal main, release, or acceptance.
