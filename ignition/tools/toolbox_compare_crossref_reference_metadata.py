#!/usr/bin/env python3
"""Compare caller-supplied Crossref reference rows with DOI-resolved Work metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
TOOLS_DIR = HERE.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import toolbox_crossref_metadata_verifier as crossref  # noqa: E402


TOOL_ID = "research.compare_crossref_reference_metadata"
TOOL_VERSION = "0.1.0"
MAX_REQUEST_BYTES = 32 * 1024
MAX_REFERENCE_ROWS = 5
MAX_REFERENCE_KEY_LENGTH = 96
MAX_TEXT_LENGTH = 256
ALLOWED_REFERENCE_FIELDS = {
    "key",
    "doi",
    "article_title",
    "year",
    "journal_title",
    "volume",
    "issue",
    "first_page",
}
STRING_FIELDS = ("article_title", "journal_title", "volume", "issue", "first_page")
FIELD_MAP = {
    "article_title": "article_title",
    "year": "year",
    "journal_title": "journal_title",
    "volume": "volume",
    "issue": "issue",
    "first_page": "first_page",
}
KEY_RE = re.compile(r"[A-Za-z0-9._:-]+\Z")


class ToolInputError(ValueError):
    """Raised when the bounded citation comparison input is invalid."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _safe_input_text(value: Any, name: str, *, max_length: int = MAX_TEXT_LENGTH) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= max_length:
        raise ToolInputError(f"{name} must be a nonempty string of at most {max_length} characters")
    if value != value.strip() or any(ord(char) < 32 for char in value):
        raise ToolInputError(f"{name} must not contain surrounding whitespace or control characters")
    return value


def parse_request(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except ToolInputError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) != {"source_work_doi", "references"}:
        raise ToolInputError("request must contain exactly source_work_doi and references")

    source_work_doi = document["source_work_doi"]
    if (
        not isinstance(source_work_doi, str)
        or len(source_work_doi) > crossref.MAX_DOI_LENGTH
        or source_work_doi != source_work_doi.strip()
        or not crossref.DOI_RE.fullmatch(source_work_doi)
    ):
        raise ToolInputError("source_work_doi must be one bare DOI identifier")

    references = document["references"]
    if not isinstance(references, list) or not 1 <= len(references) <= MAX_REFERENCE_ROWS:
        raise ToolInputError(f"references must contain between 1 and {MAX_REFERENCE_ROWS} rows")

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_dois: set[str] = set()
    for index, row in enumerate(references):
        if not isinstance(row, dict) or not {"key", "doi"} <= set(row) or not set(row) <= ALLOWED_REFERENCE_FIELDS:
            raise ToolInputError(f"references[{index}] must contain key and doi plus only supported citation fields")
        key = _safe_input_text(row["key"], f"references[{index}].key", max_length=MAX_REFERENCE_KEY_LENGTH)
        if not KEY_RE.fullmatch(key):
            raise ToolInputError(f"references[{index}].key contains unsupported characters")
        doi = row["doi"]
        if (
            not isinstance(doi, str)
            or len(doi) > crossref.MAX_DOI_LENGTH
            or doi != doi.strip()
            or not crossref.DOI_RE.fullmatch(doi)
        ):
            raise ToolInputError(f"references[{index}].doi must be one bare DOI identifier")
        if key in seen_keys or doi.lower() in seen_dois:
            raise ToolInputError("reference keys and DOI values must be unique")
        seen_keys.add(key)
        seen_dois.add(doi.lower())

        item: dict[str, Any] = {"key": key, "doi": doi}
        for field in STRING_FIELDS:
            if field in row:
                item[field] = _safe_input_text(row[field], f"references[{index}].{field}")
        if "year" in row:
            year = row["year"]
            if type(year) is not int or not 1000 <= year <= 2200:
                raise ToolInputError(f"references[{index}].year must be an integer from 1000 through 2200")
            item["year"] = year
        normalized.append(item)

    return {"source_work_doi": source_work_doi, "references": normalized}


def _first_text(message: dict[str, Any], key: str) -> str | None:
    value = message.get(key)
    if isinstance(value, list) and value and isinstance(value[0], str):
        text = value[0]
    elif isinstance(value, str):
        text = value
    else:
        return None
    text = text.strip()
    if not text or len(text) > MAX_TEXT_LENGTH or re.search(r"https?://", text, flags=re.IGNORECASE):
        return None
    return text


def _safe_scalar(message: dict[str, Any], key: str) -> str | None:
    value = message.get(key)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > MAX_TEXT_LENGTH or re.search(r"https?://", value, flags=re.IGNORECASE):
        return None
    return value


def _page_first(page: str | None) -> str | None:
    if page is None:
        return None
    match = re.match(r"\s*([A-Za-z0-9]+)", page)
    return match.group(1) if match else None


def _work_projection(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "doi": _safe_scalar(message, "DOI"),
        "article_title": _first_text(message, "title"),
        "year": crossref.UPSTREAM.extract_year(message),
        "journal_title": _first_text(message, "container-title"),
        "volume": _safe_scalar(message, "volume"),
        "issue": _safe_scalar(message, "issue"),
        "page": _safe_scalar(message, "page"),
        "first_page": _page_first(_safe_scalar(message, "page")),
    }


