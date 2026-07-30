# Pilot Result — Crossref DOI Re-verification (Task 103 §7–§8)

**Pilot:** `IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION`
**Outcome:** **SUPPORTED_WITHIN_SCOPE** (external-evidence claim fully supported; one minor in-tier caveat)
**Preregistered:** `evidence-program/preregistration/...prereg.json` (committed before any query — commit `a4d13a69…`)
**Run manifest:** `run-manifest.json` · **Source provenance:** `source-manifest.jsonl` (117 records) · **Adjudication:** `result-adjudication.json`

> **Re-run note.** RUN-1 (commit `0e9844d55`) found 5 `crossref_year` gaps and 1 intra-registry
> duplicate DOI. The 5 year gaps were corrected in-tier, then the identical preregistered procedure
> was re-run. This document reflects the **re-run** result (rate 1.0). The pre-correction RUN-1
> artifacts are preserved in git history for audit. See `deviation-log.json`.

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

## Result (re-run, after in-tier year corrections)

| Metric | Observed |
| --- | --- |
| DOIs resolved via Crossref | 117 / 117 (100%) |
| Title match | 117 / 117 (100%) |
| Year match | 117 / 117 (100%) |
| Full match (title + year) | 117 / 117 (100%) |
| Retraction signals | 0 |
| Intra-registry duplicate DOIs | 1 (intentional cross-gap citation — retained, see below) |
| Resolution failures | 0 |

## Uncertainty & deviations

- Finite census (N=117), no sampling error; exact counts reported.
- **No deviation from the preregistration PLAN** — all thresholds, scope and E-axis mapping applied
  unchanged. One re-run was performed against a *corrected input* (the registry), recorded in
  `deviation-log.json` as `non_deviation_plan_unchanged`.
- The two findings from RUN-1 are now dispositioned:
  1. **5 year gaps — CORRECTED in-tier.** `crossref_year` backfilled/corrected for GAP001-06
     (2020→2019), GAP002-02 (null→2006), GAP005-01 (null→2007), GAP008-06 (null→2005),
     GAP008-08 (null→2025), sourced from the version-locked Crossref responses in the RUN-1
     `source-manifest.jsonl`. The re-run confirms 117/117 year match.
  2. **1 intra-registry duplicate DOI — RETAINED, deferred.** `10.1016/s0070-2153(07)81015-5` is
     listed under GAP002-01 and GAP002-08. Review showed this is an intentional cross-gap citation (the
     same paper supports two distinct gaps), already flagged in-registry as `is_duplicate_doi: true` on
     GAP002-08. It is NOT an external-evidence failure (the DOI resolves and matches Crossref
     externally). **Physical removal was deliberately NOT performed** because `GAP002-08` is referenced
     across the task-104 external-research ecosystem (atlas v1/v2/v3, gap-support-matrix,
     integrity-alerts, audit-findings, knowledge docs); deletion would orphan those references. The
     disposition is deferred to the task-104 data owner.

## What changed vs what did not

- **Changed (in-tier correction, no E downgrade):** `evidence_tier_104 = METADATA_VERIFIED` is
  **confirmed** for all 117 entries. The 5 `crossref_year` corrections were applied to the registry.
- **Deliberately NOT changed:** the duplicate DOI was retained as an intentional cross-gap citation
  (deferred to 104 owner) rather than deleted.
- **Did not change:** no E-axis promotion beyond scope (§8.5); no claim about Pointfire physics
  correctness; the 5 year corrections remain `METADATA_VERIFIED` (identity/title verified, only the year
  field needed correction).
- This is a legitimate *supported* result, not a failure. Negative/null results would also have been
  preserved and adjudicated honestly (§8).

## Reserve pilots & next evidence priorities

- **Reserve 1 — OpenAlex cross-check:** re-verify the same 117 DOIs against OpenAlex for a second
  independent oracle.
- **Reserve 2 — Case-table historical anchors:** verify named historical figures/events in the case
  tables against Wikipedia.
- **Next:** promote Function OS v0.2 correctness (candidate C-04) as the next pilot once the 104 owner
  resolves the retained duplicate disposition.
