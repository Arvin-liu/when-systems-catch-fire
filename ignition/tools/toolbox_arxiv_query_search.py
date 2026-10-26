#!/usr/bin/env python3
"""Search arXiv for a bounded set of provider-reported metadata records."""
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
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


TOOL_ID = "research.search_arxiv_query"
TOOL_VERSION = "0.1.0"
API_BASE = "https://export.arxiv.org/api/query"
API_HOST = "export.arxiv.org"
MAX_REQUEST_BYTES = 4096
MAX_QUERY_CHARS = 512
MAX_QUERY_UTF8_BYTES = 2048
MAX_RESULTS = 10
MAX_RESPONSE_BYTES = 512 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 8192
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
OPEN_SEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"
NS = {"atom": ATOM_NS, "arxiv": ARXIV_NS, "opensearch": OPEN_SEARCH_NS}
MODERN_ID_RE = re.compile(r"\d{4}\.\d{4,5}(?:v[1-9][0-9]*)?\Z")
LEGACY_ID_RE = re.compile(r"[a-z][a-z0-9.-]*/\d{7}(?:v[1-9][0-9]*)?\Z")
CLAIM_CEILING = (
    "A bounded, time-stamped set of arXiv provider-reported metadata for one caller-supplied query. "
    "The search is not exhaustive and establishes no relevance, source authenticity, scientific support, "
    "publication status, or scientific validity."
)


class ToolInputError(ValueError):
    """Raised when caller input falls outside this tool's bounded contract."""


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
        "search_query": query,
        "start": "0",
        "max_results": str(max_results),
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = API_BASE + "?" + params
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.path != "/api/query"
        or target.fragment or len(url) > 8192
    ):
        raise RuntimeError("arXiv search endpoint is not the declared fixed HTTPS host")
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
        headers={"User-Agent": f"IgnitionToolboxArxivQuerySearch/{TOOL_VERSION}", "Accept": "application/atom+xml"},
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type not in {"application/atom+xml", "application/xml", "text/xml"}:
                return {"acquisition_status": "NON_ATOM_RESPONSE", "http_status": status, "body": None}
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


def _clean_text(element: Optional[ET.Element], *, limit: int = 4096) -> Optional[str]:
    if element is None or element.text is None:
        return None
    value = " ".join(element.text.split())
    if len(value) > limit:
        raise ToolInputError("provider metadata field exceeds the declared limit")
    return value or None


def _provider_entry_id(value: Optional[str]) -> Optional[Tuple[str, str]]:
    if not value:
        return None
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme not in {"http", "https"} or parsed.hostname != "arxiv.org" or port is not None
        or parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.path.startswith("/abs/")
    ):
        return None
    identifier = parsed.path[len("/abs/"):]
    if not (MODERN_ID_RE.fullmatch(identifier) or LEGACY_ID_RE.fullmatch(identifier)):
        return None
    return value, identifier


