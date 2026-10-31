# Crossref 引文候选匹配器 / Crossref Citation Candidate Matcher

## Scope

`research.match_crossref_citation` sends one caller-supplied public, non-sensitive bibliographic citation to the fixed Crossref REST API v1 Works endpoint using `query.bibliographic`. It requests two rows, the provider-recommended small result set for ordinary citation matching, and projects a bounded set of bibliographic fields plus any relevance scores returned by Crossref. It never chooses or verifies a DOI.

This is a specialized optional lookup. `research.search_crossref_query` remains useful for public topic discovery over general Crossref query fields. `research.match_pubmed_citation` remains useful when the input is a structured PubMed citation and a PMID result is required. `research.verify_crossref_metadata` checks caller-known DOI metadata and does not resolve a missing DOI. These are different output contracts; no source is universally preferred.

## Input and output

Input is UTF-8 JSON with exactly one `citation` string, at most 2,048 characters and 4,096 UTF-8 bytes. The string must be public and non-sensitive because the network-enabled call transmits it to Crossref. The output contains a citation digest, request and response digests, retrieval time, HTTP/acquisition status, rate-limit headers when present, and at most two ranked Crossref candidate projections. Raw citation text, abstracts, references, arbitrary URLs, and full responses are not returned.

`top_two_score_status` only reports whether Crossref returned equal or different scores for the first two rows. Result order, score, DOI presence, and a single row do not establish a correct match. A human or a separate authorized source check must confirm any DOI before use.

## Permissions and limits

- Mode: `READ_ONLY_RUN`; no filesystem writes, secrets, billing, or external actions.
- Network: one HTTPS GET to `api.crossref.org`, only after the caller passes `--allow-public-network`; redirects and other hosts are rejected.
- No `mailto` value, API key, retry, cache write, or hidden second request is used. The request stays in the public pool; callers must coordinate list-query rate/concurrency limits and stop on HTTP 429.
- Input is capped at 4 KiB, response at 128 KiB, timeout at five seconds, and response-read deadline at eight seconds. These are per-invocation resource bounds, not task-duration limits.
- No third-party runtime dependency; Python standard library only. Monetary cost is not measured and remains `UNKNOWN`.

## Invocation

```sh
python3 -B ignition/tools/toolbox_crossref_citation_matcher.py --stdin --allow-public-network < citation.json
```

The `--allow-public-network` flag is required even when the route planner has proposed the tool. Routing proposes a candidate; the caller still decides whether the exact citation may be transmitted. If unavailable, rate-limited, malformed, or ambiguous, preserve that status and use a separately authorized source or manual reference review.

## Evidence and comparison

The focused tests cover exact input shape, duplicate JSON keys, malformed provider payloads, redirects, rate limiting, response limits, no hidden network request, privacy-preserving output, and the default-off route.

One paired public task used the same title-and-year citation with two rows on each call. `query.bibliographic` returned the previously recorded DOI `10.1007/s10489-024-05338-9` at rank 1; the general `query` adapter returned two different works and did not include that DOI in its top two. This single interface-level observation supports keeping both routes by task scope: the citation matcher is optional for citation-shaped lookup, while general query search remains useful for topic discovery. It does not establish general citation accuracy, recall, provider quality, source authenticity, scientific support, cost, or reliability. The comparison and bounded task result are recorded in [`toolbox-crossref-citation-matcher-c1-evidence-r0.json`](../../data/operations/toolbox-crossref-citation-matcher-c1-evidence-r0.json) and [`toolbox-crossref-citation-matcher-real-task-evidence-r0.json`](../../data/operations/toolbox-crossref-citation-matcher-real-task-evidence-r0.json); the offline default-off route replay is in [`toolbox-crossref-citation-matcher-route-evidence-r0.json`](../../data/operations/toolbox-crossref-citation-matcher-route-evidence-r0.json).

Crossref API references: [REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), [access and authentication](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/), and the [query.bibliographic citation lookup guidance](https://github.com/CrossRef/rest-api-doc/blob/master/api_tips.md). Crossref metadata and relevance scores are provider observations, not independent validation.
