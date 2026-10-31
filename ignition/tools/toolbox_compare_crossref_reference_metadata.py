#!/usr/bin/env python3
"""Compare selected Crossref reference rows with their source and target Work records."""

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
TOOL_VERSION = "0.2.0"
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
    required_keys = {"source_work_doi", "references"}
    allowed_keys = required_keys | {"verify_source_link"}
    if not isinstance(document, dict) or not required_keys <= set(document) or not set(document) <= allowed_keys:
        raise ToolInputError("request must contain source_work_doi and references, plus optional verify_source_link")
    verify_source_link = document.get("verify_source_link", False)
    if type(verify_source_link) is not bool:
        raise ToolInputError("verify_source_link must be a boolean")

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

    return {
        "source_work_doi": source_work_doi,
        "references": normalized,
        "verify_source_link": verify_source_link,
    }


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


def _fetch_source_work(request: dict[str, Any]) -> dict[str, Any]:
    fetched = crossref._fetch_one(request["source_work_doi"])
    state: dict[str, Any] = {
        "request_attempted": True,
        "source_work_doi": request["source_work_doi"],
        "acquisition_status": fetched["acquisition_status"],
        "http_status": fetched["http_status"],
        "response_sha256": None,
        "status": "SOURCE_WORK_ACQUISITION_FAILED",
        "reported_reference_count": None,
        "raw_reference_rows": [],
    }
    if fetched["acquisition_status"] != "OK":
        return state

    body = fetched["body"]
    state["response_sha256"] = hashlib.sha256(body).hexdigest()
    try:
        document = json.loads(body.decode("utf-8", errors="strict"), object_pairs_hook=crossref._strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError, crossref.ToolInputError):
        state["acquisition_status"] = "INVALID_JSON_RESPONSE"
        state["status"] = "SOURCE_WORK_INVALID_JSON"
        return state
    message = document.get("message") if isinstance(document, dict) else None
    if not isinstance(message, dict):
        state["acquisition_status"] = "INVALID_CROSSREF_MESSAGE"
        state["status"] = "SOURCE_WORK_INVALID_MESSAGE"
        return state

    source_work = _work_projection(message)
    if source_work["doi"] is None:
        state["source_work_identity_status"] = "WORK_DOI_NOT_REPORTED"
    elif source_work["doi"].lower() == request["source_work_doi"].lower():
        state["source_work_identity_status"] = "EXACT_DOI_MATCH"
    else:
        state["source_work_identity_status"] = "RETURNED_DOI_DIFFERS"
    if state["source_work_identity_status"] != "EXACT_DOI_MATCH":
        state["status"] = "SOURCE_WORK_DOI_IDENTITY_UNRESOLVED"
        return state
    if "reference" not in message:
        state["status"] = "SOURCE_REFERENCES_NOT_REPORTED"
        return state
    raw_rows = message["reference"]
    if not isinstance(raw_rows, list):
        state["status"] = "SOURCE_REFERENCES_MALFORMED"
        return state
    state["reported_reference_count"] = len(raw_rows)
    state["raw_reference_rows"] = raw_rows
    state["status"] = "SOURCE_RECORD_READY"
    return state


def _source_reference_binding(reference: dict[str, Any], source_state: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": source_state["status"],
        "reference_key": reference["key"],
        "source_reference_metadata": None,
        "source_field_comparisons": {},
    }
    if source_state["status"] != "SOURCE_RECORD_READY":
        return result

    matches = [
        item for item in source_state["raw_reference_rows"]
        if isinstance(item, dict)
        and crossref._reference_text(item.get("key"), max_length=MAX_REFERENCE_KEY_LENGTH) == reference["key"]
    ]
    if not matches:
        result["status"] = "SOURCE_REFERENCE_KEY_NOT_FOUND"
        return result
    if len(matches) != 1:
        result["status"] = "SOURCE_REFERENCE_KEY_AMBIGUOUS"
        return result

    projection = crossref._parse_reference_rows({"reference": [matches[0]]})
    if not projection["rows"]:
        result["status"] = "SOURCE_REFERENCE_ROW_MALFORMED"
        return result
    source_reference = projection["rows"][0]
    result["source_reference_metadata"] = source_reference
    source_doi = source_reference.get("doi")
    if source_doi is None:
        result["status"] = "SOURCE_REFERENCE_DOI_NOT_REPORTED"
        return result
    if source_doi.lower() != reference["doi"].lower():
        result["status"] = "SOURCE_REFERENCE_DOI_MISMATCH"
        return result

    source_work_projection = {
        "article_title": source_reference.get("article_title"),
        "year": source_reference.get("year"),
        "journal_title": source_reference.get("journal_title"),
        "volume": source_reference.get("volume"),
        "issue": source_reference.get("issue"),
        "first_page": source_reference.get("first_page"),
    }
    result["status"] = "SOURCE_REFERENCE_DOI_MATCH"
    result["source_field_comparisons"] = _field_comparisons(reference, source_work_projection)
    return result


