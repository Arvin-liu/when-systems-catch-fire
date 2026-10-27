#!/usr/bin/env python3
"""Adjudicate the sealed task-110 first run under the preregistered rules."""

from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import json
import pathlib
import unicodedata
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent
RUN_DIR = ROOT / "first-run-20260801"
POPULATION = ROOT / "population-manifest.jsonl"
SOURCE = RUN_DIR / "source-manifest.jsonl"
OUT = RUN_DIR / "adjudication.jsonl"
SUMMARY = RUN_DIR / "ADJUDICATION-SUMMARY.json"


def normalize_doi(value: str | None) -> str:
    value = (value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    return value.strip()


def normalize_title(value: str | None) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    return "".join(character for character in value if character.isalnum())


def title_ratio(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def raw_retraction(value: str | None) -> str:
    return (value or "").strip().lower()


def json_line(handle, value: dict) -> None:
    handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def adjudicate(row: dict) -> dict:
    reasons: list[str] = []
    class_name: str
    canonical = None
    title_match = None
    year_match = None
    retraction_match = None
    ratio = None
    delta = None
    null_reason = None

    if row.get("http_status") != 200:
        class_name = "TEST_INVALID_OR_ABORTED"
        null_reason = "http_or_network_failure"
    elif row.get("selection_rationale") == "no_exact_doi_match":
        class_name = "NULL_OR_INCONCLUSIVE"
        null_reason = "no_exact_doi_match"
    elif row.get("selection_rationale") == "multiple_exact_doi_matches":
        class_name = "NULL_OR_INCONCLUSIVE"
        null_reason = "multiple_exact_doi_matches_no_silent_best_guess"
    elif row.get("selection_rationale") != "exact_normalized_doi_match":
        class_name = "NULL_OR_INCONCLUSIVE"
        null_reason = row.get("selection_rationale") or "unknown_selection_state"
    else:
        expected_doi = normalize_doi(row.get("doi_normalized"))
        observed_doi = normalize_doi(row.get("openalex_doi"))
        canonical = bool(observed_doi) and observed_doi == expected_doi
        if not canonical:
            class_name = "NULL_OR_INCONCLUSIVE"
            null_reason = "canonical_doi_mismatch"
        elif row.get("display_name") is None or row.get("publication_year") is None:
            class_name = "NULL_OR_INCONCLUSIVE"
            null_reason = "required_metadata_field_missing"
        else:
            ratio = title_ratio(row["crossref_title"], row["display_name"])
            title_match = ratio >= 0.92
            delta = abs(int(row["publication_year"]) - int(row["crossref_year"]))
            year_match = delta <= 1
            status = raw_retraction(row.get("registry_retraction_status"))
            observed_retracted = row.get("is_retracted")
            if status in {"none", "retracted"} and isinstance(observed_retracted, bool):
                expected_retracted = status == "retracted"
                retraction_match = expected_retracted == observed_retracted
            else:
                class_name = "NULL_OR_INCONCLUSIVE"
                null_reason = "unrecognized_registry_retraction_status_or_missing_oracle_flag"
                retraction_match = None

            if null_reason is None:
                if ratio < 0.75:
                    reasons.append("title_ratio_below_0.75")
                if delta > 1:
                    reasons.append("absolute_year_delta_greater_than_1")
                if retraction_match is False:
                    reasons.append("retraction_flag_mismatch")
                if reasons:
                    class_name = "CONTRADICTED_WITHIN_SCOPE"
                elif delta == 1 or 0.75 <= ratio < 0.92:
                    if delta == 1:
                        reasons.append("online_print_ambiguity_year_delta_1")
                    if 0.75 <= ratio < 0.92:
                        reasons.append("partial_title_match_ratio_0.75_to_0.92")
                    class_name = "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_MISMATCHES"
                else:
                    class_name = "SUPPORTED_WITHIN_SCOPE"

    return {
        "source_id": row["source_id"],
        "position": row["position"],
        "doi_normalized": row["doi_normalized"],
        "is_duplicate_doi": row["is_duplicate_doi"],
        "class": class_name,
        "canonical_id_match": canonical,
        "title_match": title_match,
        "title_ratio": ratio,
        "year_match": year_match,
        "year_delta": delta,
        "retraction_match": retraction_match,
        "mismatch_reasons": reasons,
        "null_reason": null_reason,
        "openalex_work_id": row.get("openalex_work_id"),
        "openalex_doi": row.get("openalex_doi"),
        "openalex_title": row.get("display_name"),
        "openalex_year": row.get("publication_year"),
        "openalex_type": row.get("type"),
        "openalex_is_retracted": row.get("is_retracted"),
        "registry_title": row.get("registry_title"),
        "crossref_title": row.get("crossref_title"),
        "crossref_year": row.get("crossref_year"),
        "registry_retraction_status": row.get("registry_retraction_status"),
        "selection_rationale": row.get("selection_rationale"),
        "http_status": row.get("http_status"),
        "attempts": row.get("attempts"),
        "raw_response_path": row.get("raw_response_path"),
        "raw_response_sha256": row.get("raw_response_sha256"),
        "claim_ceiling": "cross-source bibliographic metadata consistency only",
    }


def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 117:
        raise SystemExit(f"sealed source manifest must contain 117 records, found {len(rows)}")
    results = [adjudicate(row) for row in rows]
    with OUT.open("w", encoding="utf-8") as handle:
        for result in results:
            json_line(handle, result)

    primary = [result for result in results if not result["is_duplicate_doi"]]
    counts = Counter(result["class"] for result in results)
    primary_counts = Counter(result["class"] for result in primary)
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "run_id": "first-run-20260801",
        "population_records": len(results),
        "duplicate_records_excluded_from_primary_rate": len(results) - len(primary),
        "class_counts_all_records": dict(sorted(counts.items())),
        "class_counts_primary_denominator": dict(sorted(primary_counts.items())),
        "primary_denominator": len(primary),
        "primary_supported_or_partial": sum(result["class"] in {"SUPPORTED_WITHIN_SCOPE", "PARTIALLY_SUPPORTED_WITH_IDENTIFIED_MISMATCHES"} for result in primary),
        "primary_hard_contradictions": sum(result["class"] == "CONTRADICTED_WITHIN_SCOPE" for result in primary),
        "primary_null_or_inconclusive": sum(result["class"] == "NULL_OR_INCONCLUSIVE" for result in primary),
        "primary_invalid_or_aborted": sum(result["class"] == "TEST_INVALID_OR_ABORTED" for result in primary),
        "source_manifest_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "adjudication_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
        "protocol": "task-110 OpenAlex preregistration; first sealed run; no correction or rerun",
        "claim_ceiling": "cross-source bibliographic metadata consistency only",
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
