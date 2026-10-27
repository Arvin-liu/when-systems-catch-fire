# Preregistration — Task 110 OpenAlex Independent Replication Pilot (C-03)

**Status:** FORMAL PREREGISTRATION GATE — this dedicated commit is created and pushed before any outcome-bearing OpenAlex request; after push it is immutable.
**Must be an ancestor of every formal result commit for task 110.**
**Contract:** `relay/tasks/110.md` (SHA `15cdbf489ea68630d5d13cff15e65c71b12caac512742803fdc49b29a856224d`), §9.
**Relay authorization:** `relay/current` tip `889c555a09be93c6b6b0af8e3b985990e5a86d4e` (task 110 AUTHORIZED; refreshed after audited blocker recovery).

---

## 1. Exact target `main` commit

- `0bbd31a82406e1922509aa052885d214b6efff85`
  (Merge pull request #170 from Arvin-liu/agent/ignition-iteration-planner-terminalization-r1-20260801)
- All comparison baselines (task-103 Crossref pilot outputs, `104-source-registry.jsonl`) are read at this commit.

## 2. Exact population manifest and SHA-256

- File: `data/operations/iterations/110/openalex/population-manifest.jsonl`
- SHA-256: `27a92a91048a8939a5a39867971323e0af5a3c6779cddf8389cf56e24746bcb2`
- Records: 117 (one JSON object per line)
- Schema per record:
  - `source_id` (e.g. `GAP001-01`)
  - `doi_raw` (e.g. `https://doi.org/10.1007/s10489-024-05338-9`)
  - `doi_normalized` (e.g. `10.1007/s10489-024-05338-9`)
  - `title` (source-registry display title; retained as supplied and not assumed identical to `crossref_title`)
  - `crossref_title`
  - `crossref_year` (int)
  - `retraction_status` (raw registry value; observed values include `NONE`, `none`, `RETRACTED` and other)
  - `is_duplicate_doi` (bool)
- Provenance: derived from `data/external-research/104-source-registry.jsonl` task-103 Crossref-pilot `crossref_verified` records, with DOI normalization and duplicate resolution.

## 3. Inclusion / exclusion rules

- **Inclusion:** every record in `population-manifest.jsonl` (117 records). The governed DOI population is the task-103 Crossref-pilot in-scope set with all inclusions/exclusions already resolved and hashed at `27a92a91…`.
- The manifest is retained byte-for-byte, including one record whose display `title` is fuller than `crossref_title`; `crossref_title` is the sole governed title comparator. The manifest also retains raw `retraction_status` casing; matching case-folds only the exact labels `NONE`/`none` and `RETRACTED`/`retracted`, while any other value is recorded as `other` and never silently treated as `NONE`.
- **Exclusion:** records with `is_duplicate_doi == true` are retained in the manifest for completeness but flagged `duplicate` and excluded from the *primary* adjudication rate (counted separately; a duplicate that resolves in OpenAlex is not double-counted toward support/non-support).
- No record is added or dropped after preregistration. Any later addition requires a new preregistered amendment commit.

## 4. DOI normalization rules

- Strip the `https://doi.org/` (and any variant scheme/host) prefix.
- Lowercase the entire remainder.
- Trim surrounding whitespace.
- This `doi_normalized` is the canonical matching key against OpenAlex `doi`.

## 5. OpenAlex API endpoint / version assumptions and retrieval policy

- Primary endpoint: `https://api.openalex.org/works` (Works entity, current schema).
- Retrieval: `GET https://api.openalex.org/works?filter=doi:<doi_normalized>&mailto=<polite-pool-email>`
- We request the first result (`results[0]`). If multiple results, we keep the one whose `doi` (normalized) equals `doi_normalized`; if none match by DOI, the record is treated as `NULL_OR_INCONCLUSIVE` (no silent best-guess).
- Pagination is not needed (filter by exact DOI returns ≤ 1 true match).
- We do **not** use the `https://api.openalex.org/works/https://doi.org/<doi>` redirect form to avoid ambiguity; the `filter=doi:` form is the source of truth.

## 6. Authentication / polite-pool configuration (no secrets)

- No API key or token is used or committed.
- Polite pool is observed by appending `mailto=<operator-email>` to every request. The email is a public, non-secret contact address supplied at runtime via environment variable `OPENALEX_MAILTO`; it is **never** written to the repository.
- If `OPENALEX_MAILTO` is unset, requests proceed without it (lower rate limit) — this is logged, not fatal.

## 7. Rate-limit, retry, timeout and cache policy

- Rate limit: ≤ 10 requests/second (polite pool). Sequential with a 0.11 s minimum inter-request delay (≈9 req/s) to stay safely under limit.
- Retry: on HTTP 429 / 5xx / network error, retry up to 3 times with exponential backoff (1 s, 2 s, 4 s). After 3 failures the DOI is recorded `TEST_INVALID_OR_ABORTED` with the last error and the run continues (no abort of the whole census).
- Timeout: 30 s per request.
- Cache: no persistent cross-run cache. Each run re-fetches live from OpenAlex. The raw response for each DOI is snapshotted and content-addressed (see §19) so reruns are reproducible without re-calling the network.

## 8. Title normalization and match algorithm

- Normalization for matching:
  1. Unicode NFKC normalization.
  2. Lowercase.
  3. Remove all whitespace and all punctuation/separators, keep alphanumerics only.
- Match metric: `difflib.SequenceMatcher(None, norm_a, norm_b).ratio()` on the normalized strings.
  - `ratio >= 0.92` → title **match**.
  - `0.75 <= ratio < 0.92` → title **partial** (recorded as a mismatch reason, eligible for `PARTIALLY_SUPPORTED`).
  - `ratio < 0.75` → title **mismatch**.
- The original OpenAlex `display_name` and the normalized form are both retained.

## 9. Publication-year comparison rule (online/print ambiguity)

- Compare OpenAlex `publication_year` (int) against `crossref_year`.
- `|Δ| == 0` → consistent.
- `|Δ| == 1` → consistent, reason `online_print_ambiguity` (common for online-first vs print). Still counted as a match.
- `|Δ| > 1` → year mismatch (candidate `CONTRADICTED` unless overridden by a documented registry correction).
- No month/day reconciliation; year is the governed granularity.

## 10. Work-type and canonical-ID comparison rules

- Canonical ID: `doi_normalized`. Hard requirement: the chosen OpenAlex result's `doi` (normalized) must equal `doi_normalized`. Mismatch → `NULL_OR_INCONCLUSIVE`.
- Work type: compare OpenAlex `type` (e.g. `article`, `book-chapter`, `proceedings-article`) against the Crossref `type` from `104-source-registry.jsonl` when present.
  - Match / known-equivalent mapping → consistent.
  - Crossref type absent → `not_comparable` (no penalty; secondary signal only).
  - Clear contradiction (e.g. `article` vs `dataset`) → recorded mismatch reason (secondary; does not alone force `CONTRADICTED`).

## 11. Duplicate / collision handling

- Duplicates (`is_duplicate_doi == true`) are flagged and excluded from the primary rate.
- If OpenAlex returns multiple results, select by exact normalized-DOI equality. If none equals, record `NULL_OR_INCONCLUSIVE` rather than guessing.

## 12. Retraction and availability signal handling

- Compare the case-folded known manifest labels against OpenAlex `is_retracted` (bool):
  - `NONE` or `none` vs `false` → consistent.
  - `RETRACTED` or `retracted` vs `true` → consistent.
  - `NONE`/`none` vs `true` → **retraction mismatch** (flag; candidate `CONTRADICTED` if not explained by a registry correction).
  - `RETRACTED`/`retracted` vs `false` → retraction mismatch (flag).
  - any other raw value → `NULL_OR_INCONCLUSIVE` with `null_reason=unrecognized_registry_retraction_status`; it is never silently mapped.
- OpenAlex `is_retracted` is the independent oracle signal; it is never overridden by the registry silently.

## 13. Primary and secondary metrics

**Primary (each boolean, gating the adjudication class):**
- `title_match` (per §8 threshold)
- `year_match` (per §9)
- `canonical_id_match` (hard requirement)
- `retraction_match` (per §12)

**Secondary (recorded, non-gating unless specified):**
- `title_ratio` (float)
- `year_delta` (int)
- `type_match` / `type_not_comparable`
- OpenAlex `type`, `publication_year`, `cited_by_count`, `id` (work ID)
- `confidence` (derived: fraction of primary metrics satisfied)

## 14. Thresholds and adjudication classes

Per contract §11, each DOI is assigned exactly one class:

- `SUPPORTED_WITHIN_SCOPE`: `canonical_id_match` AND `title_match` AND `year_match` AND `retraction_match` (type may be `not_comparable` or matching).
- `PARTIALLY_SUPPORTED_WITH_IDENTIFIED_MISMATCHES`: `canonical_id_match` true, but at least one primary metric is a *minor* deviation that is explainable — specifically `year_delta == 1` (online/print) and/or `title_ratio in [0.75, 0.92)` — while no hard contradiction (no `|Δ|>1`, no retraction mismatch, no title `<0.75`). All mismatches are itemized in `mismatch_reasons`.
- `CONTRADICTED_WITHIN_SCOPE`: `canonical_id_match` true but at least one hard contradiction present: `title_ratio < 0.75`, or `|year_delta| > 1` unexplained, or `retraction_match` false.
- `NULL_OR_INCONCLUSIVE`: OpenAlex returns no result / no DOI-equal record / API error preventing resolution (after retries).
- `TEST_INVALID_OR_ABORTED`: acquisition failed irrecoverably and could not be quarantined (network-level abort after 3 retries). Tracked separately; never counted as support.
- Duplicates are tagged `duplicate` and excluded from the primary rate denominator.

## 15. Missing-record and API-error treatment

- No OpenAlex result (`results` empty or none DOI-equal) → `NULL_OR_INCONCLUSIVE`, with `null_reason`.
- HTTP error / timeout / 429 exhaustion → `TEST_INVALID_OR_ABORTED`, with `last_error` and `attempts`.
- First-run failures are **preserved** (see §18); they are never rewritten to look like a clean pass.

## 16. Deviation rules

- A deviation is any departure from this protocol (e.g. a record added post-hoc, a threshold changed, a retry policy altered). Every deviation is recorded in `deviations-and-corrections.md` with timestamp, cause, and effect. No silent deviation.
- If a registry correction is warranted (e.g. a manifest typo), we separate: (a) original baseline result, (b) correction evidence, (c) corrected registry commit, (d) identical-protocol rerun result. The first run is preserved verbatim.

## 17. Stop conditions

- Census stops normally when all 117 manifest records have a recorded class.
- Hard stop / abort if cumulative `TEST_INVALID_OR_ABORTED` rate exceeds 50% (indicates systemic outage) — recorded as a blocker, not silently continued.
- No early stopping on favorable counts.

## 18. Exact claim ceiling

**Cross-source bibliographic metadata consistency only.**
The claim `DOI-OPENALEX-CROSS-CHECK` is supported only to the extent that OpenAlex bibliographic metadata (title, year, DOI identity, retraction flag) is consistent with the governed registry/Crossref fields under this preregistered protocol.

It does **NOT** validate:
- cited-paper conclusions or scientific truth,
- Pointfire claims, MCF, PSD, ARN,
- any physical theory,
- paper-content or causal validity.

A favorable result strengthens confidence only in external bibliographic-metadata consistency.

## 19. Software / environment versions

- Python 3.13.12 (managed runtime)
- `requests` (HTTP client)
- Standard library: `hashlib`, `json`, `difflib`, `unicodedata`, `datetime`, `time`
- No third-party bibliographic libraries; the protocol is implemented explicitly for auditability.
- OpenAlex schema: live `api.openalex.org` (no pinned version; schema drift is captured via raw-response snapshots).

## 20. Raw-response retention and hashing plan

- For every DOI, the full raw OpenAlex JSON response is written to `data/operations/iterations/110/openalex/source-manifest.jsonl` (one record per line) containing:
  - `source_id`, `doi_normalized`
  - `http_status`
  - `retrieved_at` (ISO-8601 UTC)
  - `raw_response_sha256` (SHA-256 of the verbatim response body)
  - `openalex_work_id`, `openalex_doi`, `display_name`, `publication_year`, `type`, `is_retracted`, `cited_by_count`
  - `selected_result_index`
- A `run-manifest.jsonl` records per-DOI execution metadata: attempts, timings, final class, primary/secondary metrics, `mismatch_reasons`, `null_reason`, `last_error`.
- Raw response bodies (verbatim) are retained in `raw/<source_id>.json` and content-addressed by their SHA-256 so the census is reproducible without re-calling the network.
- First-run failures are preserved in `raw/` and never overwritten.

---

**This document and the accompanying 117-record population manifest are committed together as the formal preregistration gate. The resulting commit must be an immutable ancestor of all formal result commits for task 110. No outcome-bearing OpenAlex request or result inspection occurred before this gate.**
