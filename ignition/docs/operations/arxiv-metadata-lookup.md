# arXiv metadata lookup candidate

This default-off experimental tool accepts exactly one modern arXiv identifier and makes one bounded GET to `export.arxiv.org/api/query`. The arXiv API's `id_list` parameter accepts a comma-delimited list of arXiv IDs; this adapter narrows that contract to one caller-supplied ID. See the [arXiv API user's manual](https://info.arxiv.org/help/api/user-manual.html).

The adapter returns the provider entry ID/version, title, author names, publication/update timestamps, categories, journal reference, and DOI when supplied. It does not return abstracts, article files, or full text. The selected output supports metadata resolution only. It does not prove that an article is authentic, supports a claim, is scientifically correct, or has been accepted by a venue.

The source-bound origin is Workbench PR #81 at `9dae5a0d73f66c8b0b6d01c0c6ca14fad34cc03a`, `sources/IDEASCIENTIST-RESEARCH-IDEATION-CANDIDATE-R0.json`; its cited primary source is arXiv:2610.04074. No IdeaScientist code, model, vault data, or paper text is reused. The target use case is the blueprint's `cited_id_must_resolve` precondition, separated from evidence support or scientific judgment.

## Limits and rollback

- Only modern `YYMM.NNNN[N]` identifiers with optional lowercase `vN` are accepted; legacy slash-form identifiers need a separate tested adapter.
- The exact host is `export.arxiv.org`; redirects are rejected, response bodies are capped at 128 KiB, and network invocation requires the per-call `--allow-public-network` flag.
- Callers must explicitly permit sending the identifier to arXiv. Router proposals require both the candidate ID and the exact host allowlist and never authorize execution.
- Crossref and OpenAlex remain useful for DOI-based metadata and provider-specific fields. This adapter is scoped to direct arXiv-ID resolution; comparative latency, completeness, and effort remain unmeasured.
- Rollback: remove this candidate card, tool, focused test, evidence, and this note; regenerate the identity-card projections. No current registry, default route, or existing source tool is modified.
