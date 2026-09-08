# IGNITION-20260907-162: external longform corpus selection

Status: `FROZEN_BEFORE_SOURCE_DISCOVERY` for the selection protocol; the final eligible corpus is research evidence only. The controlling machine records are under `ignition/data/research/longform-emergence-and-historical-adjudication-2026-09-07/`.

## Freeze and selection boundary

The hypothesis and source-selection protocol were frozen at `2026-09-07T13:56:33+08:00`, before source discovery and before any candidate score was available. Queries were answer-independent and used only generic descriptions such as open-access biology, economics, philosophy, history, mathematics, and technical-handbook full text. Candidate names, Task159–161 score terms, and the Task161 answer key were forbidden from selection.

The protocol required 20–24 eligible works, at least 12, at least six domains, at least eight book/monograph/thesis-scale works, no more than four works per domain, no more than two works per author, and a target corpus of at least 700,000 words. A work was eligible only when a legal public full-text route and a reproducible normalized extraction were available, with at least 25,000 words or at least 100 continuous pages (technical manuals may satisfy the structural equivalent). No raw full-text corpus was committed.

## Final corpus

The final eligible corpus contains 22 works, 4,368,310 extracted words, 8,083 ordered sections, 3,194 PDF pages where applicable, nine domain buckets, and 18 book/monograph/open-textbook-scale works. The all-source access ledger contains 23 candidates; `NIST-800-218` was retrieved and logged but excluded because its normalized extraction contained 15,964 words and 86 sections, below the word/structure rule. Selected-domain counts and IDs are:

| Domain bucket | Works | Eligible words | Selected work IDs |
| --- | ---: | ---: | --- |
| Natural sciences / biology / evolution | 4 | 921,805 | `GUT-2009`, `GUT-2300`, `GUT-15491`, `GUT-57493` |
| Ecology / complex systems | 1 | 103,373 | `GUT-27513` |
| Engineering / safety / control | 4 | 501,344 | `GUT-66078`, `GUT-49445`, `GUT-42602`, `NIST-800-37R2` |
| Computer science / distributed protocols | 3 | 335,879 | `NIST-800-53R5`, `RFC-9000`, `RFC-9110` |
| Economics / institutions / organization | 2 | 867,277 | `GUT-3300`, `OPENSTAX-ECON-3E` |
| Philosophy / logic / science | 3 | 662,838 | `GUT-1497`, `GUT-4705`, `GUT-4280` |
| History / social systems | 3 | 452,592 | `GUT-815`, `GUT-7142`, `GUT-1232` |
| Cognition / psychology | 1 | 349,195 | `OPENSTAX-PSYCH-2E` |
| Mathematics / formal systems | 1 | 174,007 | `OPENSTAX-CALC-V1` |
| **Total** | **22** | **4,368,310** | — |

The named works, authors, years, source URLs, extraction methods, word counts, section counts, and raw/normalized hashes are the fields of `source-manifest.jsonl`; the selection order and quota audit are in `source-selection-freeze.json`. The maximum selected author count is two (`Charles Darwin` and `National Institute of Standards and Technology`); every selected domain is at or below four works.

## Source legality and access

- Project Gutenberg plain-text editions use the catalog landing pages and `cache/epub` text endpoints. The ledger records the Project Gutenberg public-domain-in-USA notice and license basis.
- NIST records use the official NIST full-text PDFs for SP 800-37 Rev. 2 and SP 800-53 Rev. 5. The excluded SP 800-218 retrieval remains in the access ledger as an exclusion, not as selected evidence.
- RFC records use the RFC Editor plain-text endpoints for RFC 9000 and RFC 9110.
- OpenStax records use the official PDF assets and title landing pages. The ledger records the landing-page Creative Commons Attribution-NonCommercial-ShareAlike 4.0 basis.

The full legal URLs are preserved in `source-access-ledger.jsonl` and `source-manifest.jsonl`. Retrievals were cached outside the repository at `/tmp/ignition-20260907-162-corpus`; only normalized metadata, hashes, section state, and derived measurements are committed.

## Restart accounting and residual bias

Run 01 was invalidated after a post-selection audit found three Darwin works, violating the frozen two-works-per-author ceiling. Run 02 preserved the same selection rule and replaced the ecology slot with `GUT-27513` before induction, but was invalidated when two PDF segment maps dropped short intervals and therefore failed the O/S/F token-preservation invariant. Run 03 repaired segmentation by retaining every positive-length interval and is the final valid run. The two invalidated output trees are preserved under `invalidated-runs/run-01/` and `invalidated-runs/run-02/`, with hashes and reasons in `restart-ledger.json`.

The corpus is not a representative sample of world knowledge. It is English-heavy, public-domain/open-license-heavy, selected through accessible full-text routes, and shaped by the hard author/domain quotas. These constraints reduce copyright and reproducibility risk but limit claims about general human knowledge or cognition. The experiment therefore supports only the stated information-volume and ordered-text measurements, not a population-level or external-truth conclusion.
