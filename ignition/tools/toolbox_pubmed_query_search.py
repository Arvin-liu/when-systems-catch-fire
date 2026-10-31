#!/usr/bin/env python3
"""Run a bounded, caller-authorized PubMed ESearch plus ESummary query."""
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


TOOL_ID = "research.search_pubmed_query"
TOOL_VERSION = "0.1.0"
ESEARCH_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
API_HOST = "eutils.ncbi.nlm.nih.gov"
TOOL_CONTACT = "IgnitionToolboxPubMedSearch"
MAX_REQUEST_BYTES = 4096
MAX_QUERY_CHARS = 512
MAX_QUERY_UTF8_BYTES = 2048
MAX_EMAIL_CHARS = 254
MAX_RESULTS = 10
MAX_RESPONSE_BYTES = 512 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 8192
CLAIM_CEILING = (
    "Bounded PubMed search and summary metadata returned for the supplied public query at retrieval time. "
    "The result set is not exhaustive, does not establish relevance, source authenticity, scientific support, "
    "publication status, or article content."
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


def parse_request(raw: bytes) -> Tuple[str, int, str]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError("request exceeds the declared byte limit")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON with unique object keys") from exc
    if not isinstance(document, dict) or set(document) != {"query", "max_results", "contact_email"}:
        raise ToolInputError("request must contain exactly query, max_results and contact_email")
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
    contact_email = document["contact_email"]
    if not isinstance(contact_email, str) or not 3 <= len(contact_email) <= MAX_EMAIL_CHARS:
        raise ToolInputError("contact_email must be a bounded email address")
    if (
        contact_email.count("@") != 1
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in contact_email)
        or any(char in contact_email for char in "\\/?#&=")
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,63}", contact_email)
    ):
        raise ToolInputError("contact_email must be an ASCII email address without control or URL delimiter characters")
    return query, max_results, contact_email


def _request_url(base: str, path: str, params: Dict[str, str]) -> str:
    if base != f"https://{API_HOST}/entrez/eutils/{path}.fcgi":
        raise RuntimeError("NCBI endpoint does not match the declared fixed HTTPS host")
    url = base + "?" + urllib.parse.urlencode(params)
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.path != f"/entrez/eutils/{path}.fcgi"
        or target.fragment or len(url) > 8192
    ):
        raise RuntimeError("NCBI request URL is outside the declared fixed-host boundary")
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


def _fetch(opener: Any, url: str) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{TOOL_CONTACT}/{TOOL_VERSION}",
            "Accept": "application/json",
        },
    )
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


def _optional_text(record: Dict[str, Any], key: str, limit: int = 4096) -> Optional[str]:
    value = record.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ToolInputError("invalid provider metadata field")
    text = " ".join(str(value).split())
    if len(text) > limit:
        raise ToolInputError("provider metadata field exceeds the declared limit")
    return text or None


