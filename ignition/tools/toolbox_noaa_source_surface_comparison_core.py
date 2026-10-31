#!/usr/bin/env python3
"""Compare NOAA GML's rendered CO2 growth table with its fixed raw table."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


TOOL_ID = "research.compare_noaa_co2_source_surfaces"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "toolbox-noaa-co2-source-surface-comparison-input-r0"
OUTPUT_SCHEMA_VERSION = "toolbox-noaa-co2-source-surface-comparison-output-r0"
PAGE_URL = "https://gml.noaa.gov/ccgg/trends/gl_gr.html"
PAGE_PATH = "/ccgg/trends/gl_gr.html"
RAW_URL = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.txt"
RAW_PATH = "/webdata/ccgg/trends/co2/co2_gr_gl.txt"
SOURCE_HOST = "gml.noaa.gov"
SOURCE_DEFINITION_MARKER = (
    "annual co2 mole fraction increase (ppm) from jan 1 through dec 31."
)
PAGE_HEADING_MARKER = "annual mean global carbon dioxide growth rates"
MAX_INPUT_BYTES = 4096
MAX_RESPONSE_BYTES = 256 * 1024
MAX_RESPONSE_DURATION_SECONDS = 7
REQUEST_TIMEOUT_SECONDS = 5
RESPONSE_CHUNK_BYTES = 4096
MIN_YEAR = 1959
MAX_YEAR = 2100
MAX_RANGE_YEARS = 50
DECIMAL_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
ROW_RE = re.compile(
    r"\s*(\d{4})\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
    r"\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\Z"
)
CLAIM_CEILING = (
    "Exact selected values and stated uncertainties from two NOAA GML CO2 source "
    "surfaces at retrieval time, plus their arithmetic differences. This result "
    "does not authenticate the source, rank the surfaces, establish why a "
    "difference exists, validate the measurements, estimate emissions, attribute "
    "sources, explain causes, or establish a scientific conclusion."
)
NON_CLAIMS = [
    "A response digest binds the received bytes but does not independently authenticate NOAA.",
    "The comparison reports literal numeric differences and does not judge rounding, statistical significance, or which surface is correct.",
    "The raw response bodies are not retained; the result is not a reproducible archive or independent scientific validation.",
    "Annual atmospheric growth values are not an emissions inventory, source attribution, or causal explanation.",
]


@dataclass(frozen=True)
class SourceProfile:
    tool_id: str
    tool_version: str
    input_schema_version: str
    output_schema_version: str
    page_url: str
    page_path: str
    raw_url: str
    raw_path: str
    source_host: str
    source_definition_marker: str
    page_heading_marker: str
    unit: str
    annual_field: str
    uncertainty_field: str
    min_year: int
    max_year: int
    claim_ceiling: str


CO2_PROFILE = SourceProfile(
    tool_id=TOOL_ID,
    tool_version=TOOL_VERSION,
    input_schema_version=INPUT_SCHEMA_VERSION,
    output_schema_version=OUTPUT_SCHEMA_VERSION,
    page_url=PAGE_URL,
    page_path=PAGE_PATH,
    raw_url=RAW_URL,
    raw_path=RAW_PATH,
    source_host=SOURCE_HOST,
    source_definition_marker=SOURCE_DEFINITION_MARKER,
    page_heading_marker=PAGE_HEADING_MARKER,
    unit="ppm",
    annual_field="annual_increase_ppm",
    uncertainty_field="uncertainty_ppm",
    min_year=1959,
    max_year=2100,
    claim_ceiling=CLAIM_CEILING,
)
CH4_PROFILE = SourceProfile(
    tool_id="research.compare_noaa_ch4_source_surfaces",
    tool_version="0.1.0",
    input_schema_version="toolbox-noaa-ch4-source-surface-comparison-input-r0",
    output_schema_version="toolbox-noaa-ch4-source-surface-comparison-output-r0",
    page_url="https://gml.noaa.gov/ccgg/trends_ch4/",
    page_path="/ccgg/trends_ch4/",
    raw_url="https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_gr_gl.txt",
    raw_path="/webdata/ccgg/trends/ch4/ch4_gr_gl.txt",
    source_host=SOURCE_HOST,
    source_definition_marker=(
        "annual ch4 mole fraction increase (ppb) from jan 1 through dec 31."
    ),
    page_heading_marker=(
        "annual increase in globally-averaged atmospheric methane"
    ),
    unit="ppb",
    annual_field="annual_increase_ppb",
    uncertainty_field="uncertainty_ppb",
    min_year=1984,
    max_year=2100,
    claim_ceiling=(
        "Exact selected annual methane mole-fraction increments and stated "
        "uncertainties from two NOAA GML surfaces at retrieval time, plus their "
        "arithmetic differences. This does not authenticate NOAA, rank the "
        "surfaces, validate measurements, estimate emissions, attribute sources, "
        "explain causes, or establish a scientific conclusion."
    ),
)
N2O_PROFILE = SourceProfile(
    tool_id="research.compare_noaa_n2o_source_surfaces",
    tool_version="0.1.0",
    input_schema_version="toolbox-noaa-n2o-source-surface-comparison-input-r0",
    output_schema_version="toolbox-noaa-n2o-source-surface-comparison-output-r0",
    page_url="https://gml.noaa.gov/ccgg/trends_n2o/",
    page_path="/ccgg/trends_n2o/",
    raw_url="https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_gr_gl.txt",
    raw_path="/webdata/ccgg/trends/n2o/n2o_gr_gl.txt",
    source_host=SOURCE_HOST,
    source_definition_marker=(
        "annual n2o mole fraction increase (ppb) from jan 1 through dec 31."
    ),
    page_heading_marker=(
        "annual increase in globally-averaged atmospheric nitrous oxide"
    ),
    unit="ppb",
    annual_field="annual_increase_ppb",
    uncertainty_field="uncertainty_ppb",
    min_year=2001,
    max_year=2100,
    claim_ceiling=(
        "Exact selected annual atmospheric N2O mole-fraction increases and stated "
        "uncertainties from two NOAA GML surfaces at retrieval time, plus their "
        "arithmetic differences. This does not authenticate NOAA, rank the "
        "surfaces, validate measurements, estimate N2O emissions, attribute "
        "sources, explain causes, or establish a scientific conclusion."
    ),
)


class ToolInputError(ValueError):
    """Raised when the bounded year-range request is malformed."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolInputError("duplicate JSON object key")
        result[key] = value
    return result


