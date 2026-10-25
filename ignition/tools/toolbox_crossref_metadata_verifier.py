#!/usr/bin/env python3
"""Verify caller-supplied DOI title/year metadata against Crossref, stdout only.

This is an opt-in public-network query adapter around the deterministic
normalization helpers used by the Task 103 Crossref pilot. It performs no
registry updates, repository writes, content retrieval, or scientific review.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


TOOL_VERSION = "0.3.0"
API_BASE = "https://api.crossref.org/works/"
API_HOST = "api.crossref.org"
MAX_REQUEST_BYTES = 32 * 1024
MAX_RECORDS = 10
MAX_DOI_LENGTH = 128
MAX_SOURCE_ID_LENGTH = 64
MAX_TITLE_LENGTH = 512
MAX_RESPONSE_BYTES = 256 * 1024
REQUEST_TIMEOUT_SECONDS = 5
MAX_RESPONSE_DURATION_SECONDS = 7
RESPONSE_CHUNK_BYTES = 8 * 1024
MAX_UPDATE_ROWS_PER_KIND = 25
MAX_RELATION_TYPES = 32
MAX_RELATION_ROWS = 50
MAX_RELATION_TEXT_LENGTH = 128
MAX_REFERENCE_ROWS = 25
MAX_REFERENCE_TEXT_LENGTH = 384
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
SOURCE_ID_RE = re.compile(r"[A-Za-z0-9._:-]+\Z")

IGNITION_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_HELPERS_PATH = IGNITION_ROOT / "evidence-program/tools/run_crossref_verification.py"
UPSTREAM_HELPERS_SHA256 = "51df778b6a5a39f58e93b94fc4e8fbe85b6a246a7a13238f4a17e908673e9c51"


class ToolInputError(ValueError):
    """Raised when a request does not match the bounded input contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent a fixed-host query from following a redirect to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_upstream_helpers() -> Any:
    if not UPSTREAM_HELPERS_PATH.is_file() or UPSTREAM_HELPERS_PATH.is_symlink():
        raise RuntimeError("Task103 Crossref helper source is missing or is a symlink")
    if _sha256(UPSTREAM_HELPERS_PATH) != UPSTREAM_HELPERS_SHA256:
        raise RuntimeError("Task103 Crossref helper source SHA-256 does not match the tested dependency")
    spec = importlib.util.spec_from_file_location("ignition_crossref_verification_helpers", UPSTREAM_HELPERS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Task103 Crossref helper module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("norm", "extract_year", "retraction_signal"):
        if not callable(getattr(module, name, None)):
            raise RuntimeError(f"Task103 Crossref helper is missing {name}")
    return module


UPSTREAM = _load_upstream_helpers()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def parse_request(raw: bytes) -> list[dict[str, Any]]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) != {"records"}:
        raise ToolInputError("request must be an object with exactly one key: records")
    records = document["records"]
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        raise ToolInputError(f"records must contain between 1 and {MAX_RECORDS} entries")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_dois: set[str] = set()
    for index, row in enumerate(records):
        if not isinstance(row, dict) or set(row) != {"source_id", "doi", "expected_title", "expected_year"}:
            raise ToolInputError(f"records[{index}] must contain exactly source_id, doi, expected_title, expected_year")
        source_id = row["source_id"]
        doi = row["doi"]
        title = row["expected_title"]
        year = row["expected_year"]
        if not isinstance(source_id, str) or not 1 <= len(source_id) <= MAX_SOURCE_ID_LENGTH or not SOURCE_ID_RE.fullmatch(source_id):
            raise ToolInputError(f"records[{index}].source_id is invalid")
        if not isinstance(doi, str) or len(doi) > MAX_DOI_LENGTH or doi != doi.strip() or not DOI_RE.fullmatch(doi):
            raise ToolInputError(f"records[{index}].doi must be one bare DOI identifier")
        if not isinstance(title, str) or not title.strip() or len(title) > MAX_TITLE_LENGTH:
            raise ToolInputError(f"records[{index}].expected_title is invalid")
        if type(year) is not int or not 1000 <= year <= 2200:
            raise ToolInputError(f"records[{index}].expected_year must be an integer from 1000 through 2200")
        doi_key = doi.lower()
        if source_id in seen_ids or doi_key in seen_dois:
            raise ToolInputError("source_id and DOI values must be unique within one request")
        seen_ids.add(source_id)
        seen_dois.add(doi_key)
        normalized.append({"source_id": source_id, "doi": doi, "expected_title": title, "expected_year": year})
    return normalized


