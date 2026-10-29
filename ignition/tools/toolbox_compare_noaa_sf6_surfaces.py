#!/usr/bin/env python3
"""Compare NOAA GML's rendered SF6 growth page with its fixed raw table."""

from __future__ import annotations

import sys
import time
import urllib
from typing import Any

import toolbox_noaa_source_surface_comparison_core as _core


CLAIM_CEILING = (
    "Exact selected annual atmospheric SF6 mole-fraction increases and stated "
    "uncertainties from two NOAA GML surfaces at retrieval time, plus their "
    "arithmetic differences. This does not authenticate NOAA, rank the "
    "surfaces, validate measurements, estimate emissions, attribute sources, "
    "explain causes, or establish a scientific conclusion."
)
PROFILE = _core.SourceProfile(
    tool_id="research.compare_noaa_sf6_source_surfaces",
    tool_version="0.1.0",
    input_schema_version="toolbox-noaa-sf6-source-surface-comparison-input-r0",
    output_schema_version="toolbox-noaa-sf6-source-surface-comparison-output-r0",
    page_url="https://gml.noaa.gov/ccgg/trends_sf6/",
    page_path="/ccgg/trends_sf6/",
    raw_url="https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_gr_gl.txt",
    raw_path="/webdata/ccgg/trends/sf6/sf6_gr_gl.txt",
    source_host="gml.noaa.gov",
    source_definition_marker=(
        "annual sf6 mole fraction increase (ppt) from jan 1 through dec 31."
    ),
    page_heading_marker=(
        "annual increase in globally-averaged atmospheric sulfur hexafluoride"
    ),
    unit="ppt",
    annual_field="annual_increase_ppt",
    uncertainty_field="uncertainty_ppt",
    min_year=1998,
    max_year=2100,
    claim_ceiling=CLAIM_CEILING,
)

TOOL_ID = PROFILE.tool_id
TOOL_VERSION = PROFILE.tool_version
INPUT_SCHEMA_VERSION = PROFILE.input_schema_version
OUTPUT_SCHEMA_VERSION = PROFILE.output_schema_version
PAGE_URL = PROFILE.page_url
PAGE_PATH = PROFILE.page_path
RAW_URL = PROFILE.raw_url
RAW_PATH = PROFILE.raw_path
SOURCE_HOST = PROFILE.source_host
SOURCE_DEFINITION_MARKER = PROFILE.source_definition_marker
PAGE_HEADING_MARKER = PROFILE.page_heading_marker
MAX_INPUT_BYTES = _core.MAX_INPUT_BYTES
MAX_RESPONSE_BYTES = _core.MAX_RESPONSE_BYTES
MAX_RESPONSE_DURATION_SECONDS = _core.MAX_RESPONSE_DURATION_SECONDS
REQUEST_TIMEOUT_SECONDS = _core.REQUEST_TIMEOUT_SECONDS
RESPONSE_CHUNK_BYTES = _core.RESPONSE_CHUNK_BYTES
MIN_YEAR = PROFILE.min_year
MAX_YEAR = PROFILE.max_year
MAX_RANGE_YEARS = _core.MAX_RANGE_YEARS
DECIMAL_RE = _core.DECIMAL_RE
ROW_RE = _core.ROW_RE
NON_CLAIMS = _core.NON_CLAIMS
ToolInputError = _core.ToolInputError
_NoRedirectHandler = _core._NoRedirectHandler
_AnnualGrowthHtmlParser = _core._AnnualGrowthHtmlParser
_bounded_header = _core._bounded_header
_read_bounded = _core._read_bounded
_decimal = _core._decimal
_selected_status = _core._selected_status
_source_receipt = _core._source_receipt


def parse_request(raw: bytes) -> dict[str, int]:
    return _core.parse_request(raw, PROFILE)


def _validate_fixed_url(url: str, expected_path: str) -> None:
    _core._validate_fixed_url(url, expected_path, PROFILE)


def _fetch(url: str, expected_path: str, expected_content_type: str) -> dict[str, Any]:
    return _core._fetch(url, expected_path, expected_content_type, PROFILE)


def _parse_page(body: bytes, start_year: int, end_year: int) -> dict[str, Any]:
    return _core._parse_page(body, start_year, end_year, PROFILE)


def _parse_raw_table(body: bytes, start_year: int, end_year: int) -> dict[str, Any]:
    return _core._parse_raw_table(body, start_year, end_year, PROFILE)


def _compare(
    page_records: list[dict[str, Any]],
    raw_records: list[dict[str, Any]],
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    return _core._compare(page_records, raw_records, start_year, end_year, PROFILE)


def lookup(raw: bytes) -> dict[str, Any]:
    return _core.lookup(raw, PROFILE)


def main(argv: list[str] | None = None) -> int:
    return _core.main(argv, PROFILE)


if __name__ == "__main__":
    raise SystemExit(main())
