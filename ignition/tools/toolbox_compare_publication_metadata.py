#!/usr/bin/env python3
"""Compare title/year fields in caller-supplied Crossref and OpenAlex results.

This local post-processor performs no network access and does not authenticate
either result. It reports only field agreement, disagreement, or missing data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


TOOL_ID = "research.compare_publication_metadata_snapshots"
TOOL_VERSION = "0.1.0"
SCHEMA_VERSION = "ignition.publication-metadata-comparison-input-r0"
MAX_INPUT_BYTES = 262_144
MAX_TITLE_LENGTH = 500
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
CROSSREF_TOOL_ID = "research.verify_crossref_metadata"
OPENALEX_TOOL_ID = "research.lookup_openalex_work_metadata"


class InputError(ValueError):
    """Raised when the JSON envelope or source results violate the contract."""


def _strict_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise InputError("non-standard JSON constant")


def _normalize_doi(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    doi = value.strip()
    lowered = doi.casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
        if lowered.startswith(prefix):
            doi = doi[len(prefix):]
            break
    doi = doi.casefold()
    return doi if DOI_RE.fullmatch(doi) else None


def _load_sha(value: Any, field: str, *, required: bool) -> Optional[str]:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise InputError("{} must be a lowercase SHA-256 digest{}".format(field, " or null" if not required else ""))
    return value


def _load_title(value: Any, field: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > MAX_TITLE_LENGTH:
        raise InputError("{} must be null or a string no longer than {} characters".format(field, MAX_TITLE_LENGTH))
    return value if value.strip() else None


def _load_year(value: Any, field: str) -> Optional[int]:
    if value is None:
        return None
    if type(value) is not int or value < 1000 or value > 9999:
        raise InputError("{} must be null or a four-digit integer".format(field))
    return value


def _result_rows(result: Any, *, tool_id: str, schema_version: str) -> List[Dict[str, Any]]:
    if not isinstance(result, dict):
        raise InputError("{} result must be an object".format(tool_id))
    if result.get("tool_id") != tool_id or result.get("tool_version") != "0.1.0":
        raise InputError("{} result has an unsupported tool identity or version".format(tool_id))
    if result.get("schema_version") != schema_version:
        raise InputError("{} result has an unsupported schema_version".format(tool_id))
    rows = result.get("rows")
    if not isinstance(rows, list) or len(rows) > 10 or not rows or any(not isinstance(row, dict) for row in rows):
        raise InputError("{} result must contain one to ten object rows".format(tool_id))
    return rows


def _crossref_snapshot(result: Dict[str, Any], requested_doi: str) -> Dict[str, Any]:
    rows = _result_rows(
        result,
        tool_id=CROSSREF_TOOL_ID,
        schema_version="ignition.crossref-metadata-verification-r0",
    )
    matches = [row for row in rows if _normalize_doi(row.get("canonical_identifier")) == requested_doi]
    if len(matches) != 1:
        raise InputError("Crossref result must contain exactly one row for the requested DOI")
    row = matches[0]
    acquisition = row.get("acquisition_status")
    if not isinstance(acquisition, str) or len(acquisition) > 64:
        raise InputError("Crossref acquisition_status is invalid")
    response_sha = _load_sha(row.get("response_sha256"), "Crossref response_sha256", required=acquisition == "OK")
    usable = acquisition == "OK"
    return {
        "tool_id": CROSSREF_TOOL_ID,
        "acquisition_status": acquisition,
        "record_status": "METADATA_ROW_RETURNED" if usable else "NOT_AVAILABLE",
        "provider_response_sha256": response_sha,
        "title": _load_title(row.get("observed_title"), "Crossref observed_title") if usable else None,
        "publication_year": _load_year(row.get("observed_year"), "Crossref observed_year") if usable else None,
    }


def _openalex_snapshot(result: Dict[str, Any], requested_doi: str) -> Dict[str, Any]:
    rows = _result_rows(
        result,
        tool_id=OPENALEX_TOOL_ID,
        schema_version="ignition.openalex-work-metadata-lookup-r0",
    )
    matches = [row for row in rows if _normalize_doi(row.get("requested_doi")) == requested_doi]
    if len(matches) != 1:
        raise InputError("OpenAlex result must contain exactly one row for the requested DOI")
    row = matches[0]
    acquisition = result.get("acquisition_status")
    if not isinstance(acquisition, str) or len(acquisition) > 64:
        raise InputError("OpenAlex acquisition_status is invalid")
    row_status = row.get("status")
    if not isinstance(row_status, str) or len(row_status) > 64:
        raise InputError("OpenAlex row status is invalid")
    response_sha = _load_sha(result.get("response_sha256"), "OpenAlex response_sha256", required=acquisition == "OK")
    usable = acquisition == "OK" and row_status == "EXACT_PRIMARY_DOI_MATCH"
    if usable and _normalize_doi(row.get("openalex_doi")) != requested_doi:
        raise InputError("OpenAlex exact-match row does not carry the requested primary DOI")
    return {
        "tool_id": OPENALEX_TOOL_ID,
        "acquisition_status": acquisition,
        "record_status": row_status if acquisition == "OK" else "NOT_AVAILABLE",
        "provider_response_sha256": response_sha,
        "title": _load_title(row.get("title"), "OpenAlex title") if usable else None,
        "publication_year": _load_year(row.get("publication_year"), "OpenAlex publication_year") if usable else None,
    }


def _normalize_title(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _compare_field(key: str, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
    observations = [
        {"tool_id": row["tool_id"], "value": row[key]}
        for row in snapshots
    ]
    values = [row[key] for row in snapshots]
    if any(value is None for value in values):
        status = "INSUFFICIENT"
    elif key == "title":
        status = "AGREE" if len({_normalize_title(value) for value in values}) == 1 else "DISAGREE"
    else:
        status = "AGREE" if len(set(values)) == 1 else "DISAGREE"
    return {"status": status, "observations": observations}


def _parse_input(raw: bytes) -> Tuple[str, List[Dict[str, Any]]]:
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("request exceeds the byte limit")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise InputError("request must be valid UTF-8 JSON with unique keys") from exc
    if not isinstance(document, dict) or set(document) != {"schema_version", "doi", "source_results"}:
        raise InputError("request must contain exactly schema_version, doi, and source_results")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise InputError("unsupported request schema_version")
    supplied_doi = document.get("doi")
    doi = _normalize_doi(supplied_doi)
    if doi is None or not isinstance(supplied_doi, str) or supplied_doi != supplied_doi.strip() or not DOI_RE.fullmatch(supplied_doi):
        raise InputError("doi must be a bare DOI identifier without surrounding whitespace")
    source_results = document.get("source_results")
    if not isinstance(source_results, list) or len(source_results) != 2:
        raise InputError("source_results must contain exactly one Crossref and one OpenAlex result")
    by_id: Dict[str, Dict[str, Any]] = {}
    for source in source_results:
        if not isinstance(source, dict) or set(source) != {"tool_id", "result"}:
            raise InputError("each source result must contain exactly tool_id and result")
        tool_id = source.get("tool_id")
        if tool_id not in {CROSSREF_TOOL_ID, OPENALEX_TOOL_ID} or tool_id in by_id:
            raise InputError("source_results must contain each supported tool exactly once")
        if not isinstance(source.get("result"), dict):
            raise InputError("source result payload must be an object")
        by_id[tool_id] = source["result"]
    if set(by_id) != {CROSSREF_TOOL_ID, OPENALEX_TOOL_ID}:
        raise InputError("source_results must contain both Crossref and OpenAlex")
    snapshots = [
        _crossref_snapshot(by_id[CROSSREF_TOOL_ID], doi),
        _openalex_snapshot(by_id[OPENALEX_TOOL_ID], doi),
    ]
    return doi, snapshots


def compare(raw: bytes) -> Dict[str, Any]:
    doi, snapshots = _parse_input(raw)
    title = _compare_field("title", snapshots)
    year = _compare_field("publication_year", snapshots)
    if "DISAGREE" in {title["status"], year["status"]}:
        status = "METADATA_DISAGREEMENT_FOUND"
    elif title["status"] == "AGREE" and year["status"] == "AGREE":
        status = "METADATA_FIELDS_AGREE"
    else:
        status = "INSUFFICIENT_METADATA"
    return {
        "schema_version": "ignition.publication-metadata-cross-source-comparison-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "requested_doi": doi,
        "status": status,
        "source_count": len(snapshots),
        "source_outcomes": snapshots,
        "field_comparisons": {"title": title, "publication_year": year},
        "claim_ceiling": (
            "Compares selected title/year fields in caller-supplied Crossref and OpenAlex result objects. "
            "The inputs and provider responses are not authenticated; agreement does not establish source "
            "authenticity, publication identity beyond these fields, article content, scientific truth, or "
            "retraction status."
        ),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read bounded adapter-result JSON from stdin")
    args = parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = compare(raw)
    except InputError as exc:
        print("INVALID_REQUEST: {}".format(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
