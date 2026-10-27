# Preregistration Protocol — Crossref DOI Re-verification Pilot (Task 103 §5)

**Pilot ID:** `IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION`
**Preregistration ID:** `PREREG-103-R1-CROSSREF`
**Status:** PRE-REGISTERED — committed and pushed BEFORE any Crossref query (see run-manifest for the canonical commit SHA and timestamp).

> This document is the human-readable counterpart of
> `IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION.prereg.json`. The machine
> file is authoritative for validation; this file explains it in plain language.

## What we are testing

The repository's external-source registry (`data/external-research/104-source-registry.jsonl`)
contains 117 source records, each asserting `crossref_verified: true` together with a
recorded `crossref_title` and `crossref_year`. We will **independently re-query the
public Crossref REST API** for each DOI and check whether the external authority
agrees with what the registry claims.

This is a **bounded metadata-integrity claim**, not a physics claim. It is allowed by
§3.9 (no grand-physics claim chosen for narrative). A real external oracle (Crossref)
is used, so the result is genuine external evidence, not internal consistency.

## Hypotheses

- **Claim:** every `crossref_verified: true` record resolves via Crossref with a
  title and year matching the registry, and is not retracted or duplicate.
- **Null / comparison:** the registry's own assertion is the baseline; Crossref is the
  independent comparator. "Verified" requires resolution + title-match + year-match +
  no-retraction + no-duplicate, all simultaneously.

## Scope & exclusions

- **In scope:** all 117 records; primary metric over the `crossref_verified: true` subset.
- **Excluded:** no assessment of article *content* or of Pointfire physics correctness;
  DOIs that cannot be parsed are reported as `PARSE_FAILED`, never silently dropped.

## Data & acquisition

- **Source:** `data/external-research/104-source-registry.jsonl` (117 records).
- **Oracle:** Crossref REST API `https://api.crossref.org/works/{bare_doi}`.
- **Identity:** each DOI is an immutable identifier (stripped from the `https://doi.org/...` form).
- **Licence:** Crossref metadata is CC0; raw redistribution permitted.
- **Retrieval:** recorded per-DOI with UTC timestamp and response SHA-256.
- **Failure handling:** network/non-200 outcomes are recorded explicitly and never
  substituted with cached or different data (relay §6).

## Baseline

The registry's own `crossref_verified: true`, `crossref_title`, `crossref_year`
(the repository's prior metadata claim) is the baseline we compare against.

## Metrics

- **Primary:** `verification_match_rate` = (# fully-matching records) / (# claiming verified).
- **Secondary:** resolution_rate, title_match_rate, year_match_rate,
  retraction_signal_count, intra_registry_duplicate_doi_count, resolution_failure_count.

## Uncertainty

N=117 is a full census (no sampling error). The only measurement uncertainty is
title normalization (case/punctuation/whitespace); we report exact counts and also a
sensitivity check under loose-containment matching.

## Decision thresholds (fixed before seeing results)

| Outcome | Condition |
| --- | --- |
| **SUPPORTED_WITHIN_SCOPE** | verification_match_rate ≥ 0.95 AND retraction_signals = 0 AND intra_registry_duplicate_dois = 0 |
| **PARTIALLY_SUPPORTED** | 0.80 ≤ rate < 0.95 |
| **NULL_OR_INCONCLUSIVE** | rate < 0.80 but failures due to matching ambiguity / network, not concrete metadata error; or resolution_rate < 0.90 |
| **CONTRADICTED_WITHIN_SCOPE** | rate < 0.80 with concrete title/year mismatches (METADATA_VERIFIED not warranted) |
| **TEST_INVALID_OR_ABORTED** | Crossref unreachable / persistent policy block / script error preventing valid queries |

## Stopping rule

All 117 DOIs attempted. On HTTP 429, bounded exponential backoff (max 4 attempts).
Persistent block or total failure ⇒ abort as TEST_INVALID_OR_ABORTED; no fabrication.

## E-axis / disposition mapping

- **Supported** → confirm `METADATA_VERIFIED` for passing entries; positive provenance note.
- **Partial** → downgrade failing entries to `METADATA_UNCONFIRMED`; keep others; limitation note.
- **Null** → retain E0-equivalent (no promotion); limitation note.
- **Contradicted** → downgrade failing entries; limitation note on atlas reliability; propagate.
- **Invalid** → retain E0-equivalent; record blocked acquisition as a limitation, not a claim failure.

## Amendment rule

Any change to the above after result generation is a deviation and must be appended to
the deviation log with a timestamp — it never overwrites this plan (§5.10).
