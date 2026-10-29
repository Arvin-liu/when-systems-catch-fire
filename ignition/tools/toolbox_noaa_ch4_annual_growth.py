#!/usr/bin/env python3
"""Retrieve a bounded year range from NOAA GML's global annual CH4 growth table."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


TOOL_ID = "research.lookup_noaa_global_ch4_annual_growth"
TOOL_VERSION = "0.1.0"
SOURCE_URL = "https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_gr_gl.txt"
SOURCE_HOST = "gml.noaa.gov"
SOURCE_PATH = "/webdata/ccgg/trends/ch4/ch4_gr_gl.txt"
SOURCE_DEFINITION_MARKER = "annual ch4 mole fraction increase (ppb) from jan 1 through dec 31."
MAX_REQUEST_BYTES = 4096
MAX_RESPONSE_BYTES = 128 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 4096
MIN_YEAR = 1984
MAX_YEAR = 2100
MAX_RANGE_YEARS = 50
ROW_RE = re.compile(r"\s*(\d{4})\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\Z")
CLAIM_CEILING = (
    "Selected provider-reported NOAA GML global annual atmospheric methane mole-fraction increments and stated uncertainties only. "
    "The result is not an emissions estimate, source attribution, causal explanation, or scientific adjudication."
)


class ToolInputError(ValueError):
    """Raised when caller input is outside the declared bounded contract."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not follow a redirect away from the fixed NOAA source endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _strict_object(pairs: List[Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def parse_request(raw: bytes) -> Dict[str, int]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ToolInputError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON with unique keys") from exc
    if not isinstance(document, dict) or set(document) != {"start_year", "end_year"}:
        raise ToolInputError("request must contain exactly start_year and end_year")
    start, end = document["start_year"], document["end_year"]
    if type(start) is not int or type(end) is not int:
        raise ToolInputError("start_year and end_year must be JSON integers")
    if not MIN_YEAR <= start <= end <= MAX_YEAR:
        raise ToolInputError(f"year range must satisfy {MIN_YEAR} <= start_year <= end_year <= {MAX_YEAR}")
    if end - start + 1 > MAX_RANGE_YEARS:
        raise ToolInputError(f"requested range may contain no more than {MAX_RANGE_YEARS} years")
    return {"start_year": start, "end_year": end}


def _source_url() -> str:
    parsed = urllib.parse.urlsplit(SOURCE_URL)
    if (
        parsed.scheme != "https"
        or parsed.hostname != SOURCE_HOST
        or parsed.port is not None
        or parsed.username
        or parsed.password
        or parsed.path != SOURCE_PATH
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("NOAA source endpoint is not the declared fixed HTTPS host and path")
    return SOURCE_URL


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


def _bounded_header(response: Any, name: str) -> Optional[str]:
    value = response.headers.get(name)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if len(value) > 256 or "\r" in value or "\n" in value:
        return None
    return value or None


def _fetch() -> Dict[str, Any]:
    url = _source_url()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"IgnitionToolboxNOAACh4AnnualGrowth/{TOOL_VERSION}", "Accept": "text/plain"},
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {"acquisition_status": "HTTP_ERROR", "http_status": status, "body": None}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type != "text/plain":
                return {"acquisition_status": "NON_TEXT_RESPONSE", "http_status": status, "body": None}
            body, error = _read_bounded(response)
            if error:
                return {"acquisition_status": error, "http_status": status, "body": None}
            return {
                "acquisition_status": "OK",
                "http_status": status,
                "body": body,
                "etag": _bounded_header(response, "ETag"),
                "last_modified": _bounded_header(response, "Last-Modified"),
            }
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


def _parse_table(body: bytes, start_year: int, end_year: int) -> Dict[str, Any]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {"status": "INVALID_TEXT_RESPONSE", "records": []}
    lines = text.splitlines()
    if not any(SOURCE_DEFINITION_MARKER in line.casefold() for line in lines if line.lstrip().startswith("#")):
        return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
    if not any(re.match(r"^\s*#\s*year\s+ann\s+inc\s+unc\s*$", line, re.IGNORECASE) for line in lines):
        return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}

    all_rows: Dict[int, Dict[str, Any]] = {}
    previous_year: Optional[int] = None
    seen_data = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = ROW_RE.fullmatch(line)
        if not match:
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        seen_data = True
        year = int(match.group(1))
        if not MIN_YEAR <= year <= MAX_YEAR or year in all_rows or (previous_year is not None and year <= previous_year):
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        try:
            growth = Decimal(match.group(2))
            uncertainty = Decimal(match.group(3))
        except InvalidOperation:
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        if not growth.is_finite() or not uncertainty.is_finite() or uncertainty < 0:
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        all_rows[year] = {
            "year": year,
            "annual_increase_ppb": float(growth),
            "uncertainty_ppb": float(uncertainty),
        }
        previous_year = year
    if not seen_data:
        return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}

    selected = [all_rows[year] for year in range(start_year, end_year + 1) if year in all_rows]
    expected_count = end_year - start_year + 1
    if len(selected) == expected_count:
        status = "FOUND"
    elif selected:
        status = "PARTIAL_DATA"
    else:
        status = "NO_MATCH"
    return {"status": status, "records": selected}


def lookup(raw: bytes) -> Dict[str, Any]:
    request = parse_request(raw)
    request_url = _source_url()
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    fetched = _fetch()
    result: Dict[str, Any] = {
        "schema_version": "toolbox-noaa-ch4-annual-growth-lookup-r0",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": fetched["acquisition_status"],
        "requested_range": request,
        "request_url": request_url,
        "retrieved_at_utc": retrieved,
        "http_status": fetched["http_status"],
        "etag": fetched.get("etag"),
        "last_modified": fetched.get("last_modified"),
        "response_sha256": None,
        "response_bytes": None,
        "units": {"annual_increase": "ppb", "uncertainty": "ppb"},
        "records": [],
        "claim_ceiling": CLAIM_CEILING,
        "source_attribution": "NOAA Global Monitoring Laboratory, Trends in Atmospheric Methane, global annual increase table.",
        "source_caveats": [
            "The source says its latest year can change after reference-gas recalibration and quality-control procedures; earlier rows can also occasionally change.",
            "NOAA defines annual increase as the change in atmospheric mole fraction over the year; it sums methane added to and removed from the atmosphere by human and natural processes, so it is not an emissions inventory or source attribution.",
            "Provider-reported values and uncertainty are returned without independent scientific validation.",
        ],
        "non_claims": [
            "The lookup does not estimate emissions, attribute changes to a source, explain causes, or establish a scientific conclusion.",
            "The response digest binds received bytes but does not independently authenticate NOAA or certify the data.",
            "The source table may be revised; this result is only the captured response at retrieved_at_utc.",
        ],
        "tool_source_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
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
    parsed = _parse_table(body, request["start_year"], request["end_year"])
    result["status"] = parsed["status"]
    result["records"] = parsed["records"]
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Retrieve a bounded year range from NOAA GML annual atmospheric CH4 growth data.")
    parser.add_argument("--stdin", action="store_true", required=True, help="read a UTF-8 JSON request from stdin")
    parser.add_argument("--allow-public-network", action="store_true", help="explicitly allow one public NOAA GML HTTPS GET")
    args = parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    try:
        parse_request(raw)
    except ToolInputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not args.allow_public_network:
        print("public NOAA GML data lookup requires --allow-public-network for this invocation", file=sys.stderr)
        return 2
    print(json.dumps(lookup(raw), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