def parse_request(raw: bytes, profile: SourceProfile = CO2_PROFILE) -> dict[str, int]:
    if len(raw) > MAX_INPUT_BYTES:
        raise ToolInputError(f"request exceeds {MAX_INPUT_BYTES} bytes")
    try:
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ToolInputError("non-standard JSON number is not allowed")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolInputError("request must be valid UTF-8 JSON with unique keys") from exc
    if not isinstance(document, dict) or set(document) != {
        "schema_version", "start_year", "end_year"
    }:
        raise ToolInputError("request must contain exactly schema_version, start_year, and end_year")
    if document["schema_version"] != profile.input_schema_version:
        raise ToolInputError("unsupported schema_version")
    start, end = document["start_year"], document["end_year"]
    if type(start) is not int or type(end) is not int:
        raise ToolInputError("start_year and end_year must be JSON integers")
    if not profile.min_year <= start <= end <= profile.max_year:
        raise ToolInputError(
            f"year range must satisfy {profile.min_year} <= start_year <= end_year <= {profile.max_year}"
        )
    if end - start + 1 > MAX_RANGE_YEARS:
        raise ToolInputError(f"requested range may contain no more than {MAX_RANGE_YEARS} years")
    return {"start_year": start, "end_year": end}


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not follow redirects away from the two fixed NOAA endpoints."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _validate_fixed_url(
    url: str, expected_path: str, profile: SourceProfile = CO2_PROFILE
) -> None:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != profile.source_host
        or parsed.port is not None
        or parsed.username
        or parsed.password
        or parsed.path != expected_path
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("NOAA source URL is not the declared fixed HTTPS endpoint")


def _bounded_header(response: Any, name: str) -> str | None:
    value = response.headers.get(name)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if len(value) > 256 or "\r" in value or "\n" in value:
        return None
    return value or None


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


