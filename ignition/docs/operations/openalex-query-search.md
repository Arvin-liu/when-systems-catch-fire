# OpenAlex bounded query search

`research.search_openalex_query` is an optional, default-off toolbox adapter over the existing OpenAlex client. It discovers Works from one caller-supplied public query and returns at most ten provider-ranked metadata records. It does not return abstracts, full text, or the raw query.

Run only after the caller has explicitly approved sending the non-sensitive query to OpenAlex and the task route allows `api.openalex.org`:

```sh
printf '%s' '{"query":"artificial intelligence healthcare","max_results":5}' \
  | python3 -B ignition/tools/toolbox_openalex_query_search.py --stdin --allow-public-network
```

The input has exactly `query` and `max_results`; the latter must be an integer from 1 through 10. The adapter sends one HTTPS GET, does not send a key or email, follows no redirects, retries nothing, and limits the response to 512 KiB and seven seconds. It records bounded usage headers when OpenAlex provides them. The legacy OpenAlex CLI remains unchanged; this mode avoids its default placeholder `mailto` and abstract output.

OpenAlex's Works `search` includes title, abstract, full text, and keywords. Its default order is provider relevance ranking, which incorporates text similarity, a capped citation-count contribution, and a keyword bonus. The returned `relevance_score` is a provider ranking field; it is not a human relevance judgment or a scientific-quality score. The adapter does not use semantic search, reranking, paging, an API key, or an account.

OpenAlex documents keyless rate limits and says search requests consume usage credits. This adapter never provides credentials, and the smoke receipt records the provider's usage headers; an account-specific monetary cost is not established here. Do not use it for sensitive queries, systematic-review completeness, bulk export, or scientific adjudication. Prefer the checked-out local evidence index when it already covers the task; choose Europe PMC or arXiv when those source-specific corpora are required.

The existing `openalex_client.search()` already provides provider search, so this toolbox candidate is a bounded safe route to an existing provider capability rather than a new search engine. Its final source binding and public smoke are recorded in `ignition/data/operations/toolbox-openalex-query-search-source-binding-r1.json` and `ignition/data/operations/toolbox-openalex-query-search-real-task-evidence-r1.json`; the earlier pre-hardening smoke remains preserved as R0. Same-task source-scope observations are in `ignition/data/operations/toolbox-arxiv-query-search-c1-evidence-r1.json`. They do not establish comparative relevance, recall, scientific value, or an account-level monetary charge.
