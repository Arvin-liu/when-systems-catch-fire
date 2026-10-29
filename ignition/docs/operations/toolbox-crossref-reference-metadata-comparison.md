# Crossref Reference Metadata Comparator 0.2.0

research.compare_crossref_reference_metadata accepts one source-work DOI and one to five caller-selected Crossref reference rows. With the optional `verify_source_link` omitted or set to `false` (the default), it preserves the 0.1.0 behavior: send only each selected reference DOI to the fixed Crossref Works API, then compare supplied structured title, year, journal, volume, issue, and first-page fields with the DOI-resolved Work metadata.

With `verify_source_link: true`, the caller also approves sending the source-work DOI to Crossref. The tool makes one bounded source Work request and requires the returned Work DOI to match that source DOI. For each selected row, it then requires exactly one source-deposited reference with the selected key and the same DOI before requesting the target Work. A missing, duplicate, malformed, or mismatched source row prevents that target request. The result reports the source-row binding and its supplied-field comparisons separately from the target Work comparisons. Source reference rows are not copied into the top-level source verification summary.

The result reports normalized equality, normalized difference, missing provider fields, and acquisition failures per input row. A difference is a literal metadata discrepancy after normalization; it does not prove that a citation is wrong. A match does not prove that either Crossref record is authentic, complete, or scientifically relevant. Even in source-link mode, this checks only Crossref's returned record and deposited reference row; it does not authenticate publisher provenance, establish that the source bibliography is complete, or validate a citation. Author strings and free-form unstructured citations are omitted from comparison because their formatting is not reliably equivalent.

The tool does not follow citation URLs, download article pages, or retrieve full text. Each explicit CLI call performs at most five sequential fixed-host HTTPS GET request attempts to `api.crossref.org`, or at most six when `verify_source_link` is true (one source Work plus up to five selected cited Works). A target request is attempted only after its source row is bound. Each request reuses the existing Crossref adapter's redirect block, request timeout, response-size cap, and response-body deadline. It sends DOI identifiers only. The result is written to stdout; invalid input is written to stderr; the repository is not modified.

Example input:

    {
      "source_work_doi": "10.1186/s12884-025-07725-7",
      "verify_source_link": true,
      "references": [
        {
          "key": "7725_CR2",
          "doi": "10.1136/bjsports-2020-102955",
          "year": 2020,
          "journal_title": "Br J Sports Med",
          "volume": "54",
          "first_page": "1451"
        }
      ]
    }

Run with `--stdin --allow-public-network`. The router candidate remains default-off and requires explicit tool inclusion plus the exact `api.crossref.org` host in the task profile. A route proposal does not authorize the network call; the CLI flag is a separate per-invocation permission. When `verify_source_link` is true, this invocation permission also covers transmission of the supplied source-work DOI.

The comparator is complementary to research.verify_crossref_metadata, which checks caller-supplied title/year expectations and projects the citing Work's references without resolving them. It is also complementary to research.compare_publication_metadata_snapshots, which compares already-collected Crossref and OpenAlex title/year results without fetching cited Works. No comparative quality, completeness, latency, or cost advantage is established.