def _fetch_one(doi: str) -> dict[str, Any]:
    url = API_BASE + urllib.parse.quote(doi, safe="")
    target = urllib.parse.urlsplit(url)
    if target.scheme != "https" or target.hostname != API_HOST or target.port is not None or target.username or target.password or target.query or target.fragment:
        raise RuntimeError("Crossref endpoint configuration is not the fixed HTTPS host")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"IgnitionToolboxCrossref/{TOOL_VERSION}", "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json" and not content_type.endswith("+json"):
                return {"acquisition_status": "NON_JSON_RESPONSE", "http_status": status, "body": None}
            deadline = time.monotonic() + MAX_RESPONSE_DURATION_SECONDS
            chunks: list[bytes] = []
            total_bytes = 0
            while total_bytes <= MAX_RESPONSE_BYTES:
                if time.monotonic() >= deadline:
                    return {"acquisition_status": "RESPONSE_TIMEOUT", "http_status": status, "body": None}
                chunk = response.read(min(RESPONSE_CHUNK_BYTES, MAX_RESPONSE_BYTES + 1 - total_bytes))
                if time.monotonic() > deadline:
                    return {"acquisition_status": "RESPONSE_TIMEOUT", "http_status": status, "body": None}
                if not chunk:
                    break
                chunks.append(chunk)
                total_bytes += len(chunk)
            if total_bytes > MAX_RESPONSE_BYTES:
                return {"acquisition_status": "RESPONSE_TOO_LARGE", "http_status": status, "body": None}
            body = b"".join(chunks)
            return {"acquisition_status": "OK", "http_status": status, "body": body}
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        outcome = "REDIRECT_BLOCKED" if 300 <= status < 400 else ("NOT_FOUND" if status == 404 else ("RATE_LIMITED" if status == 429 else "HTTP_ERROR"))
        return {"acquisition_status": outcome, "http_status": status, "body": None}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None}


def _safe_text(value: Any, *, max_length: int = MAX_RELATION_TEXT_LENGTH) -> str | None:
    if not isinstance(value, str) or not value or len(value) > max_length or value != value.strip():
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    return value


def _parse_update_rows(message: dict[str, Any], field: str) -> dict[str, Any]:
    if field not in message:
        return {"field_status": "NOT_REPORTED", "reported_count": None, "rows": [], "omitted_count": 0, "truncated": False}
    raw_rows = message[field]
    if not isinstance(raw_rows, list):
        return {"field_status": "MALFORMED", "reported_count": None, "rows": [], "omitted_count": 0, "truncated": False}

    rows: list[dict[str, Any]] = []
    for item in raw_rows[:MAX_UPDATE_ROWS_PER_KIND]:
        if not isinstance(item, dict):
            continue
        doi = item.get("DOI")
        if not isinstance(doi, str) or not DOI_RE.fullmatch(doi):
            continue
        row: dict[str, Any] = {"doi": doi}
        for source_key, output_key in (("type", "type"), ("label", "label"), ("source", "source")):
            value = _safe_text(item.get(source_key), max_length=64)
            if value is not None:
                row[output_key] = value
        updated = item.get("updated")
        if isinstance(updated, dict):
            date_time = _safe_text(updated.get("date-time"), max_length=32)
            if date_time is not None:
                row["updated_date_time"] = date_time
        rows.append(row)

    if not raw_rows:
        status = "PRESENT_EMPTY"
    else:
        status = "PRESENT_NONEMPTY"
    return {
        "field_status": status,
        "reported_count": len(raw_rows),
        "rows": rows,
        "omitted_count": len(raw_rows) - len(rows),
        "truncated": len(raw_rows) > MAX_UPDATE_ROWS_PER_KIND,
    }


