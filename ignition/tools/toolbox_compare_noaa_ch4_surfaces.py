#!/usr/bin/env python3
"""Compare NOAA GML's rendered CH4 growth table with its fixed raw table."""

from __future__ import annotations

import sys
import time
import urllib
from typing import Any

import toolbox_noaa_source_surface_comparison_core as _core


PROFILE = _core.CH4_PROFILE
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
CLAIM_CEILING = PROFILE.claim_ceiling
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