def _fetch(
    url: str,
    expected_path: str,
    expected_content_type: str,
    profile: SourceProfile = CO2_PROFILE,
) -> dict[str, Any]:
    _validate_fixed_url(url, expected_path, profile)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"IgnitionToolboxNoaaSurfaceComparator/{profile.tool_version}",
            "Accept": expected_content_type,
        },
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            if status != 200:
                return {
                    "acquisition_status": "HTTP_ERROR",
                    "http_status": status,
                    "body": None,
                    "retrieved_at_utc": retrieved_at,
                }
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
            if content_type != expected_content_type:
                return {
                    "acquisition_status": "NON_TEXT_RESPONSE",
                    "http_status": status,
                    "body": None,
                    "retrieved_at_utc": retrieved_at,
                }
            body, error = _read_bounded(response)
            if error:
                return {
                    "acquisition_status": error,
                    "http_status": status,
                    "body": None,
                    "retrieved_at_utc": retrieved_at,
                }
            return {
                "acquisition_status": "OK",
                "http_status": status,
                "body": body,
                "etag": _bounded_header(response, "ETag"),
                "last_modified": _bounded_header(response, "Last-Modified"),
                "retrieved_at_utc": retrieved_at,
            }
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        if 300 <= status < 400:
            outcome = "REDIRECT_BLOCKED"
        elif status == 429:
            outcome = "RATE_LIMITED"
        else:
            outcome = "HTTP_ERROR"
        return {
            "acquisition_status": outcome,
            "http_status": status,
            "body": None,
            "retrieved_at_utc": retrieved_at,
        }
    except (urllib.error.URLError, TimeoutError, OSError):
        return {
            "acquisition_status": "NETWORK_ERROR",
            "http_status": None,
            "body": None,
            "retrieved_at_utc": retrieved_at,
        }


class _AnnualGrowthHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.text_parts: list[str] = []
        self._in_table = False
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and not self._in_table:
            self._in_table = True
            self._table = []
        elif self._in_table and tag == "tr":
            self._row = []
        elif self._in_table and self._row is not None and tag in {"td", "th"}:
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._in_table and tag in {"td", "th"} and self._cell_parts is not None:
            assert self._row is not None
            self._row.append(" ".join(" ".join(self._cell_parts).split()))
            self._cell_parts = None
        elif self._in_table and tag == "tr" and self._row is not None:
            assert self._table is not None
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._in_table:
            assert self._table is not None
            self.tables.append(self._table)
            self._table = None
            self._in_table = False


def _decimal(value: str, where: str) -> Decimal:
    if not DECIMAL_RE.fullmatch(value):
        raise ValueError(where)
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(where) from exc
    if not result.is_finite():
        raise ValueError(where)
    return result


def _selected_status(records: list[dict[str, Any]], start: int, end: int) -> str:
    if not records:
        return "NO_MATCH"
    if len(records) == end - start + 1:
        return "FOUND"
    return "PARTIAL_DATA"


def _parse_page(
    body: bytes,
    start_year: int,
    end_year: int,
    profile: SourceProfile = CO2_PROFILE,
) -> dict[str, Any]:
    try:
        decoded = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {"status": "INVALID_TEXT_RESPONSE", "records": []}
    parser = _AnnualGrowthHtmlParser()
    try:
        parser.feed(decoded)
        parser.close()
    except Exception:
        return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}

    text = " ".join(" ".join(parser.text_parts).split()).casefold()
    if profile.page_heading_marker not in text:
        return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
    expected_header = [
        "year", f"growth ({profile.unit})", f"uncertainty ({profile.unit})"
    ]
    candidates = [
        table for table in parser.tables
        if any([cell.casefold() for cell in row] == expected_header for row in table)
    ]
    if len(candidates) != 1:
        return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}

    table = candidates[0]
    header_index = next(
        index for index, row in enumerate(table)
        if [cell.casefold() for cell in row] == expected_header
    )
    all_records: list[dict[str, Any]] = []
    previous_year: int | None = None
    seen_years: set[int] = set()
    for row in table[header_index + 1:]:
        if not row or all(not cell for cell in row):
            continue
        if len(row) != 3 or not re.fullmatch(r"\d{4}", row[0]):
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        year = int(row[0])
        if not profile.min_year <= year <= profile.max_year or year in seen_years or (
            previous_year is not None and year <= previous_year
        ):
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        try:
            growth = _decimal(row[1], "annual growth")
            uncertainty = _decimal(row[2], "uncertainty")
        except ValueError:
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        if uncertainty < 0:
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        all_records.append({
            "year": year,
            profile.annual_field: format(growth, "f"),
            profile.uncertainty_field: format(uncertainty, "f"),
        })
        seen_years.add(year)
        previous_year = year
    records = [
        row for row in all_records
        if start_year <= row["year"] <= end_year
    ]
    return {"status": _selected_status(records, start_year, end_year), "records": records}