def _parse_relation_rows(message: dict[str, Any]) -> dict[str, Any]:
    if "relation" not in message:
        return {
            "field_status": "NOT_REPORTED", "relation_type_count": None, "reported_count": None,
            "rows": [], "omitted_count": 0, "truncated": False,
        }
    relation = message["relation"]
    if not isinstance(relation, dict):
        return {
            "field_status": "MALFORMED", "relation_type_count": None, "reported_count": None,
            "rows": [], "omitted_count": 0, "truncated": False,
        }

    raw_count = sum(len(values) for values in relation.values() if isinstance(values, list))
    malformed_type_count = 0
    rows: list[dict[str, Any]] = []
    valid_types: list[tuple[str, Any]] = []
    for relation_type, values in relation.items():
        safe_type = _safe_text(relation_type, max_length=64)
        if safe_type is None:
            malformed_type_count += 1
            continue
        valid_types.append((safe_type, values))
    valid_types.sort(key=lambda item: item[0])
    type_truncated = len(valid_types) > MAX_RELATION_TYPES

    for relation_type, values in valid_types[:MAX_RELATION_TYPES]:
        if not isinstance(values, list):
            malformed_type_count += 1
            continue
        for item in values:
            if len(rows) >= MAX_RELATION_ROWS:
                continue
            if not isinstance(item, dict):
                continue
            id_type = _safe_text(item.get("id-type"), max_length=32)
            identifier = _safe_text(item.get("id"), max_length=MAX_RELATION_TEXT_LENGTH)
            if id_type is None or identifier is None or "://" in identifier:
                continue
            if id_type.lower() == "doi":
                if not DOI_RE.fullmatch(identifier):
                    continue
            elif not SOURCE_ID_RE.fullmatch(identifier):
                continue
            row = {"relation_type": relation_type, "id_type": id_type, "identifier": identifier}
            asserted_by = _safe_text(item.get("asserted-by"), max_length=32)
            if asserted_by is not None:
                row["asserted_by"] = asserted_by
            rows.append(row)

    if not relation:
        status = "PRESENT_EMPTY"
    else:
        status = "PRESENT_NONEMPTY"
    truncated = type_truncated or raw_count > MAX_RELATION_ROWS
    return {
        "field_status": status,
        "relation_type_count": len(relation),
        "reported_count": raw_count,
        "rows": rows,
        "omitted_count": raw_count - len(rows),
        "malformed_relation_type_count": malformed_type_count,
        "truncated": truncated,
    }


def _relation_metadata(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "update_to": _parse_update_rows(message, "update-to"),
        "updated_by": _parse_update_rows(message, "updated-by"),
        "related_items": _parse_relation_rows(message),
    }


def _reference_text(value: Any, *, max_length: int = MAX_REFERENCE_TEXT_LENGTH) -> str | None:
    text = _safe_text(value, max_length=max_length)
    if text is None or re.search(r"https?://", text, flags=re.IGNORECASE):
        return None
    return text


def _parse_reference_rows(message: dict[str, Any]) -> dict[str, Any]:
    if "reference" not in message:
        return {
            "field_status": "NOT_REPORTED", "reported_count": None, "rows": [],
            "omitted_count": 0, "truncated": False, "invalid_entry_count": 0,
        }
    raw_rows = message["reference"]
    if not isinstance(raw_rows, list):
        return {
            "field_status": "MALFORMED", "reported_count": None, "rows": [],
            "omitted_count": 0, "truncated": False, "invalid_entry_count": 0,
        }

    rows: list[dict[str, Any]] = []
    invalid_entry_count = 0
    for item in raw_rows[:MAX_REFERENCE_ROWS]:
        if not isinstance(item, dict):
            invalid_entry_count += 1
            continue
        row: dict[str, Any] = {}
        doi = item.get("DOI")
        if isinstance(doi, str) and DOI_RE.fullmatch(doi):
            row["doi"] = doi
        for source_key, output_key, limit in (
            ("key", "key", 96),
            ("unstructured", "unstructured", MAX_REFERENCE_TEXT_LENGTH),
            ("article-title", "article_title", 256),
            ("author", "author", 128),
            ("journal-title", "journal_title", 160),
            ("volume", "volume", 48),
            ("issue", "issue", 48),
            ("first-page", "first_page", 48),
            ("series-title", "series_title", 160),
            ("edition", "edition", 48),
            ("issn", "issn", 48),
            ("isbn", "isbn", 48),
        ):
            value = _reference_text(item.get(source_key), max_length=limit)
            if value is not None:
                row[output_key] = value
        year = item.get("year")
        if type(year) is int and 1000 <= year <= 2200:
            row["year"] = year
        elif isinstance(year, str) and re.fullmatch(r"\d{4}", year) and 1000 <= int(year) <= 2200:
            row["year"] = int(year)
        if row:
            rows.append(row)
        else:
            invalid_entry_count += 1

    return {
        "field_status": "PRESENT_EMPTY" if not raw_rows else "PRESENT_NONEMPTY",
        "reported_count": len(raw_rows),
        "rows": rows,
        "omitted_count": len(raw_rows) - len(rows),
        "truncated": len(raw_rows) > MAX_REFERENCE_ROWS,
        "invalid_entry_count": invalid_entry_count,
    }


