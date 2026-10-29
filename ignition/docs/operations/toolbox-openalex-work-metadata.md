# OpenAlex Work metadata and location lookup

`research.lookup_openalex_work_metadata` v0.2.0 accepts one to five unique bare DOI identifiers and returns an exact-primary-DOI-matched OpenAlex Work projection. In addition to the v0.1 metadata, it returns OpenAlex-reported `open_access`, `best_oa_location`, and `locations` fields.

The adapter makes one bounded `GET` to the fixed HTTPS host `api.openalex.org` per invocation. Its selected fields are `id`, `doi`, `display_name`, `publication_year`, `type`, `is_retracted`, `open_access`, `locations`, and `best_oa_location`. It keeps only a small projection: location ID, OpenAlex source ID/name/type, provider `is_oa`, landing page and PDF URLs, provider license and version; plus the OpenAlex `open_access` summary. At most 25 locations per work are returned, with the provider list count and an explicit truncation flag.

Location URLs are returned only when they are HTTPS URLs with a hostname, no embedded username/password, and no nonstandard port. Rejected URL fields become `null` and contribute to `omitted_unsafe_location_url_count`. The adapter never requests a returned location URL, downloads article text, or checks whether a link, license, access claim, or article is valid. Provider fields remain provider claims.

## Use and permission

This is an optional experimental tool and is not selected by default. A task must explicitly allowlist `research.lookup_openalex_work_metadata` and separately allow the host `api.openalex.org`; the route proposal grants neither permission. Each actual CLI call also requires `--allow-public-network` and a task-specific decision to transmit the supplied DOI values.

```json
{"dois":["10.1371/journal.pone.0005403"]}
```

```sh
python3 -B ignition/tools/toolbox_openalex_work_metadata.py --stdin --allow-public-network
```

There are no retries, redirects, repository writes, credentials, email addresses, billing data, or external actions. A response over 256 KiB, network failure, malformed location projection, or ambiguous DOI result remains an explicit failure or inconclusive outcome.

## Interpreting results

- `EXACT_PRIMARY_DOI_MATCH` means one response record's primary DOI matched the requested DOI. It does not validate that record's source or contents.
- `location_metadata_status=PROVIDER_REPORTED` means the response contained the OpenAlex `locations` array; an empty array remains an empty provider report. `NOT_RETURNED` means the field was absent or null.
- `openalex_locations_count` is the number of location entries in the response. `openalex_locations_returned_count` is the sanitized projection count; `openalex_locations_truncated` marks a list longer than 25.
- `openalex_best_oa_location`, `openalex_open_access`, and all location fields are OpenAlex-reported metadata. In particular, `is_oa`, `oa_status`, and `license` do not establish that a URL works or that reuse is legally permitted.
- The raw response is hashed but not emitted or written to disk. Abstracts and article content are not selected.

## Scope and alternatives

The Europe PMC location adapter uses Europe PMC provenance and can return its `fullTextUrlList` fields and availability codes for a known DOI, PMID, or PMCID. This OpenAlex adapter uses OpenAlex provenance and returns its Work-level `locations` projection plus OpenAlex's own open-access summary. One same-DOI comparison returned eight OpenAlex location records and three Europe PMC entries; these different provider schemas do not measure comparative completeness. The outputs are not interchangeable, so both tools remain optional for their source-specific tasks. The existing general OpenAlex client retains its broader query and article-metadata role. No comparison establishes broad coverage, reliability, URL validity, legal reuse, latency, or cost, and neither location tool is marked as a replacement.
