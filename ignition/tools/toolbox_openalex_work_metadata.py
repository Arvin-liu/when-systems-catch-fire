#!/usr/bin/env python3
"""Look up bounded OpenAlex Work metadata and location records by DOI, stdout only.

The optional adapter makes one fixed-host public GET per invocation. It
returns a small selected projection and a digest, never stores the response,
and does not make scientific, authenticity, or retraction adjudications.
"""
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
from typing import Any, Dict, List, Optional, Tuple


TOOL_VERSION = "0.2.0"
API_BASE = "https://api.openalex.org/works"
API_HOST = "api.openalex.org"
MAX_REQUEST_BYTES = 16 * 1024
MAX_DOIS = 5
MAX_DOI_LENGTH = 128
MAX_RESPONSE_BYTES = 256 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 8 * 1024
MAX_RESULTS = 100
MAX_LOCATIONS_PER_WORK = 25
MAX_LOCATION_TEXT_LENGTH = 2048
SELECT_FIELDS = "id,doi,display_name,publication_year,type,is_retracted,open_access,locations,best_oa_location"
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\Z")
OPENALEX_WORK_ID_RE = re.compile(r"https://openalex\.org/W[0-9]+\Z")
CLAIM_CEILING = (
    "OpenAlex Work metadata and provider-reported open-access/location fields in this response only. "
    "A reported URL, license, access status, or is_retracted flag does not establish URL availability, "
    "legal reuse permission, source authenticity, complete coverage, article content, scientific truth, "
    "or authoritative retraction status. Returned URLs are never requested."
)


