#!/usr/bin/env python3
"""Resolve caller-supplied DOIs to NCBI PubMed/PMC identifiers, stdout only.

This optional adapter uses only the fixed PMC ID Converter HTTPS endpoint. It
does not fetch article content, update repository records, or evaluate science.
"""
from __future__ import annotations

import argparse
import hashlib
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
API_BASE = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
API_HOST = "pmc.ncbi.nlm.nih.gov"
MAX_REQUEST_BYTES = 16 * 1024
MAX_RECORDS = 10
MAX_DOI_LENGTH = 128
MAX_RESPONSE_BYTES = 128 * 1024
REQUEST_TIMEOUT_SECONDS = 5
MAX_RESPONSE_DURATION_SECONDS = 7
RESPONSE_CHUNK_BYTES = 8 * 1024
INTER_REQUEST_DELAY_SECONDS = 0.34
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
IDENTIFIER_RE = re.compile(r"[0-9]+\Z")
PMCID_RE = re.compile(r"PMC[0-9]+\Z")


class ToolInputError(ValueError):
    """Raised when input falls outside the declared DOI lookup contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent the fixed-host request from following a redirect elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def parse_request(raw: bytes) -> list[str]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) != {"dois"}:
        raise ToolInputError("request must be an object with exactly one key: dois")
    dois = document["dois"]
    if not isinstance(dois, list) or not 1 <= len(dois) <= MAX_RECORDS:
        raise ToolInputError(f"dois must contain between 1 and {MAX_RECORDS} entries")
    seen: set[str] = set()
    normalized: list[str] = []
    for index, doi in enumerate(dois):
        if not isinstance(doi, str) or len(doi) > MAX_DOI_LENGTH or doi != doi.strip() or not DOI_RE.fullmatch(doi):
            raise ToolInputError(f"dois[{index}] must be one bare DOI identifier")
        key = doi.casefold()
        if key in seen:
            raise ToolInputError("DOI values must be unique within one request")
        seen.add(key)
        normalized.append(doi)
    return normalized


def _fetch_one(doi: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"ids": doi, "format": "json"})
    url = API_BASE + "?" + query
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.fragment
    ):
        raise RuntimeError("PMC ID Converter endpoint is not the fixed HTTPS host")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"IgnitionToolboxPubMedIdentifier/{TOOL_VERSION}", "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in {"application/json", "text/json"} and not content_type.endswith("+json"):
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
            return {"acquisition_status": "OK", "http_status": status, "body": b"".join(chunks)}
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        outcome = "REDIRECT_BLOCKED" if 300 <= status < 400 else ("NOT_FOUND" if status == 404 else ("RATE_LIMITED" if status == 429 else "HTTP_ERROR"))
        return {"acquisition_status": outcome, "http_status": status, "body": None}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None}


def _normalized_identifier(value: Any, pattern: re.Pattern[str]) -> str | None:
    return value if isinstance(value, str) and pattern.fullmatch(value) else None


def _resolve_row(doi: str) -> dict[str, Any]:
    source_url = API_BASE + "?" + urllib.parse.urlencode({"ids": doi, "format": "json"})
    result: dict[str, Any] = {
        "doi": doi,
        "retrieval_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_url": source_url,
        "acquisition_status": None,
        "http_status": None,
        "response_sha256": None,
        "identifier_status": None,
        "matched_doi": None,
        "pmid": None,
        "pmcid": None,
    }
    fetched = _fetch_one(doi)
    result["acquisition_status"] = fetched["acquisition_status"]
    result["http_status"] = fetched["http_status"]
    if fetched["acquisition_status"] != "OK":
        result["identifier_status"] = "NOT_AVAILABLE"
        return result

    body = fetched["body"]
    result["response_sha256"] = hashlib.sha256(body).hexdigest()
    try:
        document = json.loads(body.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (ToolInputError, UnicodeDecodeError, json.JSONDecodeError):
        result["acquisition_status"] = "INVALID_JSON_RESPONSE"
        result["identifier_status"] = "NOT_AVAILABLE"
        return result
    if not isinstance(document, dict) or document.get("status") not in {"ok", "error"}:
        result["acquisition_status"] = "INVALID_IDCONV_RESPONSE"
        result["identifier_status"] = "NOT_AVAILABLE"
        return result
    if document.get("status") != "ok":
        result["acquisition_status"] = "UPSTREAM_ERROR"
        result["identifier_status"] = "NOT_AVAILABLE"
        return result
    records = document.get("records")
    if not isinstance(records, list):
        result["acquisition_status"] = "INVALID_IDCONV_RESPONSE"
        result["identifier_status"] = "NOT_AVAILABLE"
        return result
    if not records:
        result["identifier_status"] = "NO_MATCH"
        return result
    if any(not isinstance(record, dict) for record in records):
        result["acquisition_status"] = "INVALID_IDCONV_RESPONSE"
        result["identifier_status"] = "NOT_AVAILABLE"
        return result
    matches = [
        record for record in records
        if isinstance(record.get("doi"), str) and record["doi"].casefold() == doi.casefold()
    ]
    if len(matches) != 1:
        result["identifier_status"] = "UPSTREAM_RECORD_MISMATCH" if records else "NO_MATCH"
        return result

    record = matches[0]
    result["matched_doi"] = record["doi"]
    result["pmid"] = _normalized_identifier(record.get("pmid"), IDENTIFIER_RE)
    result["pmcid"] = _normalized_identifier(record.get("pmcid"), PMCID_RE)
    if result["pmid"] or result["pmcid"]:
        result["identifier_status"] = "IDENTIFIER_RESOLVED"
    else:
        result["identifier_status"] = "MATCHED_WITHOUT_PUBMED_OR_PMC_ID"
    return result


def resolve(dois: list[str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, doi in enumerate(dois):
        rows.append(_resolve_row(doi))
        if index + 1 < len(dois):
            time.sleep(INTER_REQUEST_DELAY_SECONDS)
    failures = sum(row["acquisition_status"] != "OK" for row in rows)
    resolved = sum(row["identifier_status"] == "IDENTIFIER_RESOLVED" for row in rows)
    return {
        "schema_version": "ignition.pubmed-identifier-resolution-r0",
        "tool_id": "research.resolve_pubmed_identifiers",
        "tool_version": TOOL_VERSION,
        "status": "COMPLETED_WITH_EXPLICIT_FAILURES" if failures else ("IDENTIFIERS_RESOLVED" if resolved else "NO_IDENTIFIERS_RESOLVED"),
        "doi_count": len(rows),
        "resolved_count": resolved,
        "acquisition_failure_count": failures,
        "rows": rows,
        "source_code_sha256": {"wrapper": _sha256(Path(__file__).resolve())},
        "claim_ceiling": "DOI-to-PMID/PMCID identifier lookup in the live PMC ID Converter response only; no article-content, bibliographic-accuracy, source-authenticity, scientific-validity, or completeness claim is established.",
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
        dois = parse_request(raw)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(resolve(dois), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
