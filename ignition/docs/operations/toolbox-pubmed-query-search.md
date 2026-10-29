# PubMed bounded query search candidate

research.search_pubmed_query is an experimental, default-off adapter for caller-directed PubMed query-to-record discovery. It sends the caller's non-sensitive query to the fixed NCBI E-utilities host, runs one ESearch request and, when IDs are returned, one ESummary request, then emits at most ten selected bibliographic metadata records.

The input requires query, max_results, and contact_email. E-utilities requests include NCBI's tool and caller-supplied email parameters. The contact email and query are sent to NCBI; the receipt stores a query digest but does not echo or retain the email value. Do not submit confidential, patient-identifying, personal-health, or otherwise sensitive queries. If a caller cannot provide a contact address suitable for this public service, do not invoke this adapter.

Example input:

    {"query":"microplastics","max_results":5,"contact_email":"researcher@example.org"}

Run one explicit network invocation:

    python3 -B ignition/tools/toolbox_pubmed_query_search.py --stdin --allow-public-network

The adapter is capped at two sequential HTTPS requests, ten records, 512 KiB per response, five seconds per request, and seven seconds of response-body time per request. It has no redirects, retries, API key, file writes, repository mutation, billing account, or arbitrary-host support. It does not coordinate request rate across separate or concurrent invocations; the caller must respect NCBI's per-IP rate guidance. Provider-side request logging is outside this wrapper's control. The allow-public-network flag is required for every invocation.

Use this when PubMed-specific indexing or query-field syntax is part of the task, or when the caller explicitly requires PubMed as a source. Europe PMC topic search is a distinct source adapter; one live query does not establish which provider has better relevance, recall, completeness, cost, or scientific quality. Keep both tools available with different source scopes while those comparisons remain unknown. Local Knowledge search remains preferable when its checked-out corpus already answers the bounded task.

This adapter returns metadata only. It does not retrieve abstracts or full text, verify article content, judge relevance, establish scientific support, authenticate source records, or determine correction/retraction status. It is not an exhaustive or reproducible systematic-review search method.

## NCBI notice and content rights

NCBI's scripting guidelines require the NCBI Disclaimer and Copyright notice to be evident to users of software built on E-utilities. PubMed indexes literature from third-party publishers and organizations; inclusion does not imply NLM endorsement, and this wrapper does not determine reuse rights for returned citation metadata. See [NCBI usage policies](https://www.ncbi.nlm.nih.gov/home/about/policies/), the [NCBI Disclaimer](https://www.ncbi.nlm.nih.gov/About/disclaimer.html), and [E-utilities documentation](https://www.ncbi.nlm.nih.gov/books/NBK25499/). This adapter returns no abstracts or full text.

The implementation, focused negative controls, live task receipt, C1 comparison, and default-off routing experiment are listed in the candidate card. Current operation authority is unchanged.
