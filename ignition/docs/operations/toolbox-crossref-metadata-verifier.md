# Crossref Metadata Verifier 0.3.0

`research.verify_crossref_metadata` compares up to ten caller-supplied DOI, expected-title, and expected-year records with the fixed Crossref Works API. Version 0.2.0 also projects bounded Crossref `update-to`, `updated-by`, and typed `relation` identifiers from the same response, so relation metadata adds no second request.

Version 0.3.0 adds a bounded projection of the same Work response's optional `reference` list. It returns up to 25 entries per DOI, preserving a valid bare DOI and selected short citation fields such as title, author, year, journal, and page. It distinguishes a missing field from an empty or malformed one and reports provider count, omitted rows, invalid entries, and truncation. Absolute HTTP(S) URL-shaped strings in citation fields are omitted. The tool does not resolve referenced DOIs, retrieve cited articles, or judge whether a citation is correct or complete.

The relation projection preserves field status (`NOT_REPORTED`, `PRESENT_EMPTY`, `PRESENT_NONEMPTY`, or `MALFORMED`), reported counts, omitted counts, and truncation. It returns only bounded identifiers and short provider fields. It does not return abstracts, follow related identifiers, or retrieve article pages. URL-shaped identifiers are omitted. Each relation type is capped at 32, general relation rows at 50, update directions at 25 rows, and deposited reference entries at 25 rows per record.

One purposively selected DOI in the real-task record returned 40 provider-reported references; this adapter projected 25, reported 15 omitted, and marked the output truncated. This single record does not estimate reference coverage or correctness; the bounded response and hashes are recorded in [the real-task evidence](../../data/operations/toolbox-crossref-references-real-task-evidence-r0.json). Crossref says reference deposits are optional. A missing or empty `reference` field therefore does not establish that a work has no references. Returned entries are Crossref-deposited metadata at retrieval time, not a verified or complete bibliography. See [Crossref's reference deposit documentation](https://www.crossref.org/documentation/schema-library/markup-guide-metadata-segments/references/) and [REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/).

Example input:

```json
{"records":[{"source_id":"record-1","doi":"10.1000/example","expected_title":"Example title","expected_year":2024}]}
```

Run with `--stdin --allow-public-network`. The tool sends a read-only request only to `api.crossref.org`, blocks redirects, caps request/response size and duration, writes JSON to stdout, and performs no repository writes. Its optional identity remains default-off in adaptive routing; the planner requires both explicit candidate inclusion and an exact allowed host, and does not authorize the call.

Crossref update and relation metadata may overlap with the specialized PubMed Comments/Corrections reader, but the provider fields and identifier scope differ. The existing OpenAlex adapter does not expose reference lists; it returns its own Work, OA, and location fields. No same-task evidence currently justifies replacing either provider or claiming complete reference coverage. Keep the candidate optional and default-off.

The result describes metadata returned by Crossref at retrieval time. It does not authenticate the provider, establish that a relation is complete or correct, evaluate article content, determine current retraction status, or support a scientific claim. A missing or empty field is not evidence that no relation exists.
