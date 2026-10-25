#!/usr/bin/env python3
"""Locate provider-reported Europe PMC full-text URLs for exact DOI inputs.

This adapter performs a bounded metadata search only. It never requests the
returned article URLs, downloads article content, or adjudicates rights or
scientific support.
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
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit


TOOL_ID = "research.resolve_europe_pmc_fulltext_locations"
TOOL_VERSION = "0.1.0"
API_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
API_HOST = "www.ebi.ac.uk"
MAX_REQUEST_BYTES = 4096
MAX_DOIS = 5
MAX_DOI_LENGTH = 128
MAX_PROVIDER_RECORDS = 5
MAX_RESPONSE_BYTES = 512 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 8192
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
CLAIM_CEILING = (
    "Reports exact-DOI Europe PMC records and their provider-reported fullTextUrlList metadata at retrieval time. "
    "It does not request the returned URLs, download or inspect article content, verify link availability or license, "
    "establish legal permission, source authenticity, article status, or scientific support."
)


class ToolInputError(ValueError):
    """Raised when caller or provider data violates the bounded contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent a fixed-host API call from following redirects to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _strict_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ToolInputError("non-standard JSON constant")


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


def parse_request(raw: bytes) -> List[str]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError("request exceeds the declared byte limit")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ToolInputError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON with unique keys") from exc
    if not isinstance(document, dict) or set(document) != {"dois"}:
        raise ToolInputError("request must contain exactly one key: dois")
    values = document["dois"]
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_DOIS:
        raise ToolInputError("dois must contain between one and five values")

    normalized: List[str] = []
    for index, value in enumerate(values):
        if (
            not isinstance(value, str)
            or len(value) > MAX_DOI_LENGTH
            or value != value.strip()
            or not DOI_RE.fullmatch(value)
        ):
            raise ToolInputError("dois[{}] must be a bare DOI identifier".format(index))
        doi = value.casefold()
        if doi in normalized:
            raise ToolInputError("DOI values must be unique within one request")
        normalized.append(doi)
    return normalized


def _request_url(doi: str) -> str:
    url = API_BASE + "?" + urllib.parse.urlencode({
        "query": "DOI:" + doi,
        "format": "json",
        "resultType": "core",
        "pageSize": str(MAX_PROVIDER_RECORDS),
    })
    target = urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.path != "/europepmc/webservices/rest/search"
        or target.fragment or len(url) > 8192
    ):
        raise RuntimeError("Europe PMC full-text lookup endpoint is not the declared fixed HTTPS host")
    return url


def _read_bounded(response: Any) -> Tuple[Optional[bytes], Optional[str]]:
    deadline = time.monotonic() + MAX_RESPONSE_DURATION_SECONDS
    chunks: List[bytes] = []
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


def _fetch(doi: str) -> Dict[str, Any]:
    url = _request_url(doi)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "IgnitionToolboxEuropePMCFullTextLocator/{}".format(TOOL_VERSION), "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type not in {"application/json", "text/json"} and not content_type.endswith("+json"):
                return {"acquisition_status": "NON_JSON_RESPONSE", "http_status": status, "body": None}
            body, error = _read_bounded(response)
            if error:
                return {"acquisition_status": error, "http_status": status, "body": None}
            return {"acquisition_status": "OK", "http_status": status, "body": body}
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        outcome = "REDIRECT_BLOCKED" if 300 <= status < 400 else ("RATE_LIMITED" if status == 429 else "HTTP_ERROR")
        return {"acquisition_status": outcome, "http_status": status, "body": None}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None}


def _optional_text(record: Dict[str, Any], key: str, *, max_length: int = 2048) -> Optional[str]:
    value = record.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ToolInputError("invalid provider text field")
    text = " ".join(value.split())
    if len(text) > max_length:
        raise ToolInputError("provider text field exceeds the declared limit")
    return text or None


def _provider_open_access(value: Any) -> Optional[str | bool]:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, str) and len(value) <= 16:
        return value
    raise ToolInputError("invalid provider isOpenAccess field")


def _safe_provider_url(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not value or len(value) > 2048:
        return None
    if any(ord(char) < 0x21 or ord(char) == 0x7F for char in value):
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.casefold() != "https" or not parsed.hostname or parsed.username or parsed.password
        or port not in (None, 443) or parsed.fragment
    ):
        return None
    return value


def _fulltext_urls(record: Dict[str, Any]) -> Tuple[List[Dict[str, Optional[str]]], int]:
    container = record.get("fullTextUrlList")
    if container is None:
        return [], 0
    if not isinstance(container, dict):
        raise ToolInputError("provider fullTextUrlList must be an object")
    items = container.get("fullTextUrl", [])
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list) or len(items) > 64:
        raise ToolInputError("provider fullTextUrlList.fullTextUrl must be a bounded array")
    locations: List[Dict[str, Optional[str]]] = []
    omitted = 0
    for item in items:
        if not isinstance(item, dict):
            raise ToolInputError("provider full-text location must be an object")
        url = _safe_provider_url(item.get("url"))
        if url is None:
            omitted += 1
            continue
        locations.append({
            "url": url,
            "availability": _optional_text(item, "availability", max_length=128),
            "availability_code": _optional_text(item, "availabilityCode", max_length=64),
            "document_style": _optional_text(item, "documentStyle", max_length=64),
            "site": _optional_text(item, "site", max_length=256),
            "license": _optional_text(item, "license", max_length=128),
        })
    return locations, omitted


