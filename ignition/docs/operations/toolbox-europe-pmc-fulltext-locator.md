# Europe PMC exact DOI full-text location locator

`research.resolve_europe_pmc_fulltext_locations` is an optional experimental adapter for a task that already has one to five public DOI identifiers and needs the `fullTextUrlList` metadata reported by Europe PMC. It uses the fixed Europe PMC Search API with `DOI:<identifier>`, `resultType=core`, and a provider page size of five.

The adapter returns exact DOI matches, source identifiers, a small set of URL-related provider fields, response hashes, retrieval time, and reason-coded acquisition/match states. It does not return titles, abstracts, raw provider bodies, or article text. It never follows a returned URL. It omits links that are not safe HTTPS URLs and reports how many were omitted.

## Use and permission

This candidate is default-off. A task must explicitly allowlist the exact tool and separately permit the public network host `www.ebi.ac.uk`; a route proposal does not grant either permission. The CLI additionally requires `--allow-public-network` on each invocation.

Example request:

```json
{"dois":["10.1371/journal.pone.0005403"]}
```

```sh
python3 -B ignition/tools/toolbox_europe_pmc_fulltext_locator.py --stdin --allow-public-network
```

The tool accepts at most five unique bare DOI values and sends one HTTPS API request per DOI. It has no retry, redirect, file-write, credential, billing, repository-mutation, or external-action capability. Each request uses a five-second socket timeout, a seven-second response-body time budget, and a 512 KiB body limit.

## Interpreting results

- `EXACT_RECORD_WITH_LOCATIONS` means the API returned an exact DOI record with one or more syntactically safe HTTPS URL values. It does not mean any URL is reachable.
- `EXACT_RECORD_NO_USABLE_LOCATION` means an exact record was returned but it had no usable URL in the provider payload.
- `MULTIPLE_EXACT_RECORDS` preserves all returned exact DOI records and does not choose one.
- `NO_EXACT_MATCH` means this bounded API response did not contain an exact DOI record; it does not prove the work is absent.
- `INVALID_PROVIDER_RESPONSE`, HTTP errors, rate limits, redirects, timeout, oversized body, and network failures remain explicit.

`availability`, `availability_code`, `document_style`, `site`, `license`, and `is_open_access_claim` are provider-reported fields. They are not independently checked and do not establish access, a license grant, lawful reuse, source authenticity, article status, or scientific support. Callers must not treat an API URL as permission to retrieve or redistribute content.

## Comparison and scope

The existing `research.search_europe_pmc_query` operation performs public topic/text search and returns bounded `lite` publication metadata. It can be useful before a DOI is known, but its declared output does not include the `fullTextUrlList` fields required for this exact-identifier task. This locator does not replace topic search: it requires known DOIs and does not discover literature from a subject query. Existing DOI metadata adapters such as Crossref and OpenAlex provide their own selected metadata, not this Europe PMC location projection. Same-task tests compare exact DOI matching and location extraction; availability, cost, and comparative scientific quality remain unknown.

Primary provider documentation: [Europe PMC RESTful Web Service](https://europepmc.org/RestfulWebService).
