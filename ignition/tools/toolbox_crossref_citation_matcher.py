#!/usr/bin/env python3
"""Return at most two Crossref bibliographic candidates for one citation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOL_ID = "research.match_crossref_citation"
TOOL_VERSION = "0.1.0"
API_ENDPOINT = "https://api.crossref.org/v1/works"
API_HOST = "api.crossref.org"
SELECT_FIELDS = "DOI,title,author,issued,type,publisher,container-title,volume,issue,page"
MAX_REQUEST_BYTES = 4096
MAX_CITATION_CHARS = 2048
MAX_CITATION_UTF8_BYTES = 4096
MAX_RESPONSE_BYTES = 128 * 1024
MAX_RESPONSE_DURATION_SECONDS = 8
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 4096
MAX_DOI_LENGTH = 1100
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
CLAIM_CEILING = (
    "Returns up to two Crossref Works records reported for one caller-supplied "
    "bibliographic citation and preserves any provider relevance scores. It does "
    "not verify a citation-to-DOI match, rank scientific evidence, establish "
    "metadata completeness, or assess article content or scientific support."
)


class ToolInputError(ValueError):
    """Raised when the exact bounded JSON input contract is violated."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not follow the fixed-host request to another destination."""

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


def parse_request(raw: bytes) -> str:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be UTF-8 JSON with unique keys") from exc
    if not isinstance(payload, dict) or set(payload) != {"citation"}:
        raise ToolInputError("request must contain exactly citation")
    citation = payload["citation"]
    if not isinstance(citation, str) or not citation or citation != citation.strip():
        raise ToolInputError("citation must be non-empty, trimmed text")
    if len(citation) > MAX_CITATION_CHARS or len(citation.encode("utf-8")) > MAX_CITATION_UTF8_BYTES:
        raise ToolInputError("citation exceeds its character or UTF-8 byte limit")
    if any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in citation):
        raise ToolInputError("citation must not contain control characters")
    return citation


def _request_url(citation: str) -> str:
    params = urllib.parse.urlencode({
        "query.bibliographic": citation,
        "rows": "2",
        "select": SELECT_FIELDS,
    })
    url = API_ENDPOINT + "?" + params
    target = urllib.parse.urlsplit(url)
    if (
        target.scheme != "https" or target.hostname != API_HOST or target.port is not None
        or target.username or target.password or target.path != "/v1/works"
        or target.fragment or len(url) > 16384
    ):
        raise RuntimeError("Crossref endpoint is outside the fixed HTTPS host boundary")
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


