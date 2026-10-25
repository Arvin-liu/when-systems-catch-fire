#!/usr/bin/env python3
"""Look up bounded arXiv metadata for one caller-supplied modern identifier."""
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
from typing import Any, Dict, List, Optional


TOOL_ID = "research.lookup_arxiv_paper_metadata"
TOOL_VERSION = "0.1.0"
API_BASE = "https://export.arxiv.org/api/query"
API_HOST = "export.arxiv.org"
MAX_REQUEST_BYTES = 4096
MAX_RESPONSE_BYTES = 128 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 4096
ARXIV_ID_RE = re.compile(r"(?P<base>\d{2}(?:0[1-9]|1[0-2])\.\d{4,5})(?P<version>v[1-9][0-9]*)?\Z")
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
OPEN_SEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"
NS = {"atom": ATOM_NS, "arxiv": ARXIV_NS, "opensearch": OPEN_SEARCH_NS}
CLAIM_CEILING = (
    "Provider-reported arXiv metadata for one caller-supplied modern arXiv identifier. "
    "The lookup does not authenticate a paper, assess its contents, establish that cited claims are supported, "
    "or imply scientific acceptance."
)


class ToolInputError(ValueError):
    """Raised when caller input is outside this tool's bounded contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not let a fixed-host metadata request follow a redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _strict_object(pairs: List[Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_request(raw: bytes) -> str:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON with unique keys") from exc
    if not isinstance(document, dict) or set(document) != {"arxiv_id"}:
        raise ToolInputError("request must be an object with exactly one key: arxiv_id")
    value = document["arxiv_id"]
    if not isinstance(value, str) or value != value.strip() or len(value) > 32 or not ARXIV_ID_RE.fullmatch(value):
        raise ToolInputError("arxiv_id must be a modern YYMM.NNNN[N] identifier with an optional lowercase vN suffix")
    return value


def _request_url(arxiv_id: str) -> str:
    url = API_BASE + "?" + urllib.parse.urlencode({"id_list": arxiv_id})
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != API_HOST
        or parsed.port is not None
        or parsed.username
        or parsed.password
        or parsed.path != "/api/query"
        or parsed.fragment
    ):
        raise RuntimeError("arXiv metadata endpoint is not the declared fixed HTTPS host")
    return url


def _read_bounded(response: Any) -> tuple[Optional[bytes], Optional[str]]:
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


def _fetch(arxiv_id: str) -> Dict[str, Any]:
    url = _request_url(arxiv_id)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"IgnitionToolboxArxivMetadata/{TOOL_VERSION}", "Accept": "application/atom+xml"},
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
        if 300 <= status < 400:
            outcome = "REDIRECT_BLOCKED"
        elif status == 429:
            outcome = "RATE_LIMITED"
        else:
            outcome = "HTTP_ERROR"
        return {"acquisition_status": outcome, "http_status": status, "body": None}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None}


def _clean_text(element: Optional[ET.Element]) -> Optional[str]:
    if element is None or element.text is None:
        return None
    value = " ".join(element.text.split())
    return value or None


def _provider_entry_matches(entry_id: Optional[str], requested_id: str) -> bool:
    if not entry_id:
        return False
    try:
        parsed = urllib.parse.urlsplit(entry_id)
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname != "arxiv.org"
        or port is not None
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        return False
    prefix = "/abs/"
    if not parsed.path.startswith(prefix):
        return False
    match = ARXIV_ID_RE.fullmatch(parsed.path[len(prefix):])
    requested = ARXIV_ID_RE.fullmatch(requested_id)
    return bool(match and requested and match.group("base") == requested.group("base"))


def _parse_feed(body: bytes, requested_id: str) -> Dict[str, Any]:
    upper = body.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        return {"status": "INVALID_XML_RESPONSE", "record": None}
    try:
        feed = ET.fromstring(body)
    except ET.ParseError:
        return {"status": "INVALID_XML_RESPONSE", "record": None}
    if feed.tag != f"{{{ATOM_NS}}}feed":
        return {"status": "INVALID_PROVIDER_RESPONSE", "record": None}
    entries = feed.findall("atom:entry", NS)
    total_text = _clean_text(feed.find("opensearch:totalResults", NS))
    try:
        total = int(total_text) if total_text is not None else None
    except ValueError:
        total = None
    if total == 0 and not entries:
        return {"status": "NO_MATCH", "record": None}
    if total != 1 or len(entries) != 1:
        return {"status": "INVALID_PROVIDER_RESPONSE", "record": None}
    entry = entries[0]
    entry_id = _clean_text(entry.find("atom:id", NS))
    if entry_id and "/api/errors#" in entry_id:
        return {"status": "PROVIDER_ERROR_ENTRY", "record": None}
    if not _provider_entry_matches(entry_id, requested_id):
        return {"status": "INVALID_PROVIDER_RESPONSE", "record": None}
    authors = []
    for author in entry.findall("atom:author", NS):
        name = _clean_text(author.find("atom:name", NS))
        if name:
            authors.append(name)
    categories = []
    for category in entry.findall("atom:category", NS):
        term = category.attrib.get("term")
        if isinstance(term, str) and term and term not in categories:
            categories.append(term)
    primary = entry.find("arxiv:primary_category", NS)
    primary_category = primary.attrib.get("term") if primary is not None else None
    record = {
        "requested_id": requested_id,
        "entry_id": entry_id,
        "title": _clean_text(entry.find("atom:title", NS)),
        "authors": authors,
        "published": _clean_text(entry.find("atom:published", NS)),
        "updated": _clean_text(entry.find("atom:updated", NS)),
        "primary_category": primary_category,
        "categories": categories,
        "journal_ref": _clean_text(entry.find("arxiv:journal_ref", NS)),
        "doi": _clean_text(entry.find("arxiv:doi", NS)),
    }
    if not record["title"] or not record["authors"] or not record["published"] or not record["updated"]:
        return {"status": "INVALID_PROVIDER_RESPONSE", "record": None}
    return {"status": "FOUND", "record": record}


def lookup(raw: bytes) -> Dict[str, Any]:
    arxiv_id = parse_request(raw)
    request_url = _request_url(arxiv_id)
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    fetched = _fetch(arxiv_id)
    result: Dict[str, Any] = {
        "schema_version": "toolbox-arxiv-metadata-lookup-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": fetched["acquisition_status"],
        "requested_id": arxiv_id,
        "request_url": request_url,
        "retrieved_at_utc": retrieved,
        "http_status": fetched["http_status"],
        "response_sha256": None,
        "response_bytes": None,
        "record": None,
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": [
            "The lookup does not fetch or retain abstracts, article files, or full text.",
            "Metadata presence does not establish paper authenticity, content support, scientific validity, or publication acceptance.",
            "The provider response is not independently authenticated by this tool.",
        ],
        "tool_source_sha256": _sha256(Path(__file__).resolve()),
        "request_sha256": hashlib.sha256(raw).hexdigest(),
    }
    if fetched["acquisition_status"] != "OK":
        return result
    body = fetched["body"]
    if not isinstance(body, bytes):
        result["status"] = "INVALID_PROVIDER_RESPONSE"
        return result
    result["response_sha256"] = hashlib.sha256(body).hexdigest()
    result["response_bytes"] = len(body)
    parsed = _parse_feed(body, arxiv_id)
    result["status"] = parsed["status"]
    result["record"] = parsed["record"]
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Read limited metadata for one caller-supplied arXiv ID.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stdin", action="store_true", help="read a UTF-8 JSON request from stdin")
    group.add_argument("--arxiv-id", help="one modern arXiv ID, such as 2610.04074")
    parser.add_argument("--allow-public-network", action="store_true", help="explicitly allow one public arXiv API GET")
    args = parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1) if args.stdin else json.dumps({"arxiv_id": args.arxiv_id}).encode("utf-8")
    try:
        parse_request(raw)
    except ToolInputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not args.allow_public_network:
        print("public arXiv metadata lookup requires --allow-public-network for this invocation", file=sys.stderr)
        return 2
    try:
        result = lookup(raw)
    except ToolInputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
