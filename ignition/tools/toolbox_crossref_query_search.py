#!/usr/bin/env python3
"""Bounded, explicit Crossref query-to-DOI discovery for the toolbox."""
from __future__ import annotations

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


TOOL_ID = "research.search_crossref_query"
TOOL_VERSION = "0.1.0"
API_ENDPOINT = "https://api.crossref.org/v1/works"
API_HOST = "api.crossref.org"
SELECT_FIELDS = "DOI,title,author,issued,type,publisher,container-title,is-referenced-by-count"
MAX_REQUEST_BYTES = 4096
MAX_QUERY_CHARS = 512
MAX_QUERY_UTF8_BYTES = 2048
MAX_RESULTS = 10
MAX_RESPONSE_BYTES = 512 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 8192
MAX_DOI_LENGTH = 1100
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
CLAIM_CEILING = (
    "At most ten Crossref Works metadata rows returned for one caller-supplied query at retrieval time. "
    "The request is not exhaustive and establishes no relevance, source authenticity, metadata completeness, "
    "article content, scientific support, publication status, or scientific validity."
)


class ToolInputError(ValueError):
    """Raised when the exact bounded JSON input contract is violated."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent a fixed-host request from following a redirect elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ToolInputError("non-standard JSON constants are not accepted")


def parse_request(raw: bytes) -> tuple[str, int]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError("request exceeds the declared byte limit")
    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be UTF-8 JSON with unique keys") from exc
    if not isinstance(payload, dict) or set(payload) != {"query", "max_results"}:
        raise ToolInputError("request must contain exactly query and max_results")
    query = payload["query"]
    if not isinstance(query, str) or not query or query != query.strip():
        raise ToolInputError("query must be non-empty and already trimmed")
    if len(query) > MAX_QUERY_CHARS or len(query.encode("utf-8")) > MAX_QUERY_UTF8_BYTES:
        raise ToolInputError("query exceeds its character or UTF-8 byte limit")
    if any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in query):
        raise ToolInputError("query must not contain control characters")
    limit = payload["max_results"]
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
        raise ToolInputError("max_results must be an integer from 1 through 10")
    return query, limit


def _request_url(query: str, max_results: int) -> str:
    params = urllib.parse.urlencode({
        "query": query,
        "rows": str(max_results),
        "select": SELECT_FIELDS,
    })
    url = API_ENDPOINT + "?" + params
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.path != "/v1/works"
        or target.fragment or len(url) > 8192
    ):
        raise RuntimeError("Crossref endpoint is not the declared fixed HTTPS v1 host")
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


def _fetch(query: str, max_results: int) -> dict[str, Any]:
    url = _request_url(query, max_results)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"IgnitionToolboxCrossrefSearch/{TOOL_VERSION}", "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    request_sha256 = hashlib.sha256(url.encode("utf-8")).hexdigest()
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None,
                        "request_sha256": request_sha256, "usage_headers": {}}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type not in {"application/json", "text/json"} and not content_type.endswith("+json"):
                return {"acquisition_status": "NON_JSON_RESPONSE", "http_status": status, "body": None,
                        "request_sha256": request_sha256, "usage_headers": {}}
            body, error = _read_bounded(response)
            usage_headers = {}
            for name in ("x-rate-limit-limit", "x-rate-limit-interval", "x-rate-limit-type"):
                value = response.headers.get(name)
                if value is not None and len(value) <= 64 and not any(ord(ch) < 0x20 for ch in value):
                    usage_headers[name] = value
            if error:
                return {"acquisition_status": error, "http_status": status, "body": None,
                        "request_sha256": request_sha256, "usage_headers": usage_headers}
            return {"acquisition_status": "OK", "http_status": status, "body": body,
                    "request_sha256": request_sha256, "usage_headers": usage_headers}
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        outcome = "REDIRECT_BLOCKED" if 300 <= status < 400 else ("RATE_LIMITED" if status == 429 else "HTTP_ERROR")
        return {"acquisition_status": outcome, "http_status": status, "body": None,
                "request_sha256": request_sha256, "usage_headers": {}}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None,
                "request_sha256": request_sha256, "usage_headers": {}}


def _text(value: Any, max_chars: int, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > max_chars:
        raise ValueError(f"invalid {field} field")
    if any(ord(char) < 0x20 and char not in "\t\n\r" for char in value):
        raise ValueError(f"invalid {field} field")
    return " ".join(value.split()) or None


def _list_text(value: Any, field: str, max_items: int = 10000) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > max_items:
        raise ValueError(f"invalid {field} list")
    result = []
    for item in value:
        text = _text(item, 4096, field)
        if text is not None:
            result.append(text)
    return result


def _year(message: dict[str, Any]) -> int | None:
    issued = message.get("issued")
    if issued is None:
        return None
    if not isinstance(issued, dict):
        raise ValueError("invalid issued field")
    date_parts = issued.get("date-parts")
    if date_parts is None:
        return None
    if not isinstance(date_parts, list) or not date_parts:
        raise ValueError("invalid issued date-parts")
    first = date_parts[0]
    if not isinstance(first, list) or not first:
        raise ValueError("invalid issued date-parts")
    year = first[0]
    if year is None:
        return None
    if isinstance(year, bool) or not isinstance(year, int) or not 0 <= year <= 3000:
        raise ValueError("invalid issued year")
    return year


def _parse_records(body: bytes, max_results: int) -> tuple[int, list[dict[str, Any]]]:
    document = json.loads(body.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    if not isinstance(document, dict) or not isinstance(document.get("message"), dict):
        raise ValueError("response does not match the Crossref v1 envelope")
    message = document["message"]
    total = message.get("total-results")
    if isinstance(total, bool) or not isinstance(total, (int, str)) or not str(total).isdigit():
        raise ValueError("response has an invalid total-results value")
    items = message.get("items")
    if not isinstance(items, list) or len(items) > max_results:
        raise ValueError("response items are missing or exceed the requested result limit")

    records: list[dict[str, Any]] = []
    seen_dois: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("response contains a non-object Crossref item")
        doi = item.get("DOI")
        if doi is not None and (
            not isinstance(doi, str) or len(doi) > MAX_DOI_LENGTH or not DOI_RE.fullmatch(doi)
        ):
            raise ValueError("response contains an invalid DOI")
        if doi is not None:
            normalized_doi = doi.casefold()
            if normalized_doi in seen_dois:
                raise ValueError("response contains a duplicate DOI")
            seen_dois.add(normalized_doi)
        titles = _list_text(item.get("title"), "title", max_items=100)
        authors = item.get("author")
        if authors is None:
            authors = []
        if not isinstance(authors, list) or len(authors) > 10000:
            raise ValueError("response contains an invalid author list")
        author_names: list[str] = []
        for author in authors:
            if not isinstance(author, dict):
                raise ValueError("response contains a non-object author")
            literal = _text(author.get("name"), 512, "author.name")
            given = _text(author.get("given"), 512, "author.given")
            family = _text(author.get("family"), 512, "author.family")
            name = (literal or " ".join(part for part in (given, family) if part) or None)
            if name is not None and len(name) > 1024:
                name = name[:1024]
            if name:
                author_names.append(name)
        publishers = _text(item.get("publisher"), 512, "publisher")
        containers = _list_text(item.get("container-title"), "container-title", max_items=100)
        work_type = _text(item.get("type"), 256, "type")
        cited = item.get("is-referenced-by-count")
        if cited is not None and (isinstance(cited, bool) or not isinstance(cited, int) or cited < 0):
            raise ValueError("response contains an invalid is-referenced-by-count")
        records.append({
            "doi": doi,
            "title": titles[0] if titles else None,
            "publication_year": _year(item),
            "type": work_type,
            "publisher": publishers,
            "container_title": containers[0] if containers else None,
            "author_names": author_names[:10],
            "author_count": len(author_names),
            "authors_truncated": len(author_names) > 10,
            "cited_by_count": cited,
        })
    return int(total), records


def search(raw: bytes) -> dict[str, Any]:
    query, max_results = parse_request(raw)
    fetched = _fetch(query, max_results)
    body = fetched.get("body")
    acquisition = fetched.get("acquisition_status")
    receipt: dict[str, Any] = {
        "schema_version": "ignition.crossref-query-search-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": "FAILED",
        "acquisition_status": acquisition,
        "http_status": fetched.get("http_status"),
        "source_endpoint": API_ENDPOINT,
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "max_results": max_results,
        "request_count": 1,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "request_sha256": fetched.get("request_sha256"),
        "response_sha256": None,
        "response_bytes": 0,
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "provider_hit_count": None,
        "returned_count": 0,
        "usage_headers": fetched.get("usage_headers", {}),
        "records": [],
        "claim_ceiling": CLAIM_CEILING,
    }
    if acquisition != "OK" or not isinstance(body, bytes):
        return receipt
    receipt["response_sha256"] = hashlib.sha256(body).hexdigest()
    receipt["response_bytes"] = len(body)
    try:
        total, records = _parse_records(body, max_results)
    except (OverflowError, TypeError, ValueError):
        receipt["acquisition_status"] = "INVALID_RESPONSE"
        return receipt
    receipt["provider_hit_count"] = total
    receipt["records"] = records
    receipt["returned_count"] = len(records)
    receipt["status"] = "FOUND" if records else "NOT_FOUND"
    return receipt


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or set(args) != {"--stdin", "--allow-public-network"}:
        sys.stderr.write("Crossref toolbox search requires exactly --stdin --allow-public-network.\n")
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        result = search(raw)
    except ToolInputError as exc:
        sys.stderr.write(f"Invalid Crossref toolbox search input: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0 if result["acquisition_status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
