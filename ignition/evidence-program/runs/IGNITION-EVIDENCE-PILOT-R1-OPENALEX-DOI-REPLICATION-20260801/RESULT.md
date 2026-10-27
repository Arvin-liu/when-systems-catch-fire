# OpenAlex Independent Replication Pilot — First Run Result

Run: `IGNITION-EVIDENCE-PILOT-R1-OPENALEX-DOI-REPLICATION-20260801`  
Preregistration ancestor: `a830664c1add6a26b2b516a13769cdd71412eda2`  
Claim ceiling: **Cross-source bibliographic metadata consistency only; no paper-content, scientific-truth, Pointfire-physics, MCF, PSD or ARN validation.**

## Bounded result

The locked population contained 117 DOI records. The first run obtained 117 HTTP 200 JSON responses and preserved one raw response per record. One declared duplicate was retained for audit and excluded from the primary denominator, leaving 116 primary records.

| Class | Primary count | Rate |
|---|---:|---:|
| `SUPPORTED_WITHIN_SCOPE` | 101 | 87.0690% |
| `PARTIALLY_SUPPORTED_WITH_IDENTIFIED_MISMATCHES` | 8 | 6.8966% |
| `CONTRADICTED_WITHIN_SCOPE` | 0 | 0.0000% |
| `NULL_OR_INCONCLUSIVE` | 7 | 6.0345% |
| `TEST_INVALID_OR_ABORTED` | 0 | 0.0000% |

The seven null/inconclusive primary records are preserved rather than averaged away: four returned multiple exact normalized-DOI works and three returned no exact DOI match. The nine partial records are itemized; the primary partial count is eight after duplicate exclusion, all due to the preregistered one-year online/print ambiguity. No hard contradiction was observed in this first run.

## Evidence and limits

- Raw responses: `data/operations/iterations/110/openalex/first-run-20260801/raw/`.
- Acquisition manifest: `data/operations/iterations/110/openalex/first-run-20260801/source-manifest.jsonl`.
- Run manifest: `data/operations/iterations/110/openalex/first-run-20260801/run-manifest.jsonl`.
- First-run adjudication: `data/operations/iterations/110/openalex/first-run-20260801/adjudication.jsonl`.
- No registry correction or corrected rerun was performed.
- This result does not validate paper contents, cited conclusions, scientific truth, Pointfire physics, MCF, PSD, ARN, causality or maturity promotion.
