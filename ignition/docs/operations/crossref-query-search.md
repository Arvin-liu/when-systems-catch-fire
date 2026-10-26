# Crossref topic query search

`research.search_crossref_query` is an optional, default-off adapter for discovering Crossref Works from one caller-supplied public query. It makes one request to the versioned `/v1/works` endpoint, asks Crossref for at most ten rows and a limited field projection, and returns DOI and bibliographic metadata only.

Run only after the caller has separately approved sending the non-sensitive query to Crossref and the typed route allows `api.crossref.org`:

```sh
printf '%s' '{"query":"artificial intelligence healthcare","max_results":5}' \
  | python3 -B ignition/tools/toolbox_crossref_query_search.py --stdin --allow-public-network
```

The adapter uses the public pool: no `mailto`, account email, key, `Authorization` header or billing credential is sent. Crossref's July 2026 guidance sets list-query traffic to one request per second with one concurrent request for the public pool; the wrapper makes one request per invocation, while callers must coordinate the rate across processes. It follows no redirects, retries nothing, caps the response at 512 KiB and seven seconds, and records the selected rate-limit headers when present. [REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), [API version guidance](https://www.crossref.org/documentation/retrieve-metadata/api-versioning/), [July 2026 rate-limit guidance](https://community.crossref.org/t/refining-rest-api-limits-for-improved-stability-and-reliability/16137).

The `select` projection omits Crossref abstracts, references, links and arbitrary URLs. The result order and cited-by count are provider fields; neither establishes human relevance, evidence strength, coverage, citation correctness or scientific quality. Crossref metadata comes from member deposits and trusted sources, can be partial, and is distinct from OpenAlex, PubMed, Europe PMC and arXiv source scopes.

Do not use this route for confidential or health-identifying queries, systematic-review completeness, full-text retrieval, authoritative correction/retraction adjudication, or scientific decisions. Prefer local source navigation when it already satisfies the task; use an exact-identifier adapter when the DOI is already known. If the provider is unavailable or the route is not authorized, retain the explicit failure or do not invoke the adapter.