def _verify_row(record: dict[str, Any]) -> dict[str, Any]:
    observed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    result: dict[str, Any] = {
        "source_id": record["source_id"],
        "canonical_identifier": record["doi"],
        "expected_title": record["expected_title"],
        "expected_year": record["expected_year"],
        "retrieval_timestamp_utc": observed_at,
        "source_url": API_BASE + urllib.parse.quote(record["doi"], safe=""),
        "source_license": "Crossref bibliographic metadata; public reuse basis documented by Crossref",
        "crossref_relation_metadata": None,
        "crossref_reference_metadata": None,
    }
    fetched = _fetch_one(record["doi"])
    result["acquisition_status"] = fetched["acquisition_status"]
    result["http_status"] = fetched["http_status"]
    if fetched["acquisition_status"] != "OK":
        result.update({
            "response_sha256": None,
            "observed_title": None,
            "observed_year": None,
            "title_match": None,
            "year_match": None,
            "retraction_signal": None,
        })
        return result

    body = fetched["body"]
    result["response_sha256"] = hashlib.sha256(body).hexdigest()
    try:
        document = json.loads(body.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        result.update({
            "acquisition_status": "INVALID_JSON_RESPONSE",
            "observed_title": None,
            "observed_year": None,
            "title_match": None,
            "year_match": None,
            "retraction_signal": None,
        })
        return result
    message = document.get("message") if isinstance(document, dict) else None
    if not isinstance(message, dict):
        result.update({
            "acquisition_status": "INVALID_CROSSREF_MESSAGE",
            "observed_title": None,
            "observed_year": None,
            "title_match": None,
            "year_match": None,
            "retraction_signal": None,
        })
        return result
    titles = message.get("title")
    observed_title = titles[0] if isinstance(titles, list) and titles and isinstance(titles[0], str) else None
    observed_year = UPSTREAM.extract_year(message)
    title_match = UPSTREAM.norm(observed_title) == UPSTREAM.norm(record["expected_title"])
    year_match = observed_year is not None and observed_year == record["expected_year"]
    result.update({
        "observed_title": observed_title,
        "observed_year": observed_year,
        "title_match": title_match,
        "year_match": year_match,
        "full_match": bool(title_match and year_match),
        "retraction_signal": UPSTREAM.retraction_signal(message),
        "crossref_relation_metadata": _relation_metadata(message),
        "crossref_reference_metadata": _parse_reference_rows(message),
    })
    return result


def verify(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        rows.append(_verify_row(record))
        if index + 1 < len(records):
            time.sleep(0.1)
    failures = sum(row["acquisition_status"] != "OK" for row in rows)
    mismatches = sum(row.get("acquisition_status") == "OK" and not row.get("full_match", False) for row in rows)
    return {
        "schema_version": "ignition.crossref-metadata-verification-r0",
        "tool_id": "research.verify_crossref_metadata",
        "tool_version": TOOL_VERSION,
        "status": "COMPLETED_WITH_EXPLICIT_FAILURES" if failures else ("METADATA_MISMATCHES" if mismatches else "ALL_METADATA_MATCHED"),
        "record_count": len(rows),
        "resolved_count": sum(row["acquisition_status"] == "OK" for row in rows),
        "acquisition_failure_count": failures,
        "metadata_mismatch_count": mismatches,
        "rows": rows,
        "source_code_sha256": {
            "wrapper": _sha256(Path(__file__).resolve()),
            "task103_crossref_helpers": _sha256(UPSTREAM_HELPERS_PATH),
        },
        "claim_ceiling": "Crossref API metadata retrieval, normalized title/year comparison, and bounded projection of returned update-to, updated-by, typed relation identifiers, and deposited reference citation metadata only. Returned fields are provider-deposited metadata at retrieval time; omissions, empty fields, or relation labels do not establish completeness, source authenticity, article content, scientific truth, or current retraction status.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read the bounded JSON contract from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="authorize this invocation to make fixed-host public HTTPS GET requests")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        print("PUBLIC_NETWORK_CALL_REQUIRES --allow-public-network", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        records = parse_request(raw)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(verify(records), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
