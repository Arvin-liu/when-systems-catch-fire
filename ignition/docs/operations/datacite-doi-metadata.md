# DataCite DOI metadata lookup

`research.lookup_datacite_doi_metadata` retrieves one DataCite DOI record projection from the public, unauthenticated API. The input is exactly one bare DOI in UTF-8 JSON, such as `{"doi":"10.25491/3v3x-tj13"}`. Run it only when DataCite-specific record fields are needed and the caller permits this public request:

```sh
python3 -B ignition/tools/toolbox_datacite_doi_metadata.py --stdin --allow-public-network
```

The adapter performs one GET to `api.datacite.org`, has a five-second request timeout and seven-second bounded response read, caps the response at 128 KiB, blocks redirects, emits a selected JSON projection and response SHA-256 to stdout, and writes no files. It does not send credentials, follow the returned DOI landing page, retrieve dataset contents, or update provider or repository records. The API wrapper uses only the Python standard library.

The projection includes DataCite state and schema version, publisher, publication year, `resourceTypeGeneral`, `resourceType`, bounded title/creator/rights/identifier/relation/date fields, per-field reported/omitted/invalid counts, and the raw response digest. Missing and malformed fields remain distinct. No `url`, raw response, or content URL is emitted.

The DataCite Public API returns Findable DOI records; Registered and Draft metadata require authenticated access. A 404 is recorded as `NO_FINDABLE_DATACITE_RECORD`, not as evidence that a DOI does not exist. Provider-supplied rights fields are metadata only and are not a legal reuse determination. DataCite-specific metadata can complement OpenAlex DOI metadata, while Crossref may independently return no record; one matched DOI establishes no provider ranking or coverage estimate.

Input and output contracts: [`toolbox-datacite-doi-metadata-input-r0.schema.json`](../../schemas/operations/toolbox-datacite-doi-metadata-input-r0.schema.json), [`toolbox-datacite-doi-metadata-output-r0.schema.json`](../../schemas/operations/toolbox-datacite-doi-metadata-output-r0.schema.json).