def _parse_provider_document(body: bytes, requested_doi: str) -> Dict[str, Any]:
    document = json.loads(
        body.decode("utf-8", errors="strict"),
        object_pairs_hook=_strict_object,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(document, dict):
        raise ToolInputError("provider response must be an object")
    result_list = document.get("resultList")
    if not isinstance(result_list, dict) or not isinstance(result_list.get("result"), list):
        raise ToolInputError("provider response is missing resultList.result")
    hit_count = document.get("hitCount")
    if (
        isinstance(hit_count, bool) or not isinstance(hit_count, (int, str))
        or not str(hit_count).isdigit() or len(str(hit_count)) > 12
    ):
        raise ToolInputError("provider response has an invalid hitCount")
    results = result_list["result"]
    if len(results) > MAX_PROVIDER_RECORDS:
        raise ToolInputError("provider response exceeds the exact-DOI record limit")

    exact_records: List[Dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict):
            raise ToolInputError("provider result must be an object")
        doi = _optional_text(result, "doi", max_length=MAX_DOI_LENGTH)
        if _normalize_doi(doi) != requested_doi:
            continue
        source = _optional_text(result, "source", max_length=32)
        record_id = _optional_text(result, "id", max_length=128)
        if not source or not record_id:
            raise ToolInputError("exact DOI provider record is missing source or id")
        locations, omitted = _fulltext_urls(result)
        exact_records.append({
            "source": source,
            "id": record_id,
            "pmid": _optional_text(result, "pmid", max_length=32),
            "pmcid": _optional_text(result, "pmcid", max_length=32),
            "doi": doi,
            "is_open_access_claim": _provider_open_access(result.get("isOpenAccess")),
            "full_text_locations": locations,
            "omitted_unsafe_location_count": omitted,
        })
    return {"hit_count": int(hit_count), "records": exact_records}


def locate(dois: List[str]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    successful_acquisitions = 0
    valid_provider_responses = 0
    for doi in dois:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        row: Dict[str, Any] = {
            "requested_doi": doi,
            "query_sha256": hashlib.sha256(("DOI:" + doi).encode("utf-8")).hexdigest(),
            "retrieval_timestamp_utc": timestamp,
            "source_endpoint": API_BASE,
            "acquisition_status": "NOT_AVAILABLE",
            "http_status": None,
            "response_sha256": None,
            "provider_hit_count": None,
            "match_status": "NOT_RUN",
            "record_count": 0,
            "full_text_location_count": 0,
            "records": [],
        }
        fetched = _fetch(doi)
        row["acquisition_status"] = fetched["acquisition_status"]
        row["http_status"] = fetched["http_status"]
        if fetched["acquisition_status"] != "OK":
            row["match_status"] = "NOT_AVAILABLE"
            rows.append(row)
            continue
        successful_acquisitions += 1
        body = fetched["body"]
        row["response_sha256"] = hashlib.sha256(body).hexdigest()
        try:
            provider = _parse_provider_document(body, doi)
        except (ToolInputError, UnicodeDecodeError, json.JSONDecodeError):
            row["acquisition_status"] = "INVALID_PROVIDER_RESPONSE"
            row["match_status"] = "NOT_AVAILABLE"
            rows.append(row)
            continue
        valid_provider_responses += 1
        row["provider_hit_count"] = provider["hit_count"]
        row["records"] = provider["records"]
        row["record_count"] = len(provider["records"])
        row["full_text_location_count"] = sum(len(record["full_text_locations"]) for record in provider["records"])
        if not provider["records"]:
            row["match_status"] = "NO_EXACT_MATCH"
        elif row["record_count"] > 1:
            row["match_status"] = "MULTIPLE_EXACT_RECORDS"
        elif row["full_text_location_count"]:
            row["match_status"] = "EXACT_RECORD_WITH_LOCATIONS"
        else:
            row["match_status"] = "EXACT_RECORD_NO_USABLE_LOCATION"
        rows.append(row)

    status = "OK" if valid_provider_responses == len(dois) else ("PARTIAL" if valid_provider_responses else "NOT_AVAILABLE")
    return {
        "schema_version": "ignition.europe-pmc-fulltext-locator-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "source_code_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
        "provider": "Europe PMC",
        "status": status,
        "requested_count": len(dois),
        "successful_acquisition_count": successful_acquisitions,
        "valid_provider_response_count": valid_provider_responses,
        "records": rows,
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded JSON request from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="explicitly permit fixed-host public API queries")
    args = parser.parse_args(argv)
    if not args.stdin:
        print("INVALID_REQUEST: --stdin is required", file=sys.stderr)
        return 2
    if not args.allow_public_network:
        print("PUBLIC_NETWORK_CALL_REQUIRES --allow-public-network", file=sys.stderr)
        return 2
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        dois = parse_request(raw)
    except ToolInputError as exc:
        print("INVALID_REQUEST: {}".format(exc), file=sys.stderr)
        return 2
    print(json.dumps(locate(dois), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
