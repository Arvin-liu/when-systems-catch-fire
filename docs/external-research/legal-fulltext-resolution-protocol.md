# Legal Full-Text Resolution Protocol (IGNITION-121)

## Purpose
This protocol governs how ignition external-research tasks locate, download, and verify legitimate open-access full-text versions of academic papers. It is designed for reuse across IGNITION-NNN tasks that require real full-text evidence.

## Scope
Applies to:
- DOI
- arXiv ID
- PMID/PMCID
- OpenAlex ID
- OpenReview ID
- Known PDF/HTML URLs
- Paper titles used for discovery only

## Resolution Order
Each source must be tried in order, with each attempt logged.

1. **Registered direct open endpoints** already recorded in the source registry (arXiv HTML/PDF, NeurIPS, PMLR, ACL Anthology, OpenReview, PMC/Europe PMC, DOAJ, Zenodo, HAL, institutional repositories).
2. **arXiv official path** for arXiv IDs:
   - `https://arxiv.org/html/{id}`
   - `https://arxiv.org/pdf/{id}.pdf`
   - arXiv metadata API: `https://export.arxiv.org/api/query?search_query=id:{id}`
   - ar5iv HTML mirror as fallback: `https://ar5iv.labs.arxiv.org/html/{id}`
3. **OpenAlex OA locations** (`best_oa_location`, `locations`, `pdf_url`, repository/accepted manuscript locations).
4. **DOI / OA discovery**:
   - Crossref metadata
   - Unpaywall (email only from environment `UNPAYWALL_EMAIL`, no secrets in repo)
   - Semantic Scholar metadata
   - Europe PMC/PMC for life sciences
   - CORE / OA Button only when a public, no-authentication endpoint is available
5. **Official conference/journal open pages** (only the publicly available version).

## Prohibited
- Sci-Hub, LibGen, or similar infringing sources.
- Institution account, cookie, or login-state reuse.
- Bypassing paywalls, captchas, robots, or access control.
- Treating abstracts, search snippets, or model summaries as full-text reviews.
- Treating `has_fulltext=true` or OA metadata as having read the content.

## Evidence Standard
A source may be marked `FULLTEXT_REVIEWED` only when all of the following are true:
1. A complete HTML or PDF file was obtained through a legitimate channel.
2. PDF magic number, HTTP content-type, and file size are reasonable.
3. Text can be extracted; OCR limitations must be explicitly recorded if present.
4. SHA256 is recorded.
5. Version is identified (preprint, accepted manuscript, published version, author manuscript).
6. Access channel, timestamp, and open license/public status are recorded.
7. Real page numbers, sections, figures, or stable HTML anchors are recorded.
8. The paper's specific support for ignition claims is stated.
9. The paper's limitations / non-support for ignition claims are stated.
10. `claim_support_status` is one of: `CONFIRMED`, `PARTIAL`, `NOT_SUPPORTED`, `UNRESOLVED`.

## Cache and Repository Rules
- Full-text files are cached locally under `.cache/fulltext/`.
- `.cache/fulltext/` is in `.gitignore` and must not be committed.
- Only hashes, relative cache identifiers, metadata, and evidence cards are committed.
- No API keys, tokens, cookies, or credential fragments may be committed.
- Use environment variables names only; never store values.

## Output Formats
- `121-fulltext-resolution-log.jsonl`: one line per resolution attempt.
- `121-fulltext-source-registry.jsonl`: one line per source with resolution status.
- `121-fulltext-evidence-cards.jsonl`: one line per full-text-reviewed source.
- `121-fulltext-failure-register.jsonl`: one line per failed resolution with reason.

## Contact Pool
- OpenAlex: `mailto` from `OPENALEX_MAILTO` (default: `research@ignition.local`).
- Unpaywall: `UNPAYWALL_EMAIL`.
- Crossref: polite user-agent, no key required.

## Version
IGNITION-121, 2026-07-14.
