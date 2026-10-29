#!/usr/bin/env python3
"""Resolve one public structured citation to a provider-reported PubMed ID.

This optional adapter sends one caller-supplied citation to the fixed NCBI
ECitMatch endpoint. It returns only the provider-reported PMID and bounded
response evidence; it does not fetch article text or verify the record.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOL_ID = "research.match_pubmed_citation"
TOOL_VERSION = "0.1.0"
TOOL_CONTACT = "IgnitionPubMedCitationMatcher"
RESPONSE_KEY = "IgnitionToolbox0"
API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/ecitmatch.cgi"
API_HOST = "eutils.ncbi.nlm.nih.gov"
NCBI_DISCLAIMER_URL = "https://www.ncbi.nlm.nih.gov/About/disclaimer.html"
NCBI_USAGE_POLICY_URL = "https://www.ncbi.nlm.nih.gov/home/about/policies/"
MAX_REQUEST_BYTES = 4096
MAX_RESPONSE_BYTES = 16 * 1024
MAX_RESPONSE_DURATION_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 2048
YEAR_RE = re.compile(r"[0-9]{4}\Z")
PMID_RE = re.compile(r"[1-9][0-9]{0,11}\Z")
EXPECTED_FIELDS = ("journal_title", "year", "volume", "first_page", "first_author")
FIELD_LIMITS = {
    "journal_title": 160,
    "year": 4,
    "volume": 32,
    "first_page": 32,
    "first_author": 100,
}
CLAIM_CEILING = (
    "Reports the PMID returned by NCBI ECitMatch for one caller-supplied "
    "structured citation. The provider match is not independently verified "
    "and does not establish source authenticity, citation correctness, "
    "article relevance, or scientific support."
)


class ToolInputError(ValueError):
    """Raised when input falls outside the bounded citation contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent the fixed-host request from following a redirect elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _normalize_field(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ToolInputError(f"{name} must be a string")
    if any(char == "|" or ord(char) < 32 or 127 <= ord(char) < 160 for char in value):
        raise ToolInputError(f"{name} contains a forbidden delimiter or control character")
    normalized = " ".join(value.split())
    if not normalized:
        raise ToolInputError(f"{name} must not be empty")
    if len(normalized) > FIELD_LIMITS[name]:
        raise ToolInputError(f"{name} exceeds {FIELD_LIMITS[name]} characters")
    return normalized


def parse_request(raw: bytes) -> dict[str, str]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) != set(EXPECTED_FIELDS):
        raise ToolInputError("request must contain exactly journal_title, year, volume, first_page, and first_author")
    citation = {name: _normalize_field(document[name], name) for name in EXPECTED_FIELDS}
    if not YEAR_RE.fullmatch(citation["year"]):
        raise ToolInputError("year must be a four-digit publication year")
    return citation


def _citation_sha256(citation: dict[str, str]) -> str:
    canonical = json.dumps(citation, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _sha256_source() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _request_url(citation: dict[str, str]) -> str:
    bdata = "|".join(citation[name] for name in EXPECTED_FIELDS) + f"|{RESPONSE_KEY}|"
    url = API_BASE + "?" + urllib.parse.urlencode({
        "db": "pubmed",
        "bdata": bdata,
        "retmode": "xml",
        "rettype": "xml",
        "tool": TOOL_CONTACT,
    })
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.path != "/entrez/eutils/ecitmatch.cgi"
        or target.fragment or len(url) > 8192
    ):
        raise RuntimeError("NCBI ECitMatch endpoint is outside the fixed HTTPS host boundary")
    return url


def _read_bounded(response: Any) -> tuple[bytes | None, str | None]:
    deadline = time.monotonic() + MAX_RESPONSE_DURATION_SECONDS
    chunks: list[bytes] = []
    total = 0
    while total <= MAX_RESPONSE_BYTES:
        if time.monotonic() >= deadline:
            return None, "RESPONSE_TIMEOUT"
        chunk = response.read(min(RESPONSE_CHUNK_BYTES, MAX_RESPONSE_BYTES + 1 - total))
        if time.monotonic() > deadline:
            return None, "RESPONSE_TIMEOUT"
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    if total > MAX_RESPONSE_BYTES:
        return None, "RESPONSE_TOO_LARGE"
    return b"".join(chunks), None


