#!/usr/bin/env python3
"""Retrieve a bounded year range from NOAA GML's fixed raw SF6 growth table."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import toolbox_noaa_source_surface_comparison_core as _core


TOOL_ID = "research.lookup_noaa_global_sf6_annual_growth"
TOOL_VERSION = "0.1.0"
INPUT_SCHEMA_VERSION = "toolbox-noaa-sf6-annual-growth-lookup-input-r0"
OUTPUT_SCHEMA_VERSION = "toolbox-noaa-sf6-annual-growth-lookup-output-r0"
CLAIM_CEILING = (
    "Provider-reported NOAA GML global annual atmospheric SF6 mole-fraction "
    "increases and raw-table uncertainty values for selected years only. This "
    "is not an emissions estimate, source attribution, causal explanation, "
    "source authentication, independent validation, or scientific conclusion."
)
PROFILE = replace(
    _core.N2O_PROFILE,
    tool_id=TOOL_ID,
    tool_version=TOOL_VERSION,
    input_schema_version=INPUT_SCHEMA_VERSION,
    output_schema_version=OUTPUT_SCHEMA_VERSION,
    page_url="https://gml.noaa.gov/ccgg/trends_sf6/",
    page_path="/ccgg/trends_sf6/",
    raw_url="https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_gr_gl.txt",
    raw_path="/webdata/ccgg/trends/sf6/sf6_gr_gl.txt",
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
    claim_ceiling=CLAIM_CEILING,
)

MAX_INPUT_BYTES = _core.MAX_INPUT_BYTES
MAX_RESPONSE_BYTES = _core.MAX_RESPONSE_BYTES
_NoRedirectHandler = _core._NoRedirectHandler
ToolInputError = _core.ToolInputError


def parse_request(raw: bytes) -> dict[str, int]:
    return _core.parse_request(raw, PROFILE)


def lookup(raw: bytes) -> dict[str, Any]:
    request = parse_request(raw)
    capture = _core._fetch(
        PROFILE.raw_url,
        PROFILE.raw_path,
        "text/plain",
        PROFILE,
    )
    if capture.get("acquisition_status") == "OK" and isinstance(capture.get("body"), bytes):
        parsed = _core._parse_raw_table(
            capture["body"], request["start_year"], request["end_year"], PROFILE
        )
    else:
        parsed = {"status": "NOT_RUN", "records": []}
    receipt = _core._source_receipt(PROFILE.raw_url, capture, parsed)

    if capture.get("acquisition_status") != "OK":
        status = "SOURCE_UNAVAILABLE"
    else:
        status = parsed["status"]

    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": status,
        "requested_range": request,
        "units": {"annual_increase": "ppt", "uncertainty": "ppt"},
        "source": receipt,
        "source_attribution": "NOAA Global Monitoring Laboratory, fixed raw global annual sulfur-hexafluoride increase table.",
        "source_caveats": [
            "NOAA may revise recent and earlier annual values as additional samples and quality-control updates enter the analysis.",
            "The raw table reports uncertainty to two decimal places; a reported 0.00 is rounded precision and must not be interpreted as zero uncertainty.",
            "Annual atmospheric mole-fraction growth is a net atmospheric change, not an emissions inventory or source attribution.",
            "Provider-reported values and uncertainties are returned without independent scientific validation.",
        ],
        "non_claims": [
            "The response digest binds received bytes but does not independently authenticate NOAA or certify the data.",
            "The lookup does not estimate SF6 emissions, identify sectors, attribute changes, explain causes, or establish a scientific conclusion.",
            "A missing year is not zero and does not prove that no measurement exists.",
        ],
        "claim_ceiling": CLAIM_CEILING,
        "tool_source_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
        "request_sha256": hashlib.sha256(raw).hexdigest(),
        "invocation": {
            "allow_public_network_flag": True,
            "requests_made": 1,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Retrieve a bounded range from NOAA GML's fixed raw global annual SF6 growth table."
    )
    parser.add_argument("--stdin", action="store_true", required=True)
    parser.add_argument("--allow-public-network", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_public_network:
        print("NETWORK_CALL_REQUIRES_ALLOW_PUBLIC_NETWORK", file=sys.stderr)
        return 2

    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        parse_request(raw)
        result = lookup(raw)
    except ToolInputError as exc:
        print("INPUT_ERROR: " + str(exc), file=sys.stderr)
        return 2
    output = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if len(output.encode("utf-8")) > MAX_RESPONSE_BYTES:
        print("OUTPUT_TOO_LARGE", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