def _parse_esearch(body: bytes, max_results: int) -> Dict[str, Any]:
    document = json.loads(body.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    if not isinstance(document, dict) or not isinstance(document.get("esearchresult"), dict):
        raise ToolInputError("provider response is missing esearchresult")
    result = document["esearchresult"]
    count = result.get("count")
    if isinstance(count, bool) or not isinstance(count, str) or not count.isdigit() or len(count) > 12:
        raise ToolInputError("provider response has an invalid PubMed hit count")
    ids = result.get("idlist")
    if not isinstance(ids, list) or len(ids) > max_results:
        raise ToolInputError("provider response has an invalid or oversized PubMed identifier list")
    normalized: List[str] = []
    for value in ids:
        if not isinstance(value, str) or not value.isdigit() or len(value) > 12:
            raise ToolInputError("provider returned a malformed PubMed identifier")
        normalized.append(value)
    if len(set(normalized)) != len(normalized):
        raise ToolInputError("provider returned duplicate PubMed identifiers")
    if int(count) < len(normalized):
        raise ToolInputError("provider hit count is smaller than its returned identifier list")
    if int(count) > 0 and not normalized:
        raise ToolInputError("provider reported hits but returned no identifiers")
    return {"hit_count": int(count), "pmids": normalized}


def _parse_authors(record: Dict[str, Any]) -> Dict[str, Any]:
    authors = record.get("authors")
    if authors is None:
        return {"author_names": [], "author_count": None, "authors_truncated": False}
    if not isinstance(authors, list):
        raise ToolInputError("provider returned an invalid authors field")
    names: List[str] = []
    for author in authors[:10]:
        if not isinstance(author, dict):
            raise ToolInputError("provider returned a malformed author record")
        name = _optional_text(author, "name", 256)
        if name:
            names.append(name)
    return {
        "author_names": names,
        "author_count": len(authors),
        "authors_truncated": len(authors) > 10,
    }


def _parse_doi(record: Dict[str, Any]) -> Optional[str]:
    articleids = record.get("articleids")
    if articleids is None:
        return None
    if not isinstance(articleids, list):
        raise ToolInputError("provider returned an invalid articleids field")
    values: List[str] = []
    for item in articleids:
        if not isinstance(item, dict):
            raise ToolInputError("provider returned a malformed article identifier")
        if item.get("idtype") == "doi":
            doi = _optional_text(item, "value", 512)
            if doi:
                values.append(doi)
    if len(values) > 1:
        return None
    return values[0] if values else None


def _parse_esummary(body: bytes, requested_ids: List[str]) -> Dict[str, Any]:
    document = json.loads(body.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    if not isinstance(document, dict) or not isinstance(document.get("result"), dict):
        raise ToolInputError("provider response is missing result")
    result = document["result"]
    returned_ids = result.get("uids")
    if not isinstance(returned_ids, list) or len(returned_ids) > len(requested_ids):
        raise ToolInputError("provider response has an invalid or oversized summary identifier list")
    normalized: List[str] = []
    for value in returned_ids:
        if not isinstance(value, str) or not value.isdigit() or value not in requested_ids:
            raise ToolInputError("provider returned an unexpected summary identifier")
        normalized.append(value)
    if len(set(normalized)) != len(normalized):
        raise ToolInputError("provider returned duplicate summary identifiers")
    records: List[Dict[str, Any]] = []
    missing: List[str] = []
    for pmid in requested_ids:
        record = result.get(pmid)
        if pmid not in normalized or not isinstance(record, dict):
            missing.append(pmid)
            continue
        if record.get("uid") != pmid:
            raise ToolInputError("summary record UID does not match its requested PubMed identifier")
        authors = _parse_authors(record)
        records.append({
            "pmid": pmid,
            "doi": _parse_doi(record),
            "title": _optional_text(record, "title"),
            **authors,
            "journal_title": _optional_text(record, "fulljournalname"),
            "publication_date": _optional_text(record, "pubdate", 128),
        })
    return {"records": records, "missing_summary_pmids": missing}


def search(query: str, max_results: int, contact_email: str) -> Dict[str, Any]:
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    receipt: Dict[str, Any] = {
        "schema_version": "ignition.pubmed-query-search-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "source_code_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
        "query_sha256": query_hash,
        "source_endpoints": {"esearch": ESEARCH_BASE, "esummary": ESUMMARY_BASE},
        "retrieval_timestamp_utc": timestamp,
        "max_results": max_results,
        "contact_email_sent_to_provider": True,
        "contact_email_retained": False,
        "acquisition_status": "NOT_AVAILABLE",
        "http_status": {"esearch": None, "esummary": None},
        "response_sha256": {"esearch": None, "esummary": None},
        "request_count": 0,
        "search_status": "NOT_AVAILABLE",
        "status": "NOT_AVAILABLE",
        "hit_count": None,
        "search_returned_pmids": [],
        "returned_count": 0,
        "missing_summary_pmids": [],
        "records": [],
        "claim_ceiling": CLAIM_CEILING,
    }
    opener = urllib.request.build_opener(_NoRedirectHandler())
    esearch_url = _request_url(ESEARCH_BASE, "esearch", {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "relevance",
        "tool": TOOL_CONTACT,
        "email": contact_email,
    })
    fetched = _fetch(opener, esearch_url)
    receipt["request_count"] = 1
    receipt["http_status"]["esearch"] = fetched["http_status"]
    receipt["acquisition_status"] = fetched["acquisition_status"]
    if fetched["acquisition_status"] != "OK":
        return receipt
    esearch_body = fetched["body"]
    receipt["response_sha256"]["esearch"] = hashlib.sha256(esearch_body).hexdigest()
    try:
        search_result = _parse_esearch(esearch_body, max_results)
    except (ToolInputError, UnicodeDecodeError, json.JSONDecodeError):
        receipt["acquisition_status"] = "INVALID_ESEARCH_RESPONSE"
        return receipt
    receipt["hit_count"] = search_result["hit_count"]
    receipt["search_returned_pmids"] = search_result["pmids"]
    receipt["search_status"] = "FOUND" if search_result["pmids"] else "NO_MATCH"
    if not search_result["pmids"]:
        receipt["acquisition_status"] = "OK"
        receipt["status"] = "NO_MATCH"
        return receipt

    esummary_url = _request_url(ESUMMARY_BASE, "esummary", {
        "db": "pubmed",
        "id": ",".join(search_result["pmids"]),
        "retmode": "json",
        "tool": TOOL_CONTACT,
        "email": contact_email,
    })
    fetched = _fetch(opener, esummary_url)
    receipt["request_count"] = 2
    receipt["http_status"]["esummary"] = fetched["http_status"]
    if fetched["acquisition_status"] != "OK":
        receipt["acquisition_status"] = "ESUMMARY_" + fetched["acquisition_status"]
        return receipt
    esummary_body = fetched["body"]
    receipt["response_sha256"]["esummary"] = hashlib.sha256(esummary_body).hexdigest()
    try:
        summary_result = _parse_esummary(esummary_body, search_result["pmids"])
    except (ToolInputError, UnicodeDecodeError, json.JSONDecodeError):
        receipt["acquisition_status"] = "INVALID_ESUMMARY_RESPONSE"
        return receipt
    receipt["records"] = summary_result["records"]
    receipt["missing_summary_pmids"] = summary_result["missing_summary_pmids"]
    receipt["returned_count"] = len(summary_result["records"])
    receipt["acquisition_status"] = "OK"
    receipt["status"] = "PARTIAL" if summary_result["missing_summary_pmids"] else (
        "FOUND" if summary_result["records"] else "NO_MATCH"
    )
    return receipt


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read one bounded JSON request from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="explicitly permit this invocation's two fixed-host requests")
    args = parser.parse_args(argv)
    if not args.stdin:
        print("INVALID_REQUEST: --stdin is required", file=sys.stderr)
        return 2
    if not args.allow_public_network:
        print("PUBLIC_NETWORK_CALL_REQUIRES --allow-public-network", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        query, max_results, contact_email = parse_request(raw)
        receipt = search(query, max_results, contact_email)
    except ToolInputError as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if receipt["acquisition_status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
