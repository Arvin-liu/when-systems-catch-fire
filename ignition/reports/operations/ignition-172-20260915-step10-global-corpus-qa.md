# Task172 Step10 — global corpus QA

Status: `PASS_WITH_EXPLICIT_DEFICITS`

This is a repository-local integrity and metadata-governance audit. It does not promote scholarly metadata to evidence, establish external truth, or treat a provider taxonomy as UNESCO authority.

## Exact counts

- UNESCO primary authority: 24/24 fields, 245/245 four-digit disciplines, and 2,178 primary six-digit subdisciplines.
- Every primary four-digit discipline has 8 metadata links; minimum and maximum are both 8.
- Global corpus: 1,802 physical metadata records and 1,960 many-to-many discipline links.
- Missing primary taxonomy anchors: 0; invalid hierarchy: 0; orphan links: 0.
- Duplicate physical IDs: 0; duplicate normalized identity keys: 0; duplicate discipline-link keys: 0.

## Explicit deficits and warnings

- The corpus remains metadata-only: no abstract, full text, or raw provider response is persisted, and all evidence/proof/replication promotion flags remain false.
- Language and rights-status fields are absent on all 1,802 records. License/OA signals occur on 399 records but are not content authorization.
- Nine records carry `UPDATED`; they remain retained and manual-review-bound. No corrected/retracted row was promoted as ordinary positive evidence.
- Sixty-eight records have no title; three have unavailable publication year/date, including one `9999` sentinel; 1,203 lack `publication_date`.
- Regional, language, DOI, and low-DOI humanities/law/arts/philosophy bias could not be measured from this snapshot. Provider counts are Crossref 798, OpenAlex 524, OpenAIRE 405, and PubMed E-utilities 75. Provider failure is not “no literature.”

The deficits are explicit metadata-quality and fairness limitations, not a systemic taxonomy, dedupe, rights-boundary, or projection blocker. The machine record is `data/operations/iterations/172/step10-global-corpus-qa.json`.
