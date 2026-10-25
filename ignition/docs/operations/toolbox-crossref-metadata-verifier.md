# Crossref Metadata Verifier 0.2.0

`research.verify_crossref_metadata` compares up to ten caller-supplied DOI, expected-title, and expected-year records with the fixed Crossref Works API. Version 0.2.0 also projects bounded Crossref `update-to`, `updated-by`, and typed `relation` identifiers from the same response, so relation metadata adds no second request.

The relation projection preserves field status (`NOT_REPORTED`, `PRESENT_EMPTY`, `PRESENT_NONEMPTY`, or `MALFORMED`), reported counts, omitted counts, and truncation. It returns only bounded identifiers and short provider fields. It does not return abstracts, follow related identifiers, or retrieve article pages. URL-shaped identifiers are omitted. Each relation type is capped at 32, general relation rows at 50, and each update direction at 25 rows per record.

Example input:

```json
{"records":[{"source_id":"record-1","doi":"10.1000/example","expected_title":"Example title","expected_year":2024}]}
```

Run with `--stdin --allow-public-network`. The tool sends a read-only request only to `api.crossref.org`, blocks redirects, caps request/response size and duration, writes JSON to stdout, and performs no repository writes. Its optional identity remains default-off in adaptive routing; the planner requires both explicit candidate inclusion and an exact allowed host, and does not authorize the call.

Crossref update and relation metadata may overlap with the specialized PubMed Comments/Corrections reader, but the provider fields and identifier scope differ. Current comparison evidence is insufficient to claim replacement, broad superiority, complete relationship coverage, or lower cost. Keep both optional while matched real-task comparisons remain open.

The result describes metadata returned by Crossref at retrieval time. It does not authenticate the provider, establish that a relation is complete or correct, evaluate article content, determine current retraction status, or support a scientific claim. A missing or empty field is not evidence that no relation exists.
