# Europe PMC topic search candidate

`research.search_europe_pmc_query` is an experimental, default-off adapter for discovering a small set of publication metadata records from a caller-supplied public query. It sends one request to the [Europe PMC REST Web Service](https://europepmc.org/RestfulWebService), asks for JSON `lite` results, and returns no more than ten selected metadata rows. The provider documentation describes `lite` as key metadata; abstracts and full text are not requested or returned by this wrapper.

Example input:

```json
{
  "query": "CRISPR off-target",
  "max_results": 3
}
```

Run one explicit network invocation:

```sh
python3 -B ignition/tools/toolbox_europe_pmc_query_search.py --stdin --allow-public-network
```

The query is sent to `www.ebi.ac.uk` as a URL parameter. The receipt includes a query SHA-256 instead of echoing the query, along with the response SHA-256, retrieval timestamp, provider hit count, bounded result count, source IDs and selected citation metadata. The adapter has no file writes, redirects, retries, credentials or billing account. Provider-side request logging is outside its control.

Use this only when the caller needs query-to-record discovery and the query is appropriate for a public service. Do not send confidential, patient-identifying, personal-health or other sensitive terms. A route proposal does not authorize network use; the caller must explicitly select the candidate, permit the exact host in the task context, and pass `--allow-public-network` for each actual invocation.

This search is not an exhaustive literature-search method and does not assess relevance quality, scientific validity, source authenticity, publication status, corrections, retractions, or whether a record supports a claim. Prefer checked-out source navigation or an existing article-cluster brief when that local corpus already satisfies the task. When a DOI, PMID or arXiv identifier is already known, use the corresponding identifier-specific adapter if its narrower output is needed. The local Crossref/OpenAlex comparator remains separate because it consumes existing adapter results and performs no retrieval. These functions can coexist because their inputs and outputs differ.

The route and live smoke evidence is recorded in `ignition/data/operations/toolbox-europe-pmc-query-search-evidence-r0.json`. The implementation and focused negative controls are in `ignition/tools/toolbox_europe_pmc_query_search.py` and `ignition/tests/test_toolbox_europe_pmc_query_search.py`.