def _parse_raw_table(
    body: bytes,
    start_year: int,
    end_year: int,
    profile: SourceProfile = CO2_PROFILE,
) -> dict[str, Any]:
    try:
        decoded = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {"status": "INVALID_TEXT_RESPONSE", "records": []}
    lines = decoded.splitlines()
    if not any(
        profile.source_definition_marker in line.casefold()
        for line in lines if line.lstrip().startswith("#")
    ):
        return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
    if not any(
        re.match(r"^\s*#\s*year\s+ann\s+inc\s+unc\s*$", line, re.IGNORECASE)
        for line in lines
    ):
        return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
    all_records: list[dict[str, Any]] = []
    previous_year: int | None = None
    seen_years: set[int] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = ROW_RE.fullmatch(line)
        if not match:
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        year = int(match.group(1))
        if not profile.min_year <= year <= profile.max_year or year in seen_years or (
            previous_year is not None and year <= previous_year
        ):
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        try:
            growth = _decimal(match.group(2), "annual growth")
            uncertainty = _decimal(match.group(3), "uncertainty")
        except ValueError:
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        if uncertainty < 0:
            return {"status": "INVALID_PROVIDER_RESPONSE", "records": []}
        all_records.append({
            "year": year,
            profile.annual_field: format(growth, "f"),
            profile.uncertainty_field: format(uncertainty, "f"),
        })
        seen_years.add(year)
        previous_year = year
    records = [
        row for row in all_records
        if start_year <= row["year"] <= end_year
    ]
    return {"status": _selected_status(records, start_year, end_year), "records": records}


