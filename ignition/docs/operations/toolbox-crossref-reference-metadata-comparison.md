# Crossref Reference Metadata Comparator 0.1.0

research.compare_crossref_reference_metadata accepts one caller-declared source-work DOI and one to five selected Crossref reference rows. It sends only each selected reference DOI to the fixed Crossref Works API, then compares any supplied structured title, year, journal, volume, issue, and first-page fields with the DOI-resolved Work metadata.

The result reports normalized equality, normalized difference, missing provider fields, and acquisition failures per input row. A difference is a literal metadata discrepancy after normalization; it does not prove that a citation is wrong. A match does not prove that either Crossref record is authentic, complete, or scientifically relevant. The source-work DOI is caller-declared, not authenticated or requested by this tool. Author strings and free-form unstructured citations are omitted from comparison because their formatting is not reliably equivalent.

The tool does not follow citation URLs, download article pages, or retrieve full text. Each explicit CLI call performs at most five sequential fixed-host HTTPS GET requests to api.crossref.org; each request reuses the existing Crossref adapter's redirect block, request timeout, response-size cap, and response-body deadline. It sends DOI identifiers only. The result is written to stdout; invalid input is written to stderr; the repository is not modified.

Example input:

    {
      "source_work_doi": "10.1186/s12884-025-07725-7",
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

Run with --stdin --allow-public-network. The router candidate remains default-off and requires explicit tool inclusion plus the exact api.crossref.org host in the task profile. A route proposal does not authorize the network call; the CLI flag is a separate per-invocation permission.

The comparator is complementary to research.verify_crossref_metadata, which checks caller-supplied title/year expectations and projects the citing Work's references without resolving them. It is also complementary to research.compare_publication_metadata_snapshots, which compares already-collected Crossref and OpenAlex title/year results without fetching cited Works. No comparative quality, completeness, latency, or cost advantage is established.
