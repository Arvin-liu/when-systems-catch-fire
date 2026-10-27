# IGNITION-172 Step08 — UNESCO/provider metadata pilot

This logical step follows Gate T, Gate R and the Gate C policy/provider lock. The frozen parent is `36a1ed4c0e5b91598b5a4fada4bec1539ccc106b` on the existing Task172 branch and Draft PR #218.

- Gate T authority: the 1988 UNESCO primary parse, 24 fields / 245 four-digit disciplines / 2178 six-digit subdisciplines. The 248 mirror, 250 local inventory and 2183 historical secondary counts remain discrepancy values, not silent substitutes.
- Pilot scope: one Gate T four-digit discipline seed from each of the 24 fields; provider requests were bounded to OpenAlex, Crossref and OpenAIRE, with PubMed E-utilities only for the medical field.
- Crosswalk status: `QUERY_SEED_ONLY_NO_DIRECT_PROVIDER_EQUIVALENCE`; provider taxonomy identifiers are not copied into UNESCO identity, and every target remains manual-review-required.
- Results: 365 sanitized metadata candidates admitted as `GENERAL_KNOWLEDGE_REFERENCE` / `SCHOLARLY_METADATA`; no content body was persisted, no scientific relevance was adjudicated, and no evidence/proof/replication promotion occurred.
- Dedupe: normalized DOI first, then namespaced provider ID, retaining provider provenance and unresolved collisions.
- Failure semantics: provider errors or empty results are provider-health events and are not no-literature conclusions.

Decision: `STEP08_PILOT_PASS_FOR_METADATA_PIPELINE; NO_DIRECT_PROVIDER_EQUIVALENCE; NO_SCIENTIFIC_EVIDENCE_PROMOTION`. The 24-field Formal ingestion lanes may now prepare under the one-field/one-commit gate, subject to exact-head CI and the unchanged Draft/open lifecycle ceiling.
