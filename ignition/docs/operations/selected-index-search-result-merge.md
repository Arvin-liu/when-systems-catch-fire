# Selected index search result merge

`research.merge_selected_index_search_results@0.1.0` combines two or three already captured topic-search receipts from the existing Crossref, OpenAlex, and Europe PMC adapters. It is a local, offline operation: it makes no network requests, reads no repository files, writes no files, and does not need credentials or extra permissions.

## Use

Provide a UTF-8 JSON object with exactly one field, `source_results`, containing two or three complete provider receipts. Each receipt must retain its adapter ID/version, fixed endpoint, acquisition status, retrieval timestamp, result limit, query hash, response hash, returned count, and bounded records. Failed provider receipts may be included so the result preserves partial coverage.

```sh
python3 -B ignition/tools/toolbox_merge_selected_index_search_results.py --stdin
```

The tool validates each receipt against its provider identity and endpoint, then returns bounded record summaries and clusters only records whose DOI matches after stripping a standard DOI URL prefix and case-folding. Records without a valid DOI stay unclustered. Title, year, authors, or provider rank never create identity groups. The output includes the exact input hash and source-level query/response hashes.

## Limits

- This is useful after a task already calls for searching more than one index. For a task satisfied by one index, use that provider's adapter and skip this step.
- Provider query syntax, corpus coverage, ranking, result counts, and timestamps differ. The tool preserves source-specific results side by side; it does not compare relevance, recall, quality, or provider accuracy.
- An exact DOI group is an identifier observation only. It does not establish that a citation is correct, the record authentic, or a claim scientifically supported.
- This utility does not replace Crossref, OpenAlex, Europe PMC, or the known-DOI metadata comparator. Each provider adapter remains independently useful for its source-specific coverage and output.

## Primary provider references

- [Crossref REST API](https://api.crossref.org/)
- [Europe PMC RESTful Web Service](https://europepmc.org/RestfulWebService)
- OpenAlex results are accepted only from the repository's existing bounded Works query adapter; this tool does not issue a new request.