class ToolInputError(ValueError):
    """Raised when caller input does not match the bounded tool contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep a fixed-host request from following a redirect to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _strict_object(pairs: List[Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-standard JSON constant")


def parse_request(raw: bytes) -> List[str]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError("request exceeds the byte limit")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
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


def _normalize_response_doi(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    doi = value.strip()
    lowered = doi.casefold()
    for prefix in ("https://doi.org/", "http://doi.org/"):
        if lowered.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.casefold()


def _request_url(dois: List[str]) -> str:
    filter_value = "doi:" + "|".join(dois)
    query = urllib.parse.urlencode({
        "filter": filter_value,
        "per_page": str(MAX_RESULTS),
        "select": SELECT_FIELDS,
    })
    url = API_BASE + "?" + query
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != API_HOST
        or parsed.port is not None
        or parsed.username
        or parsed.password
        or parsed.path != "/works"
        or not parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("OpenAlex endpoint configuration is not the fixed HTTPS host")
    return url


def _safe_header(headers: Any, name: str) -> Optional[str]:
    value = headers.get(name) if headers is not None else None
    if not isinstance(value, str) or len(value) > 64 or any(ord(char) < 32 for char in value):
        return None
    return value


def _usage_headers(headers: Any) -> Dict[str, Optional[str]]:
    names = (
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Credits-Used",
        "X-RateLimit-Reset",
    )
    return {name: _safe_header(headers, name) for name in names}


def _fetch(dois: List[str]) -> Dict[str, Any]:
    url = _request_url(dois)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "IgnitionToolboxOpenAlex/{}".format(TOOL_VERSION),
            "Accept": "application/json",
        },
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            headers = response.headers
            usage = _usage_headers(headers)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None, "usage_headers": usage}
            content_type = headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type != "application/json" and not content_type.endswith("+json"):
                return {"acquisition_status": "NON_JSON_RESPONSE", "http_status": status, "body": None, "usage_headers": usage}

            deadline = time.monotonic() + MAX_RESPONSE_DURATION_SECONDS
            chunks: List[bytes] = []
            total_bytes = 0
            while total_bytes <= MAX_RESPONSE_BYTES:
                if time.monotonic() >= deadline:
                    return {"acquisition_status": "RESPONSE_TIMEOUT", "http_status": status, "body": None, "usage_headers": usage}
                chunk = response.read(min(RESPONSE_CHUNK_BYTES, MAX_RESPONSE_BYTES + 1 - total_bytes))
                if time.monotonic() > deadline:
                    return {"acquisition_status": "RESPONSE_TIMEOUT", "http_status": status, "body": None, "usage_headers": usage}
                if not chunk:
                    break
                chunks.append(chunk)
                total_bytes += len(chunk)
            if total_bytes > MAX_RESPONSE_BYTES:
                return {"acquisition_status": "RESPONSE_TOO_LARGE", "http_status": status, "body": None, "usage_headers": usage}
            return {
                "acquisition_status": "OK",
                "http_status": status,
                "body": b"".join(chunks),
                "usage_headers": usage,
            }
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        outcome = "REDIRECT_BLOCKED" if 300 <= status < 400 else ("RATE_LIMITED" if status == 429 else ("NOT_FOUND" if status == 404 else "HTTP_ERROR"))
        usage = _usage_headers(exc.headers)
        return {"acquisition_status": outcome, "http_status": status, "body": None, "usage_headers": usage}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None, "usage_headers": {}}


def _valid_work(work: Dict[str, Any]) -> bool:
    work_id = work.get("id")
    if not isinstance(work_id, str) or not OPENALEX_WORK_ID_RE.fullmatch(work_id):
        return False
    if work.get("doi") is not None and not isinstance(work.get("doi"), str):
        return False
    if work.get("display_name") is not None and not isinstance(work.get("display_name"), str):
        return False
    if work.get("publication_year") is not None and type(work.get("publication_year")) is not int:
        return False
    if work.get("type") is not None and not isinstance(work.get("type"), str):
        return False
    if work.get("is_retracted") is not None and type(work.get("is_retracted")) is not bool:
        return False
    if "locations" in work:
        locations = work.get("locations")
        if locations is not None and (
            not isinstance(locations, list)
            or any(not _valid_location(location) for location in locations)
        ):
            return False
    if "best_oa_location" in work and work.get("best_oa_location") is not None:
        if not _valid_location(work["best_oa_location"]):
            return False
    if "open_access" in work and work.get("open_access") is not None:
        if not _valid_open_access(work["open_access"]):
            return False
    return True


def _valid_optional_text(value: Any, max_length: int = MAX_LOCATION_TEXT_LENGTH) -> bool:
    return value is None or (isinstance(value, str) and len(value) <= max_length)


def _valid_location(location: Any) -> bool:
    if not isinstance(location, dict):
        return False
    for key in ("id", "landing_page_url", "pdf_url", "license", "version"):
        if not _valid_optional_text(location.get(key)):
            return False
    if location.get("is_oa") is not None and type(location.get("is_oa")) is not bool:
        return False
    source = location.get("source")
    if source is not None:
        if not isinstance(source, dict):
            return False
        for key, limit in (("id", 256), ("display_name", 512), ("type", 128)):
            if not _valid_optional_text(source.get(key), limit):
                return False
    return True


def _valid_open_access(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for key in ("is_oa", "any_repository_has_fulltext"):
        if value.get(key) is not None and type(value.get(key)) is not bool:
            return False
    if not _valid_optional_text(value.get("oa_status"), 64):
        return False
    return _valid_optional_text(value.get("oa_url"))


def _safe_https_url(value: Any) -> Tuple[Optional[str], bool]:
    if value is None:
        return None, False
    if not isinstance(value, str) or len(value) > MAX_LOCATION_TEXT_LENGTH:
        return None, True
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError:
        return None, True
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or any(ord(char) < 32 for char in value)
    ):
        return None, True
    return value, False


def _project_location(location: Optional[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
    if location is None:
        return None, 0
    landing_page_url, unsafe_landing = _safe_https_url(location.get("landing_page_url"))
    pdf_url, unsafe_pdf = _safe_https_url(location.get("pdf_url"))
    source = location.get("source")
    projected_source = None
    if isinstance(source, dict):
        projected_source = {
            "id": source.get("id"),
            "display_name": source.get("display_name"),
            "type": source.get("type"),
        }
    return {
        "id": location.get("id"),
        "is_oa": location.get("is_oa"),
        "landing_page_url": landing_page_url,
        "pdf_url": pdf_url,
        "source": projected_source,
        "license": location.get("license"),
        "version": location.get("version"),
    }, int(unsafe_landing) + int(unsafe_pdf)


def _project_open_access(value: Optional[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
    if value is None:
        return None, 0
    oa_url, unsafe_url = _safe_https_url(value.get("oa_url"))
    return {
        "is_oa": value.get("is_oa"),
        "oa_status": value.get("oa_status"),
        "oa_url": oa_url,
        "any_repository_has_fulltext": value.get("any_repository_has_fulltext"),
    }, int(unsafe_url)


def _parse_response(body: bytes) -> Dict[str, Any]:
    try:
        document = json.loads(
            body.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {"acquisition_status": "INVALID_JSON_RESPONSE", "results": [], "meta": {}}
    if not isinstance(document, dict) or not isinstance(document.get("results"), list) or not isinstance(document.get("meta"), dict):
        return {"acquisition_status": "INVALID_OPENALEX_RESPONSE", "results": [], "meta": {}}
    works = document["results"]
    if any(not isinstance(work, dict) or not _valid_work(work) for work in works):
        return {"acquisition_status": "INVALID_OPENALEX_WORK_RECORD", "results": [], "meta": {}}
    return {"acquisition_status": "OK", "results": works, "meta": document["meta"]}


def _meta_projection(meta: Dict[str, Any]) -> Dict[str, Any]:
    count = meta.get("count")
    if type(count) is not int or count < 0:
        count = None
    cost = meta.get("cost")
    if isinstance(cost, float) and not math.isfinite(cost):
        cost = None
    if not isinstance(cost, (int, float, str)) or isinstance(cost, bool) or (isinstance(cost, str) and len(cost) > 32):
        cost = None
    db_time = meta.get("db_response_time_ms")
    if type(db_time) not in (int, float) or (isinstance(db_time, float) and not math.isfinite(db_time)):
        db_time = None
    return {"count": count, "cost": cost, "db_response_time_ms": db_time}


def _project_row(doi: str, works: List[Dict[str, Any]], total_count: Optional[int]) -> Dict[str, Any]:
    exact = [work for work in works if _normalize_response_doi(work.get("doi")) == doi]
    if total_count is not None and total_count > MAX_RESULTS:
        return {"requested_doi": doi, "status": "RESULT_LIMIT_REACHED", "exact_primary_doi_match_count_seen": len(exact)}
    if len(exact) > 1:
        return {
            "requested_doi": doi,
            "status": "AMBIGUOUS_MULTIPLE_EXACT_MATCHES",
            "exact_primary_doi_match_count": len(exact),
            "candidate_work_ids": [work["id"] for work in exact],
        }
    if not exact:
        status = "NO_RESULT_FOR_FILTER" if total_count == 0 else "INCONCLUSIVE_NO_PRIMARY_DOI_MATCH"
        return {
            "requested_doi": doi,
            "status": status,
            "filter_result_count": total_count,
            "note": "A DOI filter hit can include a DOI recorded at a work location; no exact primary DOI match was selected.",
        }
    work = exact[0]
    raw_locations = work.get("locations")
    projected_locations: Optional[List[Dict[str, Any]]] = None
    unsafe_location_url_count = 0
    if isinstance(raw_locations, list):
        projected_locations = []
        for location in raw_locations[:MAX_LOCATIONS_PER_WORK]:
            projected, unsafe_count = _project_location(location)
            if projected is not None:
                projected_locations.append(projected)
            unsafe_location_url_count += unsafe_count
    best_oa_location, unsafe_best_url_count = _project_location(work.get("best_oa_location"))
    open_access, unsafe_oa_url_count = _project_open_access(work.get("open_access"))
    return {
        "requested_doi": doi,
        "status": "EXACT_PRIMARY_DOI_MATCH",
        "openalex_id": work["id"],
        "openalex_doi": work.get("doi"),
        "title": work.get("display_name"),
        "publication_year": work.get("publication_year"),
        "type": work.get("type"),
        "is_retracted": work.get("is_retracted"),
        "location_metadata_status": "PROVIDER_REPORTED" if isinstance(raw_locations, list) else "NOT_RETURNED",
        "openalex_locations_count": len(raw_locations) if isinstance(raw_locations, list) else None,
        "openalex_locations_returned_count": len(projected_locations) if projected_locations is not None else None,
        "openalex_locations_truncated": bool(
            isinstance(raw_locations, list) and len(raw_locations) > MAX_LOCATIONS_PER_WORK
        ),
        "openalex_locations": projected_locations,
        "openalex_best_oa_location": best_oa_location,
        "openalex_open_access": open_access,
        "omitted_unsafe_location_url_count": (
            unsafe_location_url_count + unsafe_best_url_count + unsafe_oa_url_count
        ),
    }


def lookup(dois: List[str]) -> Dict[str, Any]:
    fetched = _fetch(dois)
    body = fetched.get("body")
    response_sha256 = hashlib.sha256(body).hexdigest() if isinstance(body, bytes) else None
    rows: List[Dict[str, Any]]
    meta: Dict[str, Any] = {}
    if fetched["acquisition_status"] != "OK":
        rows = [{"requested_doi": doi, "status": fetched["acquisition_status"]} for doi in dois]
        status = "COMPLETED_WITH_EXPLICIT_FAILURES"
    else:
        parsed = _parse_response(body)
        if parsed["acquisition_status"] != "OK":
            rows = [{"requested_doi": doi, "status": parsed["acquisition_status"]} for doi in dois]
            status = "COMPLETED_WITH_EXPLICIT_FAILURES"
        else:
            meta = _meta_projection(parsed["meta"])
            rows = [_project_row(doi, parsed["results"], meta["count"]) for doi in dois]
            status = "EXACT_DOI_WORKS_RESOLVED" if all(row["status"] == "EXACT_PRIMARY_DOI_MATCH" for row in rows) else "COMPLETED_WITH_INCONCLUSIVE_ROWS"
    return {
        "schema_version": "ignition.openalex-work-metadata-lookup-r0",
        "tool_id": "research.lookup_openalex_work_metadata",
        "tool_version": TOOL_VERSION,
        "status": status,
        "doi_count": len(dois),
        "request_count": 1,
        "api_host": API_HOST,
        "api_path": "/works",
        "selected_fields": SELECT_FIELDS.split(","),
        "http_status": fetched["http_status"],
        "acquisition_status": fetched["acquisition_status"],
        "response_sha256": response_sha256,
        "api_usage": {"meta": meta, "rate_limit_headers": fetched.get("usage_headers", {})},
        "rows": rows,
        "claim_ceiling": CLAIM_CEILING,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read the bounded JSON contract from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="authorize this invocation to make one fixed-host public HTTPS GET")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        print("PUBLIC_NETWORK_CALL_REQUIRES --allow-public-network", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        dois = parse_request(raw)
    except ToolInputError as exc:
        print("INVALID_REQUEST: {}".format(exc), file=sys.stderr)
        return 2
    print(json.dumps(lookup(dois), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