def _source_receipt(url: str, capture: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    body = capture.get("body")
    return {
        "url": url,
        "acquisition_status": capture.get("acquisition_status", "UNKNOWN"),
        "parse_status": parsed.get("status", "NOT_RUN"),
        "http_status": capture.get("http_status"),
        "etag": capture.get("etag"),
        "last_modified": capture.get("last_modified"),
        "retrieved_at_utc": capture.get("retrieved_at_utc"),
        "response_bytes": len(body) if isinstance(body, bytes) else None,
        "response_sha256": hashlib.sha256(body).hexdigest() if isinstance(body, bytes) else None,
        "records": parsed.get("records", []),
        "raw_response_retained": False,
    }


def _compare(
    page_records: list[dict[str, Any]],
    raw_records: list[dict[str, Any]],
    start_year: int,
    end_year: int,
    profile: SourceProfile = CO2_PROFILE,
) -> dict[str, Any]:
    page_by_year = {row["year"]: row for row in page_records}
    raw_by_year = {row["year"]: row for row in raw_records}
    rows: list[dict[str, Any]] = []
    for year in range(start_year, end_year + 1):
        page = page_by_year.get(year)
        raw = raw_by_year.get(year)
        if page is None and raw is None:
            rows.append({"year": year, "status": "MISSING_FROM_BOTH"})
            continue
        if page is None:
            rows.append({
                "year": year,
                "status": "MISSING_FROM_PAGE",
                "raw_table": raw,
            })
            continue
        if raw is None:
            rows.append({
                "year": year,
                "status": "MISSING_FROM_RAW_TABLE",
                "page": page,
            })
            continue
        page_growth = Decimal(page[profile.annual_field])
        raw_growth = Decimal(raw[profile.annual_field])
        page_uncertainty = Decimal(page[profile.uncertainty_field])
        raw_uncertainty = Decimal(raw[profile.uncertainty_field])
        growth_difference = page_growth - raw_growth
        uncertainty_difference = page_uncertainty - raw_uncertainty
        equal = growth_difference == 0 and uncertainty_difference == 0
        rows.append({
            "year": year,
            "status": "EXACT_MATCH" if equal else "NUMERIC_DIFFERENCE",
            f"page_{profile.annual_field}": page[profile.annual_field],
            f"raw_table_{profile.annual_field}": raw[profile.annual_field],
            f"page_minus_raw_{profile.annual_field}": format(growth_difference, "f"),
            f"page_{profile.uncertainty_field}": page[profile.uncertainty_field],
            f"raw_table_{profile.uncertainty_field}": raw[profile.uncertainty_field],
            f"page_minus_raw_{profile.uncertainty_field}": format(uncertainty_difference, "f"),
        })
    if any(row["status"] == "NUMERIC_DIFFERENCE" for row in rows):
        status = "DIFFERENT"
    elif any(row["status"] != "EXACT_MATCH" for row in rows):
        status = "PARTIAL"
    else:
        status = "EXACT_MATCH"
    return {
        "status": status,
        "requested_year_count": end_year - start_year + 1,
        "exact_match_count": sum(row["status"] == "EXACT_MATCH" for row in rows),
        "numeric_difference_count": sum(row["status"] == "NUMERIC_DIFFERENCE" for row in rows),
        "missing_year_count": sum(row["status"].startswith("MISSING_") for row in rows),
        "rows": rows,
    }


def lookup(raw: bytes, profile: SourceProfile = CO2_PROFILE) -> dict[str, Any]:
    request = parse_request(raw, profile)
    page_capture = _fetch(
        profile.page_url, profile.page_path, "text/html", profile
    )
    raw_capture = _fetch(profile.raw_url, profile.raw_path, "text/plain", profile)
    page_parsed = (
        _parse_page(
            page_capture["body"], request["start_year"], request["end_year"], profile
        )
        if page_capture.get("acquisition_status") == "OK"
        else {"status": "NOT_RUN", "records": []}
    )
    raw_parsed = (
        _parse_raw_table(
            raw_capture["body"], request["start_year"], request["end_year"], profile
        )
        if raw_capture.get("acquisition_status") == "OK"
        else {"status": "NOT_RUN", "records": []}
    )
    page_receipt = _source_receipt(profile.page_url, page_capture, page_parsed)
    raw_receipt = _source_receipt(profile.raw_url, raw_capture, raw_parsed)
    if page_parsed["status"] in {"FOUND", "PARTIAL_DATA", "NO_MATCH"} and raw_parsed["status"] in {
        "FOUND", "PARTIAL_DATA", "NO_MATCH"
    }:
        comparison = _compare(
            page_parsed["records"], raw_parsed["records"],
            request["start_year"], request["end_year"],
            profile,
        )
    else:
        comparison = {
            "status": "NOT_COMPARED",
            "requested_year_count": request["end_year"] - request["start_year"] + 1,
            "exact_match_count": 0,
            "numeric_difference_count": 0,
            "missing_year_count": 0,
            "rows": [],
        }
    source_ok = (
        page_capture.get("acquisition_status") == "OK"
        and raw_capture.get("acquisition_status") == "OK"
        and page_parsed["status"] in {"FOUND", "PARTIAL_DATA", "NO_MATCH"}
        and raw_parsed["status"] in {"FOUND", "PARTIAL_DATA", "NO_MATCH"}
    )
    overall_status = (
        "COMPARED" if source_ok and comparison["status"] in {"EXACT_MATCH", "DIFFERENT", "PARTIAL"}
        else "SOURCE_UNAVAILABLE"
    )
    return {
        "schema_version": profile.output_schema_version,
        "tool_id": profile.tool_id,
        "tool_version": profile.tool_version,
        "status": overall_status,
        "requested_range": request,
        "sources": {
            "provider_page": page_receipt,
            "fixed_raw_table": raw_receipt,
        },
        "comparison": comparison,
        "claim_ceiling": profile.claim_ceiling,
        "non_claims": NON_CLAIMS,
    }


def main(argv: list[str] | None = None, profile: SourceProfile = CO2_PROFILE) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdin", action="store_true", required=True)
    parser.add_argument("--allow-public-network", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        print("NETWORK_CALL_REQUIRES_ALLOW_PUBLIC_NETWORK", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = lookup(raw, profile)
    except ToolInputError as exc:
        print("INPUT_ERROR: " + str(exc), file=sys.stderr)
        return 2
    result["invocation"] = {
        "allow_public_network_flag": True,
        "requests_made": 2,
    }
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(output.encode("utf-8")) > MAX_RESPONSE_BYTES:
        print("OUTPUT_TOO_LARGE", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