def _parse_feed(body: bytes, max_results: int) -> Dict[str, Any]:
    upper = body.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        return {"status": "INVALID_XML_RESPONSE", "hit_count": None, "records": []}
    try:
        feed = ET.fromstring(body)
    except ET.ParseError:
        return {"status": "INVALID_XML_RESPONSE", "hit_count": None, "records": []}
    if feed.tag != f"{{{ATOM_NS}}}feed":
        return {"status": "INVALID_PROVIDER_RESPONSE", "hit_count": None, "records": []}
    total_text = _clean_text(feed.find("opensearch:totalResults", NS), limit=20)
    if not total_text or not total_text.isdigit():
        return {"status": "INVALID_PROVIDER_RESPONSE", "hit_count": None, "records": []}
    hit_count = int(total_text)
    entries = feed.findall("atom:entry", NS)
    if hit_count == 0 and not entries:
        return {"status": "NO_MATCH", "hit_count": 0, "records": []}
    if not entries or hit_count < len(entries) or len(entries) > max_results:
        return {"status": "INVALID_PROVIDER_RESPONSE", "hit_count": hit_count, "records": []}

    records: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    try:
        for entry in entries:
            entry_id = _clean_text(entry.find("atom:id", NS), limit=512)
            if entry_id and "/api/errors#" in entry_id:
                return {"status": "PROVIDER_ERROR_ENTRY", "hit_count": hit_count, "records": []}
            parsed_id = _provider_entry_id(entry_id)
            if parsed_id is None or parsed_id[1] in seen_ids:
                return {"status": "INVALID_PROVIDER_RESPONSE", "hit_count": hit_count, "records": []}
            seen_ids.add(parsed_id[1])
            authors = []
            all_authors = entry.findall("atom:author", NS)
            for author in all_authors[:10]:
                name = _clean_text(author.find("atom:name", NS), limit=256)
                if name:
                    authors.append(name)
            categories: List[str] = []
            for category in entry.findall("atom:category", NS)[:32]:
                term = category.attrib.get("term")
                if term is not None and (not isinstance(term, str) or len(term) > 128):
                    raise ToolInputError("provider returned an invalid category")
                if term and term not in categories:
                    categories.append(term)
            primary = entry.find("arxiv:primary_category", NS)
            primary_category = primary.attrib.get("term") if primary is not None else None
            if primary_category is not None and len(primary_category) > 128:
                raise ToolInputError("provider returned an oversized primary category")
            title = _clean_text(entry.find("atom:title", NS), limit=2048)
            published = _clean_text(entry.find("atom:published", NS), limit=64)
            updated = _clean_text(entry.find("atom:updated", NS), limit=64)
            if not title or not published or not updated:
                return {"status": "INVALID_PROVIDER_RESPONSE", "hit_count": hit_count, "records": []}
            records.append({
                "arxiv_id": parsed_id[1],
                "entry_id": parsed_id[0],
                "title": title,
                "author_names": authors,
                "author_count": len(all_authors),
                "authors_truncated": len(all_authors) > 10,
                "published": published,
                "updated": updated,
                "primary_category": primary_category,
                "categories": categories,
                "journal_ref": _clean_text(entry.find("arxiv:journal_ref", NS), limit=1024),
                "doi": _clean_text(entry.find("arxiv:doi", NS), limit=512),
            })
    except ToolInputError:
        return {"status": "INVALID_PROVIDER_RESPONSE", "hit_count": hit_count, "records": []}
    return {"status": "FOUND", "hit_count": hit_count, "records": records}


def search(raw: bytes) -> Dict[str, Any]:
    query, max_results = parse_request(raw)
    receipt: Dict[str, Any] = {
        "schema_version": "ignition.arxiv-query-search-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "source_code_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "source_endpoint": API_BASE,
        "retrieval_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_results": max_results,
        "request_count": 0,
        "acquisition_status": "NOT_AVAILABLE",
        "http_status": None,
        "response_sha256": None,
        "response_bytes": None,
        "status": "NOT_AVAILABLE",
        "hit_count": None,
        "returned_count": 0,
        "records": [],
        "claim_ceiling": CLAIM_CEILING,
        "rate_limit_note": "Caller must serialize arXiv API use and keep at least 3 seconds between requests across all controlled machines.",
        "request_sha256": hashlib.sha256(raw).hexdigest(),
    }
    fetched = _fetch(query, max_results)
    receipt["request_count"] = 1
    receipt["acquisition_status"] = fetched["acquisition_status"]
    receipt["http_status"] = fetched["http_status"]
    if fetched["acquisition_status"] != "OK":
        receipt["status"] = fetched["acquisition_status"]
        return receipt
    body = fetched["body"]
    if not isinstance(body, bytes):
        receipt["acquisition_status"] = "INVALID_PROVIDER_RESPONSE"
        receipt["status"] = "INVALID_PROVIDER_RESPONSE"
        return receipt
    receipt["response_sha256"] = hashlib.sha256(body).hexdigest()
    receipt["response_bytes"] = len(body)
    try:
        parsed = _parse_feed(body, max_results)
    except (ToolInputError, UnicodeDecodeError):
        parsed = {"status": "INVALID_PROVIDER_RESPONSE", "hit_count": None, "records": []}
    receipt["status"] = parsed["status"]
    receipt["hit_count"] = parsed["hit_count"]
    receipt["records"] = parsed["records"]
    receipt["returned_count"] = len(parsed["records"])
    if parsed["status"] not in {"FOUND", "NO_MATCH"}:
        receipt["acquisition_status"] = parsed["status"]
    return receipt


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded UTF-8 JSON query from stdin")
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
        parse_request(raw)
        receipt = search(raw)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if receipt["status"] in {"FOUND", "NO_MATCH"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
