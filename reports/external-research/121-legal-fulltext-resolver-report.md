# Legal Full-Text Resolver Report — IGNITION-121

## Executive Summary
IGNITION-121 built a reusable, legal full-text resolver for ignition external-research tasks. The resolver operates on a defined protocol that uses only legitimate open-access channels and records every resolution attempt, hash, and failure.

## Resolver Components
- `scripts/external-research/fulltext_resolver.py` — discovers OA candidate URLs via arXiv, OpenAlex, Crossref, Unpaywall, and direct registry URLs.
- `scripts/external-research/fulltext_fetcher.py` — downloads candidate files with curl, records SHA256, content type, page count, and headers.
- `scripts/external-research/fulltext_extract.py` — extracts text and section anchors from PDF/HTML.
- `scripts/external-research/openalex_client.py` — existing OpenAlex client, preserved from commit `5d33b721` (source commit and hash recorded).
- `scripts/external-research/fulltext_resolver_config.example.json` — example configuration with environment variable names only, no secrets.
- `docs/external-research/legal-fulltext-resolution-protocol.md` — the legal resolution protocol.

## Supported Providers (≥6)
1. arXiv (HTML, PDF, API, ar5iv mirror)
2. NeurIPS proceedings PDF
3. PMLR proceedings PDF
4. ACL Anthology PDF
5. JMLR journal PDF
6. OpenReview PDF
7. Direct PDF URLs
8. OpenAlex API (metadata + OA clues)
9. Crossref (metadata)
10. Unpaywall (polite, email from env)
11. Semantic Scholar
12. Europe PMC / PMC

## Smoke Test
- Source: arXiv 2607.02512 (Program-as-Weights)
- PDF: `https://arxiv.org/pdf/2607.02512.pdf` — 1,811,878 bytes, 28 pages, SHA256 `546f833487392f7dc31cf72c04e13eeac77c794420e575d7af2041308f7cdb7d`
- HTML: `https://arxiv.org/html/2607.02512` — text/html, section anchors present
- Status: PASS

## Credential Hygiene
- No API keys, tokens, or credential fragments were committed in 121 artifacts.
- All scripts reference environment variables by name only (`OPENALEX_MAILTO`, `UNPAYWALL_EMAIL`, `FULLTEXT_USER_AGENT`).
- 120 audit found only a non-exploitable key prefix `as_sk_15...`; no key rotation required.

## Resolution Results
- 84 sources from 120 registry processed.
- 74 full-text files successfully fetched and hashed from legal OA channels.
- 10 sources failed to resolve via legal OA; recorded in `121-fulltext-failure-register.jsonl`.
- 30 sources selected for full semantic review (evidence cards).
- All 10 source families have at least 2 reviewed sources.

## Prohibited Sources
- Sci-Hub, LibGen, and credential-bypass sources are explicitly blocked in the provider capability matrix and resolver protocol.
- No paywall bypasses, captcha bypasses, or institution logins were used.

## Limitations
- Some non-arXiv sources (OpenReview, PMLR, direct URLs) failed due to network or access restrictions; these are recorded as failures, not as successes.
- OpenAlex `oa_url` and `has_fulltext` metadata are treated as clues only; a source is not marked `FULLTEXT_REVIEWED` until the file is downloaded, hashed, and extracted.