def _field_comparisons(reference: dict[str, Any], work: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for reference_field, work_field in FIELD_MAP.items():
        if reference_field not in reference:
            continue
        expected = reference[reference_field]
        observed = work.get(work_field)
        if observed is None:
            status = "WORK_FIELD_NOT_REPORTED"
        elif reference_field == "year":
            status = "NORMALIZED_EQUAL" if expected == observed else "NORMALIZED_DIFFERENT"
        else:
            status = (
                "NORMALIZED_EQUAL"
                if crossref.UPSTREAM.norm(expected) == crossref.UPSTREAM.norm(observed)
                else "NORMALIZED_DIFFERENT"
            )
        comparisons[reference_field] = {
            "reference_value": expected,
            "work_value": observed,
            "status": status,
        }
    return comparisons


def _row_status(acquisition_status: str, comparisons: dict[str, Any]) -> str:
    if acquisition_status != "OK":
        return "NOT_COMPARED_ACQUISITION_FAILED"
    statuses = [item["status"] for item in comparisons.values()]
    if not statuses:
        return "NO_COMPARABLE_REFERENCE_FIELDS"
    if "NORMALIZED_DIFFERENT" in statuses:
        return "FIELD_DIFFERENCES_OBSERVED"
    if "WORK_FIELD_NOT_REPORTED" in statuses:
        return "PARTIAL_COMPARISON"
    return "ALL_PROVIDED_FIELDS_NORMALIZED_EQUAL"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compare_one(reference: dict[str, Any]) -> dict[str, Any]:
    retrieved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fetched = crossref._fetch_one(reference["doi"])
    result: dict[str, Any] = {
        "reference_key": reference["key"],
        "reference_doi": reference["doi"],
        "reference_fields": {key: value for key, value in reference.items() if key not in {"key", "doi"}},
        "retrieval_timestamp_utc": retrieved_at,
        "source_url": crossref.API_BASE + urllib.parse.quote(reference["doi"], safe=""),
        "acquisition_status": fetched["acquisition_status"],
        "http_status": fetched["http_status"],
        "response_sha256": None,
        "crossref_work": None,
        "doi_identity_status": "NOT_CHECKED",
        "field_comparisons": {},
    }
    if fetched["acquisition_status"] != "OK":
        result["comparison_status"] = _row_status(fetched["acquisition_status"], {})
        return result

    body = fetched["body"]
    result["response_sha256"] = hashlib.sha256(body).hexdigest()
    try:
        document = json.loads(body.decode("utf-8", errors="strict"), object_pairs_hook=crossref._strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError, crossref.ToolInputError):
        result["acquisition_status"] = "INVALID_JSON_RESPONSE"
        result["comparison_status"] = _row_status(result["acquisition_status"], {})
        return result
    message = document.get("message") if isinstance(document, dict) else None
    if not isinstance(message, dict):
        result["acquisition_status"] = "INVALID_CROSSREF_MESSAGE"
        result["comparison_status"] = _row_status(result["acquisition_status"], {})
        return result

    work = _work_projection(message)
    if work["doi"] is None:
        result["doi_identity_status"] = "WORK_DOI_NOT_REPORTED"
    elif work["doi"].lower() == reference["doi"].lower():
        result["doi_identity_status"] = "EXACT_DOI_MATCH"
    else:
        result["doi_identity_status"] = "RETURNED_DOI_DIFFERS"
    result["crossref_work"] = work
    if result["doi_identity_status"] != "EXACT_DOI_MATCH":
        result["comparison_status"] = "NOT_COMPARED_DOI_IDENTITY_UNRESOLVED"
        return result
    result["field_comparisons"] = _field_comparisons(reference, work)
    result["comparison_status"] = _row_status("OK", result["field_comparisons"])
    return result


def compare(request: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, reference in enumerate(request["references"]):
        rows.append(_compare_one(reference))
        if index + 1 < len(request["references"]):
            time.sleep(0.1)
    failures = sum(row["acquisition_status"] != "OK" for row in rows)
    identity_failures = sum(row["doi_identity_status"] != "EXACT_DOI_MATCH" for row in rows if row["acquisition_status"] == "OK")
    differences = sum(row["comparison_status"] == "FIELD_DIFFERENCES_OBSERVED" for row in rows)
    no_comparable_fields = sum(row["comparison_status"] == "NO_COMPARABLE_REFERENCE_FIELDS" for row in rows)
    if failures or identity_failures:
        status = "COMPLETED_WITH_EXPLICIT_FAILURES"
    elif no_comparable_fields == len(rows):
        status = "NO_COMPARABLE_REFERENCE_FIELDS"
    elif differences:
        status = "FIELD_DIFFERENCES_OBSERVED"
    else:
        status = "COMPLETED_WITHOUT_FIELD_DIFFERENCES"
    return {
        "schema_version": "ignition.crossref-reference-metadata-comparison-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "source_work_doi": request["source_work_doi"],
        "source_work_doi_status": "CALLER_DECLARED_NOT_AUTHENTICATED_OR_FETCHED",
        "record_count": len(rows),
        "request_count": len(rows),
        "acquisition_failure_count": failures,
        "doi_identity_failure_count": identity_failures,
        "rows_with_field_differences": differences,
        "rows_without_comparable_reference_fields": no_comparable_fields,
        "rows": rows,
        "source_code_sha256": {
            "wrapper": _sha256_file(HERE),
            "crossref_metadata_verifier": _sha256_file(Path(crossref.__file__).resolve()),
            "task103_crossref_helpers": _sha256_file(crossref.UPSTREAM_HELPERS_PATH),
        },
        "claim_ceiling": (
            "For up to five caller-supplied Crossref reference rows, retrieve the exact cited DOI Work metadata from "
            "api.crossref.org and report normalized field equality or difference for supplied title, year, journal, "
            "volume, issue, and first-page values. A difference is not proof of an incorrect citation; a match does "
            "not establish source authenticity, bibliography completeness, article content, or scientific support. "
            "The source-work DOI and projection provenance are caller declarations only."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read the bounded JSON input contract from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="authorize up to five fixed-host Crossref HTTPS GET requests")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        print("PUBLIC_NETWORK_CALL_REQUIRES --allow-public-network", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        request = parse_request(raw)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(compare(request), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
