# Pilot Result — Crossref DOI Re-verification (Task 103 §7–§8)

**Pilot:** `IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION`
**Outcome:** **SUPPORTED_WITHIN_SCOPE** (external-evidence claim supported; two minor in-tier caveats)
**Preregistered:** `evidence-program/preregistration/...prereg.json` (committed before any query — commit `a4d13a69…`)
**Run manifest:** `run-manifest.json` · **Source provenance:** `source-manifest.jsonl` (117 records) · **Adjudication:** `result-adjudication.json`

## Why this pilot

Pointfire's external-source registry (`data/external-research/104-source-registry.jsonl`) holds 117
source records, each asserting `crossref_verified: true` with a recorded title and year. The claim had
never been independently re-checked against the external authority that produced it. This pilot asks a
bounded, falsifiable question: *do those DOIs actually resolve in Crossref with the recorded title and
year, and are they not retracted or duplicated?* It is a metadata-integrity claim (allowed by §3.9 — no
grand-physics claim chosen for narrative) using a genuine external oracle.

## What was tested (preregistered)

- **Population:** all 117 registry records.
- **Oracle:** public Crossref REST API (`https://api.crossref.org/works/{doi}`), CC0 licence, per-DOI
  retrieval timestamp + response SHA-256 recorded.
- **Baseline:** the registry's own `crossref_verified` / `crossref_title` / `crossref_year` assertion.
- **Metrics:** verification_match_rate (primary) + resolution/title/year rates, retraction count,
  duplicate count.
- **Decision thresholds (fixed before seeing results):** SUPPORTED if rate ≥ 0.95 AND retractions = 0
  AND intra-registry duplicates = 0.

## Result

| Metric | Observed |
| --- | --- |
| DOIs resolved via Crossref | 117 / 117 (100%) |
| Title match | 117 / 117 (100%) |
| Year match | 112 / 117 (95.7%) |
| Full match (title + year) | 112 / 117 (95.7%) |
| Retraction signals | 0 |
| Intra-registry duplicate DOIs | 1 |
| Resolution failures | 0 |

## Uncertainty & deviations

- Finite census (N=117), no sampling error; exact counts reported.
- **No deviation from the preregistration plan** — all thresholds, scope and E-axis mapping applied
  unchanged (deviation-log is empty).
- The two findings are *results*, not plan changes:
  1. **1 intra-registry duplicate DOI** — `10.1016/s0070-2153(07)81015-5` is listed under GAP002-01
     and GAP002-08. This is internal registry redundancy; that DOI still resolves and matches Crossref
     externally, so it does not contradict the external claim. → de-duplicate in the registry.
  2. **5 year mismatches** (title matches in all 5): GAP001-06 (2020 vs 2019, off-by-one); GAP002-02,
     GAP005-01, GAP008-06 (registry year missing → Crossref provides it); GAP008-08 (supplement DOI,
     year 2025). → backfill/correct `crossref_year` for these 5 entries.

## What changed vs what did not

- **Changed (in-tier correction, no E downgrade):** `evidence_tier_104 = METADATA_VERIFIED` is
  **confirmed** for all 117 entries. Two data-quality fixes are required within the same tier: year
  backfill for 5 entries; de-duplicate 1 DOI. A positive provenance note is recorded.
- **Did not change:** no E-axis promotion beyond scope (§8.5); no claim about Pointfire physics
  correctness; the 5 year mismatches remain `METADATA_VERIFIED` (identity/title verified, only the year
  field needs correction).
- This is a legitimate *supported* result, not a failure. Negative/null results would also have been
  preserved and adjudicated honestly (§8).

## Reserve pilots & next evidence priorities

- **Reserve 1 — OpenAlex cross-check:** re-verify the same 117 DOIs against OpenAlex for a second
  independent oracle.
- **Reserve 2 — Case-table historical anchors:** verify named historical figures/events in the case
  tables against Wikipedia.
- **Next:** apply the two in-tier corrections to the registry; then promote Function OS v0.2 correctness
  (candidate C-04) as the next pilot.