def _fetch(citation: str, opener: Any | None = None) -> dict[str, Any]:
    url = _request_url(citation)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"IgnitionCrossrefCitationMatcher/{TOOL_VERSION} (https://github.com/Arvin-liu/when-systems-catch-fire)",
            "Accept": "application/json",
        },
    )
    if opener is None:
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
            body, read_error = _read_bounded(response)
            usage_headers = {}
            for name in ("x-rate-limit-limit", "x-rate-limit-interval", "x-rate-limit-type"):
                value = response.headers.get(name)
                if value is not None and len(value) <= 64 and not any(ord(char) < 0x20 for char in value):
                    usage_headers[name] = value
            if read_error:
                return {"acquisition_status": read_error, "http_status": status, "body": None,
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


def _list_text(value: Any, field: str, max_items: int = 100) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > max_items:
        raise ValueError(f"invalid {field} list")
    result = []
    for item in value:
        text = _text(item, 2048, field)
        if text is not None:
            result.append(text)
    return result


def _year(item: dict[str, Any]) -> int | None:
    issued = item.get("issued")
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


def _score(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("invalid Crossref relevance score")
    score = float(value)
    if not math.isfinite(score):
        raise ValueError("invalid Crossref relevance score")
    return score


def _parse_records(body: bytes) -> tuple[int, list[dict[str, Any]]]:
    document = json.loads(
        body.decode("utf-8", errors="strict"),
        object_pairs_hook=_strict_object,
        parse_constant=_reject_constant,
    )
    if not isinstance(document, dict) or not isinstance(document.get("message"), dict):
        raise ValueError("response does not match the Crossref v1 envelope")
    message = document["message"]
    total = message.get("total-results")
    if isinstance(total, bool) or not isinstance(total, (int, str)) or not str(total).isdigit():
        raise ValueError("response has an invalid total-results value")
    total_count = int(total)
    if total_count > 2_147_483_647:
        raise ValueError("response total-results exceeds the declared integer bound")
    items = message.get("items")
    if not isinstance(items, list) or len(items) > 2:
        raise ValueError("response items are missing or exceed the two-result limit")

    records: list[dict[str, Any]] = []
    seen_dois: set[str] = set()
    for rank, item in enumerate(items, start=1):
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
        titles = _list_text(item.get("title"), "title")
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
            name = literal or " ".join(part for part in (given, family) if part) or None
            if name:
                author_names.append(name[:512])
        records.append({
            "provider_rank": rank,
            "doi": doi,
            "title": titles[0] if titles else None,
            "publication_year": _year(item),
            "type": _text(item.get("type"), 256, "type"),
            "publisher": _text(item.get("publisher"), 512, "publisher"),
            "container_title": (_list_text(item.get("container-title"), "container-title")[0]
                                if item.get("container-title") else None),
            "volume": _text(item.get("volume"), 128, "volume"),
            "issue": _text(item.get("issue"), 128, "issue"),
            "page": _text(item.get("page"), 256, "page"),
            "author_names": author_names[:10],
            "author_count": len(author_names),
            "authors_truncated": len(author_names) > 10,
            "crossref_relevance_score": _score(item.get("score")),
        })
    return total_count, records


def _score_tie_status(records: list[dict[str, Any]]) -> str:
    if len(records) < 2:
        return "INSUFFICIENT_CANDIDATES"
    first = records[0]["crossref_relevance_score"]
    second = records[1]["crossref_relevance_score"]
    if first is None or second is None:
        return "SCORE_NOT_RETURNED"
    return "TOP_SCORES_EQUAL_AS_REPORTED" if first == second else "TOP_SCORES_DIFFER_AS_REPORTED"


def match(raw: bytes, opener: Any | None = None) -> dict[str, Any]:
    citation = parse_request(raw)
    fetched = _fetch(citation, opener=opener)
    body = fetched.get("body")
    receipt: dict[str, Any] = {
        "schema_version": "ignition.crossref-citation-matcher-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "citation_sha256": hashlib.sha256(citation.encode("utf-8")).hexdigest(),
        "source_endpoint": API_ENDPOINT,
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "UNAVAILABLE",
        "acquisition_status": fetched["acquisition_status"],
        "http_status": fetched["http_status"],
        "request_count": 1,
        "request_sha256": fetched["request_sha256"],
        "response_sha256": None,
        "response_bytes": 0,
        "provider_hit_count": None,
        "returned_count": 0,
        "top_two_score_status": "NOT_EVALUATED",
        "usage_headers": fetched["usage_headers"],
        "candidates": [],
        "claim_ceiling": CLAIM_CEILING,
    }
    if fetched["acquisition_status"] != "OK" or not isinstance(body, bytes):
        return receipt
    receipt["response_sha256"] = hashlib.sha256(body).hexdigest()
    receipt["response_bytes"] = len(body)
    try:
        total, candidates = _parse_records(body)
    except (OverflowError, TypeError, UnicodeDecodeError, json.JSONDecodeError, ToolInputError, ValueError):
        receipt["status"] = "INVALID_RESPONSE"
        receipt["acquisition_status"] = "INVALID_RESPONSE"
        return receipt
    receipt["status"] = "CANDIDATES_REPORTED" if candidates else "NO_CANDIDATE_REPORTED"
    receipt["provider_hit_count"] = total
    receipt["returned_count"] = len(candidates)
    receipt["top_two_score_status"] = _score_tie_status(candidates)
    receipt["candidates"] = candidates
    return receipt


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or set(args) != {"--stdin", "--allow-public-network"}:
        sys.stderr.write("Crossref citation matcher requires exactly --stdin --allow-public-network.\n")
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        result = match(raw)
    except ToolInputError as exc:
        sys.stderr.write(f"Invalid Crossref citation matcher input: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return 0 if result["acquisition_status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
