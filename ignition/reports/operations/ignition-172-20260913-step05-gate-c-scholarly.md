# IGNITION-172 Step05 — Gate C scholarly admission policy

Gate C is a policy lock downstream of Gate T and Gate R at Formal head `998b5654248b41a8982d0674bf0368b400b65eec`. It freezes scholarly-admission semantics, provider roles, rights handling, correction/retraction handling, conservative deduplication, and a synthetic cross-domain pilot. It does not establish external scholarly truth.

- Taxonomy authority: the locked 1988 UNESCO primary document, with 24 fields / 245 four-digit disciplines / 2178 six-digit subdisciplines.
- Gate R precondition: the bounded routing schema and 750-row precision pilot remain manual-review-only and are not promoted into evidence or corpus truth.
- Admission mode: `METADATA_ONLY`; accepted identifiers are DOI or namespaced provider-stable IDs.
- Provider roles: OpenAlex for broad metadata discovery, Crossref for DOI/update provenance, OpenAIRE for open-research relations, and PubMed E-utilities for biomedical index/correction relations. None is an evidence-promotion channel.
- Rights: factual metadata and linkouts may be retained; unknown rights block abstract/full-text persistence; open-access status is not itself a license.
- Corrections/retractions: original records remain linked and auditable; corrected, retracted, expression-of-concern, updated, and unknown states never create positive evidence.
- Deduplication: normalized DOI, then namespaced provider ID, then conservative title/first-author/year candidate matching; unresolved collisions remain separate.
- Cross-domain pilot: four domain buckets, target 5 per domain with an allowed range of 5–12, synthetic policy cases only.
- Live scholarly retrieval, metadata-row admission, abstract/full-text persistence, and mass Formal ingestion: disabled (`0` / `false`).

Decision: Gate C passes for the scholarly-admission policy and provider-role lock only. No scholarly corpus has been admitted, no external source has been adjudicated as truth, and no 24-field Formal ingestion is authorized until this step's own exact-head CI succeeds.
