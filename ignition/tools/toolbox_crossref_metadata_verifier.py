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


TOOL_VERSION = "0.1.0"
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
        "claim_ceiling": "Crossref API metadata retrieval and normalized title/year comparison only; this does not validate article content, source authenticity, scientific truth, or retraction status beyond returned metadata fields.",
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