def _compare_one(
    reference: dict[str, Any],
    *,
    source_binding: dict[str, Any] | None = None,
    verify_source_link: bool = False,
) -> dict[str, Any]:
    retrieved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    source_binding = source_binding or {
        "status": "NOT_REQUESTED",
        "reference_key": reference["key"],
        "source_reference_metadata": None,
        "source_field_comparisons": {},
    }
    result: dict[str, Any] = {
        "reference_key": reference["key"],
        "reference_doi": reference["doi"],
        "reference_fields": {key: value for key, value in reference.items() if key not in {"key", "doi"}},
        "retrieval_timestamp_utc": retrieved_at,
        "source_reference_binding": source_binding,
        "source_url": None,
        "target_request_attempted": False,
        "acquisition_status": "NOT_ATTEMPTED",
        "http_status": None,
        "response_sha256": None,
        "crossref_work": None,
        "doi_identity_status": "NOT_CHECKED",
        "field_comparisons": {},
    }
    if verify_source_link and source_binding["status"] != "SOURCE_REFERENCE_DOI_MATCH":
        result["comparison_status"] = "NOT_COMPARED_SOURCE_REFERENCE_NOT_BOUND"
        return result

    result["source_url"] = crossref.API_BASE + urllib.parse.quote(reference["doi"], safe="")
    result["target_request_attempted"] = True
    fetched = crossref._fetch_one(reference["doi"])
    result.update({
        "acquisition_status": fetched["acquisition_status"],
        "http_status": fetched["http_status"],
    })
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
    source_state = _fetch_source_work(request) if request["verify_source_link"] else None
    rows: list[dict[str, Any]] = []
    for index, reference in enumerate(request["references"]):
        binding = _source_reference_binding(reference, source_state) if source_state is not None else None
        rows.append(_compare_one(
            reference,
            source_binding=binding,
            verify_source_link=request["verify_source_link"],
        ))
        if index + 1 < len(request["references"]):
            time.sleep(0.1)
    failures = sum(row["acquisition_status"] not in {"OK", "NOT_ATTEMPTED"} for row in rows)
    identity_failures = sum(row["doi_identity_status"] != "EXACT_DOI_MATCH" for row in rows if row["acquisition_status"] == "OK")
    differences = sum(row["comparison_status"] == "FIELD_DIFFERENCES_OBSERVED" for row in rows)
    no_comparable_fields = sum(row["comparison_status"] == "NO_COMPARABLE_REFERENCE_FIELDS" for row in rows)
    source_binding_failures = sum(
        row["source_reference_binding"]["status"] != "SOURCE_REFERENCE_DOI_MATCH"
        for row in rows
    ) if request["verify_source_link"] else 0
    source_acquisition_failure_count = int(
        source_state is not None and source_state["acquisition_status"] != "OK"
    )
    source_work_verification_failure_count = int(
        source_state is not None
        and source_state["acquisition_status"] == "OK"
        and source_state["status"] != "SOURCE_RECORD_READY"
    )
    if (
        failures
        or identity_failures
        or source_binding_failures
        or source_acquisition_failure_count
        or source_work_verification_failure_count
    ):
        status = "COMPLETED_WITH_EXPLICIT_FAILURES"
    elif no_comparable_fields == len(rows):
        status = "NO_COMPARABLE_REFERENCE_FIELDS"
    elif differences:
        status = "FIELD_DIFFERENCES_OBSERVED"
    else:
        status = "COMPLETED_WITHOUT_FIELD_DIFFERENCES"
    return {
        "schema_version": "ignition.crossref-reference-metadata-comparison-r1",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "source_work_doi": request["source_work_doi"],
        "source_work_doi_status": (
            "CALLER_DECLARED_NOT_AUTHENTICATED_OR_FETCHED"
            if source_state is None
            else source_state.get("source_work_identity_status", "NOT_VERIFIED")
        ),
        "record_count": len(rows),
        "request_count": int(source_state is not None) + sum(row["target_request_attempted"] for row in rows),
        "acquisition_failure_count": failures,
        "doi_identity_failure_count": identity_failures,
        "source_binding_mode": "VERIFY" if source_state is not None else "NOT_REQUESTED",
        "source_work_verification": None if source_state is None else {
            key: value for key, value in source_state.items() if key != "raw_reference_rows"
        },
        "source_acquisition_failure_count": source_acquisition_failure_count,
        "source_work_verification_failure_count": source_work_verification_failure_count,
        "source_reference_binding_failure_count": source_binding_failures,
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
            "volume, issue, and first-page values. A difference is not proof of an incorrect citation. "
            "When verify_source_link=true, make one additional fixed-host request "
            "to check whether each selected key and DOI occurs in the source Work's Crossref-deposited references, "
            "then compare supplied fields with that row. This does not establish publisher/source authenticity, "
            "citation correctness, bibliography completeness, article content, or scientific support."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read the bounded JSON input contract from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="authorize up to six fixed-host Crossref HTTPS GET requests: one source Work plus up to five cited Works")
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
