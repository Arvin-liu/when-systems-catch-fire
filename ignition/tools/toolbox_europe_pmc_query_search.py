#!/usr/bin/env python3
"""Search Europe PMC for a bounded set of provider-reported publication records."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


TOOL_ID = "research.search_europe_pmc_query"
TOOL_VERSION = "0.1.0"
API_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
API_HOST = "www.ebi.ac.uk"
MAX_REQUEST_BYTES = 4096
MAX_QUERY_CHARS = 512
MAX_QUERY_UTF8_BYTES = 2048
MAX_RESULTS = 10
MAX_RESPONSE_BYTES = 512 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 8192
CLAIM_CEILING = (
    "Bounded Europe PMC publication metadata returned for the supplied query at retrieval time. "
    "Results are not exhaustive, do not establish scientific support or quality, and do not authenticate "
    "the source or the article's current status."
)


class ToolInputError(ValueError):
    """Raised when caller input falls outside the declared bounded contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent a fixed-host request from following redirects to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _strict_object(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def parse_request(raw: bytes) -> Tuple[str, int]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError("request exceeds the declared byte limit")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON with unique object keys") from exc
    if not isinstance(document, dict) or set(document) != {"query", "max_results"}:
        raise ToolInputError("request must contain exactly query and max_results")
    query = document["query"]
    if not isinstance(query, str) or not query or query != query.strip():
        raise ToolInputError("query must be a non-empty, already-trimmed string")
    if len(query) > MAX_QUERY_CHARS or len(query.encode("utf-8")) > MAX_QUERY_UTF8_BYTES:
        raise ToolInputError("query exceeds the declared character or UTF-8 byte limit")
    if any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in query):
        raise ToolInputError("query must not contain control characters")
    max_results = document["max_results"]
    if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= MAX_RESULTS:
        raise ToolInputError("max_results must be an integer from 1 through 10")
    return query, max_results


def _request_url(query: str, max_results: int) -> str:
    params = urllib.parse.urlencode({
        "query": query,
        "format": "json",
        "resultType": "lite",
        "pageSize": str(max_results),
    })
    url = API_BASE + "?" + params
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.path != "/europepmc/webservices/rest/search"
        or target.fragment or len(url) > 8192
    ):
        raise RuntimeError("Europe PMC search endpoint is not the declared fixed HTTPS host")
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


def _fetch(query: str, max_results: int) -> Dict[str, Any]:
    url = _request_url(query, max_results)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"IgnitionToolboxEuropePMCSearch/{TOOL_VERSION}", "Accept": "application/json"},
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


def _optional_text(record: Dict[str, Any], key: str) -> Optional[str]:
    value = record.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ToolInputError("invalid provider metadata field")
    text = " ".join(str(value).split())
    if len(text) > 4096:
        raise ToolInputError("provider metadata field exceeds the declared limit")
    return text or None


def _parse_provider_document(body: bytes, max_results: int) -> Dict[str, Any]:
    document = json.loads(body.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    if not isinstance(document, dict):
        raise ToolInputError("provider response must be an object")
    result_list = document.get("resultList")
    if not isinstance(result_list, dict) or not isinstance(result_list.get("result"), list):
        raise ToolInputError("provider response is missing resultList.result")
    hit_count = document.get("hitCount")
    if isinstance(hit_count, bool) or not isinstance(hit_count, (int, str)) or not str(hit_count).isdigit():
        raise ToolInputError("provider response has an invalid hitCount")
    results = result_list["result"]
    if len(results) > max_results:
        raise ToolInputError("provider response exceeds the requested result limit")
    rows: List[Dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict):
            raise ToolInputError("provider result must be an object")
        source = _optional_text(result, "source")
        record_id = _optional_text(result, "id")
        if not source or not record_id:
            raise ToolInputError("provider result is missing source or id")
        rows.append({
            "source": source,
            "id": record_id,
            "pmid": _optional_text(result, "pmid"),
            "pmcid": _optional_text(result, "pmcid"),
            "doi": _optional_text(result, "doi"),
            "title": _optional_text(result, "title"),
            "author_string": _optional_text(result, "authorString"),
            "journal_title": _optional_text(result, "journalTitle"),
            "publication_year": _optional_text(result, "pubYear"),
        })
    return {"hit_count": int(hit_count), "records": rows}


def search(query: str, max_results: int) -> Dict[str, Any]:
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    receipt: Dict[str, Any] = {
        "schema_version": "ignition.europe-pmc-query-search-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "source_code_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
        "query_sha256": query_hash,
        "source_endpoint": API_BASE,
        "retrieval_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_results": max_results,
        "acquisition_status": None,
        "http_status": None,
        "response_sha256": None,
        "status": "NOT_AVAILABLE",
        "hit_count": None,
        "returned_count": 0,
        "records": [],
        "claim_ceiling": CLAIM_CEILING,
    }
    fetched = _fetch(query, max_results)
    receipt["acquisition_status"] = fetched["acquisition_status"]
    receipt["http_status"] = fetched["http_status"]
    if fetched["acquisition_status"] != "OK":
        return receipt
    body = fetched["body"]
    receipt["response_sha256"] = hashlib.sha256(body).hexdigest()
    try:
        provider = _parse_provider_document(body, max_results)
    except (ToolInputError, UnicodeDecodeError, json.JSONDecodeError):
        receipt["acquisition_status"] = "INVALID_PROVIDER_RESPONSE"
        return receipt
    receipt["hit_count"] = provider["hit_count"]
    receipt["records"] = provider["records"]
    receipt["returned_count"] = len(provider["records"])
    receipt["status"] = "FOUND" if provider["records"] else "NO_MATCH"
    return receipt


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded JSON request from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="explicitly permit this invocation's fixed-host request")
    args = parser.parse_args(argv)
    if not args.stdin:
        print("INVALID_REQUEST: --stdin is required", file=sys.stderr)
        return 2
    if not args.allow_public_network:
        print("PUBLIC_NETWORK_CALL_REQUIRES --allow-public-network", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        query, max_results = parse_request(raw)
        receipt = search(query, max_results)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if receipt["acquisition_status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
