# PubMed Citation Matcher

`research.match_pubmed_citation` is an experimental, default-off adapter for one caller-supplied **public bibliographic citation** when no DOI or PMID is available. It sends journal title, year, volume, first page, and first author to the fixed NCBI ECitMatch endpoint and returns only the PMID that NCBI reports, if any.

Example input:

```json
{"journal_title":"proc natl acad sci u s a","year":"1991","volume":"88","first_page":"3248","first_author":"mann bj"}
```

Run one explicit public-network invocation:

```sh
python3 -B ignition/tools/toolbox_pubmed_citation_matcher.py --stdin --allow-public-network
```

The adapter makes one HTTPS GET to `eutils.ncbi.nlm.nih.gov`, with a stable `tool` parameter. It does not send an email address or API key. The exact citation fields are sent to NCBI, so do not use it for confidential, patient-identifying, or otherwise sensitive material. One invocation makes one request, with no redirects, retries, arbitrary URLs, file writes, repository mutations, billing, or external actions. Separate invocations are not globally rate-coordinated; callers must follow [NCBI scripting policies](https://www.ncbi.nlm.nih.gov/home/about/policies/).

`PROVIDER_MATCH_REPORTED` means only that a well-shaped response echoed the request key and fields and returned a numeric PMID. It does not authenticate the provider response or independently verify that the record's metadata matches the citation. `NO_MATCH_REPORTED` is an observation for this request, not evidence that an article does not exist. Follow a returned PMID to the PubMed record and check the citation before relying on it.

Use this only when a structured citation needs a PubMed identifier. It complements `research.resolve_pubmed_identifiers` (DOI input) and `research.search_pubmed_query` (caller-directed PubMed query and metadata). It returns no title, abstract, or full text and makes no relevance, retraction, or scientific judgment.

NCBI's [usage policies](https://www.ncbi.nlm.nih.gov/home/about/policies/) and [disclaimer and copyright notice](https://www.ncbi.nlm.nih.gov/About/disclaimer.html) apply. The adapter returns no article text; PubMed citation matching is not a copyright or reuse determination.

The candidate is experimental and excluded from routing by default. A route proposal does not authorize this network request; each invocation still requires `--allow-public-network` and caller permission to send the citation fields to NCBI.