def _fetch(citation: dict[str, str], opener: Any | None = None) -> dict[str, Any]:
    url = _request_url(citation)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{TOOL_CONTACT}/{TOOL_VERSION}",
            "Accept": "text/plain, application/xml, text/xml",
        },
    )
    if opener is None:
        opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type not in {"text/plain", "application/xml", "text/xml"} and not content_type.endswith("+xml"):
                return {"acquisition_status": "NON_TEXT_RESPONSE", "http_status": status, "body": None}
            body, read_error = _read_bounded(response)
            if read_error:
                return {"acquisition_status": read_error, "http_status": status, "body": None}
            assert body is not None
            return {"acquisition_status": "OK", "http_status": status, "body": body}
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        outcome = "REDIRECT_BLOCKED" if 300 <= status < 400 else ("RATE_LIMITED" if status == 429 else "HTTP_ERROR")
        return {"acquisition_status": outcome, "http_status": status, "body": None}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None}


def _parse_response(body: bytes, citation: dict[str, str]) -> dict[str, Any]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {"acquisition_status": "INVALID_RESPONSE_ENCODING", "match_status": "NOT_EVALUATED", "returned_pmid": None}
    lines = [line for line in text.splitlines() if line]
    if len(lines) != 1:
        return {"acquisition_status": "INVALID_RESPONSE_SHAPE", "match_status": "NOT_EVALUATED", "returned_pmid": None}
    parts = lines[0].split("|")
    if len(parts) != 7 or parts[5] != RESPONSE_KEY:
        return {"acquisition_status": "INVALID_RESPONSE_SHAPE", "match_status": "NOT_EVALUATED", "returned_pmid": None}
    echoed = [" ".join(value.split()).casefold() for value in parts[:5]]
    submitted = [citation[name].casefold() for name in EXPECTED_FIELDS]
    if echoed != submitted:
        return {"acquisition_status": "CITATION_ECHO_MISMATCH", "match_status": "NOT_EVALUATED", "returned_pmid": None}
    returned = parts[6].strip()
    if returned == "":
        return {"acquisition_status": "OK", "match_status": "NO_MATCH_REPORTED", "returned_pmid": None}
    if not PMID_RE.fullmatch(returned):
        return {"acquisition_status": "UNRECOGNIZED_MATCH_VALUE", "match_status": "NOT_EVALUATED", "returned_pmid": None}
    return {"acquisition_status": "OK", "match_status": "PROVIDER_MATCH_REPORTED", "returned_pmid": returned}


def match(citation: dict[str, str], opener: Any | None = None) -> dict[str, Any]:
    fetched = _fetch(citation, opener=opener)
    body = fetched.get("body")
    parsed = _parse_response(body, citation) if isinstance(body, bytes) else {
        "acquisition_status": fetched["acquisition_status"],
        "match_status": "NOT_AVAILABLE",
        "returned_pmid": None,
    }
    if parsed["acquisition_status"] not in {"OK", "INVALID_RESPONSE_ENCODING", "INVALID_RESPONSE_SHAPE", "CITATION_ECHO_MISMATCH", "UNRECOGNIZED_MATCH_VALUE"}:
        match_status = "NOT_AVAILABLE"
    else:
        match_status = parsed["match_status"]
    return {
        "schema_version": "ignition.pubmed-citation-matcher-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "source_code_sha256": _sha256_source(),
        "citation_sha256": _citation_sha256(citation),
        "source_endpoint": API_BASE,
        "retrieval_timestamp_utc": _utc_now(),
        "acquisition_status": parsed["acquisition_status"],
        "http_status": fetched["http_status"],
        "request_count": 1,
        "tool_parameter_sent": True,
        "email_sent_to_provider": False,
        "api_key_used": False,
        "response_sha256": hashlib.sha256(body).hexdigest() if isinstance(body, bytes) else None,
        "response_binding_status": "REQUEST_KEY_AND_NORMALIZED_CITATION_ECHO" if parsed["match_status"] in {"PROVIDER_MATCH_REPORTED", "NO_MATCH_REPORTED"} else "NOT_ESTABLISHED",
        "match_status": match_status,
        "returned_pmid": parsed["returned_pmid"] if match_status == "PROVIDER_MATCH_REPORTED" else None,
        "provider_disclaimer": NCBI_DISCLAIMER_URL,
        "provider_usage_policy": NCBI_USAGE_POLICY_URL,
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded UTF-8 JSON citation from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="explicitly permit one request to the fixed NCBI ECitMatch host")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        parser.error("--allow-public-network is required for the NCBI request")
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        citation = parse_request(raw)
    except ToolInputError as exc:
        print(f"TOOL_INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    receipt = match(citation)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
