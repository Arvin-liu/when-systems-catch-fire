#!/usr/bin/env python3
"""Pair captured NOAA CO2 and CH4 source-surface comparisons by year, offline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import re
import sys
from typing import Any, Optional


TOOL_ID = "research.pair_noaa_co2_ch4_growth_by_year"
TOOL_VERSION = "0.3.0"
LEGACY_INPUT_SCHEMA_VERSION = "toolbox-noaa-co2-ch4-growth-pair-input-r0"
INPUT_SCHEMA_R1_VERSION = "toolbox-noaa-co2-ch4-growth-pair-input-r1"
INPUT_SCHEMA_VERSION = "toolbox-noaa-co2-ch4-growth-pair-input-r2"
OUTPUT_SCHEMA_VERSION = "toolbox-noaa-co2-ch4-growth-pair-output-r2"
MAX_INPUT_BYTES = 256 * 1024
MAX_RANGE_YEARS = 50
DECIMAL_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
YEAR_STATUSES = {
    "EXACT_MATCH",
    "NUMERIC_DIFFERENCE",
    "MISSING_FROM_PAGE",
    "MISSING_FROM_RAW_TABLE",
    "MISSING_FROM_BOTH",
}
COMPARISON_STATUSES = {"NOT_COMPARED", "EXACT_MATCH", "DIFFERENT", "PARTIAL"}
SOURCE_STATUSES = {
    "OK",
    "HTTP_ERROR",
    "REDIRECT_BLOCKED",
    "RATE_LIMITED",
    "NON_TEXT_RESPONSE",
    "RESPONSE_TIMEOUT",
    "RESPONSE_TOO_LARGE",
    "NETWORK_ERROR",
}
PARSE_STATUSES = {
    "FOUND",
    "PARTIAL_DATA",
    "NO_MATCH",
    "NOT_RUN",
    "INVALID_TEXT_RESPONSE",
    "INVALID_PROVIDER_RESPONSE",
}
SOURCE_URLS = {
    "co2": {
        "provider_page": "https://gml.noaa.gov/ccgg/trends/gl_gr.html",
        "fixed_raw_table": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_gr_gl.txt",
    },
    "ch4": {
        "provider_page": "https://gml.noaa.gov/ccgg/trends_ch4/",
        "fixed_raw_table": "https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_gr_gl.txt",
    },
    "n2o": {
        "provider_page": "https://gml.noaa.gov/ccgg/trends_n2o/",
        "fixed_raw_table": "https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_gr_gl.txt",
    },
}
UNIT_FIELDS = {
    "co2": {
        "annual": "annual_increase_ppm",
        "uncertainty": "uncertainty_ppm",
        "row_fields": {
            "page_annual_increase_ppm",
            "raw_table_annual_increase_ppm",
            "page_minus_raw_annual_increase_ppm",
            "page_uncertainty_ppm",
            "raw_table_uncertainty_ppm",
            "page_minus_raw_uncertainty_ppm",
        },
        "min_year": 1959,
        "tool_id": "research.compare_noaa_co2_source_surfaces",
        "input_schema_version": "toolbox-noaa-co2-source-surface-comparison-output-r0",
    },
    "ch4": {
        "annual": "annual_increase_ppb",
        "uncertainty": "uncertainty_ppb",
        "row_fields": {
            "page_annual_increase_ppb",
            "raw_table_annual_increase_ppb",
            "page_minus_raw_annual_increase_ppb",
            "page_uncertainty_ppb",
            "raw_table_uncertainty_ppb",
            "page_minus_raw_uncertainty_ppb",
        },
        "min_year": 1984,
        "tool_id": "research.compare_noaa_ch4_source_surfaces",
        "input_schema_version": "toolbox-noaa-ch4-source-surface-comparison-output-r0",
    },
    "n2o": {
        "annual": "annual_increase_ppb",
        "uncertainty": "uncertainty_ppb",
        "row_fields": {
            "page_annual_increase_ppb",
            "raw_table_annual_increase_ppb",
            "page_minus_raw_annual_increase_ppb",
            "page_uncertainty_ppb",
            "raw_table_uncertainty_ppb",
            "page_minus_raw_uncertainty_ppb",
        },
        "min_year": 2001,
        "tool_id": "research.compare_noaa_n2o_source_surfaces",
        "input_schema_version": "toolbox-noaa-n2o-source-surface-comparison-output-r0",
    },
    "sf6": {
        "annual": "annual_increase_ppt",
        "uncertainty": "uncertainty_ppt",
        "row_fields": {
            "page_annual_increase_ppt",
            "raw_table_annual_increase_ppt",
            "page_minus_raw_annual_increase_ppt",
            "page_uncertainty_ppt",
            "raw_table_uncertainty_ppt",
            "page_minus_raw_uncertainty_ppt",
        },
        "min_year": 1998,
        "tool_id": "research.compare_noaa_sf6_source_surfaces",
        "input_schema_version": "toolbox-noaa-sf6-source-surface-comparison-output-r0",
    },
}
SOURCE_URLS["sf6"] = {
    "provider_page": "https://gml.noaa.gov/ccgg/trends_sf6/",
    "fixed_raw_table": "https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_gr_gl.txt",
}
OUTPUT_ROW_FIELDS = {
    "year",
    "status",
    *(field for gas in UNIT_FIELDS.values() for field in gas["row_fields"]),
}
LEGACY_CLAIM_CEILING = (
    "Year-key alignment of caller-supplied, already captured NOAA GML CO2 and CH4 "
    "source-surface comparison outputs, preserving each gas's original unit, "
    "comparison status, retrieval metadata, and response digests. It performs no "
    "network retrieval or cross-gas arithmetic and does not establish simultaneous "
    "measurement, physical comparability, emissions, attribution, causation, source "
    "authenticity, measurement validity, or a scientific conclusion."
)
CLAIM_CEILING = (
    "Year-key alignment of caller-supplied, already captured NOAA GML CO2, CH4, and "
    "optionally N2O source-surface comparison outputs, preserving each gas's original "
    "unit, comparison status, retrieval metadata, and response digests. It performs no "
    "network retrieval or cross-gas arithmetic and does not establish simultaneous "
    "measurement, physical comparability, emissions, attribution, causation, source "
    "authenticity, measurement validity, or a scientific conclusion."
)
SF6_CLAIM_CEILING = (
    "Year-key alignment of caller-supplied, already captured NOAA GML CO2, CH4, "
    "optionally N2O, and SF6 source-surface comparison outputs, preserving each "
    "gas's original unit, comparison status, retrieval metadata, and response "
    "digests. It performs no network retrieval or cross-gas arithmetic and does "
    "not establish simultaneous measurement, physical comparability, emissions, "
    "attribution, causation, source authenticity, measurement validity, or a "
    "scientific conclusion."
)
LEGACY_NON_CLAIMS = [
    "Pairing rows by the same integer year does not make CO2 ppm and CH4 ppb values directly comparable or commensurate.",
    "The tool performs no unit conversion, ratio, sum, weighting, trend ranking, interpolation, or causal analysis across gases.",
    "Source timestamps and response digests are inherited from caller-supplied comparator outputs; they do not authenticate NOAA or make the captures simultaneous.",
    "The tool does not retrieve current data, validate measurements, estimate emissions, attribute sources, or establish scientific truth.",
]
NON_CLAIMS = [
    "Pairing rows by the same integer year does not make CO2 ppm, CH4 ppb, and N2O ppb values directly comparable or commensurate.",
    "The tool performs no unit conversion, ratio, sum, weighting, trend ranking, interpolation, or causal analysis across gases.",
    "Source timestamps and response digests are inherited from caller-supplied comparator outputs; they do not authenticate NOAA or make the captures simultaneous.",
    "The tool does not retrieve current data, validate measurements, estimate emissions, attribute sources, or establish scientific truth.",
]
SF6_NON_CLAIMS = [
    "Pairing rows by the same integer year does not make CO2 ppm, CH4/N2O ppb, and SF6 ppt values directly comparable or commensurate.",
    "The tool performs no unit conversion, ratio, sum, weighting, trend ranking, interpolation, or causal analysis across gases.",
    "Source timestamps and response digests are inherited from caller-supplied comparator outputs; they do not authenticate NOAA or make the captures simultaneous.",
    "The tool does not retrieve current data, validate measurements, estimate emissions, attribute sources, or establish scientific truth.",
]


class PairingInputError(ValueError):
    """Raised when either captured comparator output violates its bounded contract."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PairingInputError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise PairingInputError("non-standard JSON number is not allowed")


def _require_object(value: Any, field: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise PairingInputError(f"{field} must contain exactly {sorted(keys)}")
    return value


def _require_integer(value: Any, field: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise PairingInputError(f"{field} must be an integer from {minimum} through {maximum}")
    return value


def _require_decimal_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) > 64 or DECIMAL_RE.fullmatch(value) is None:
        raise PairingInputError(f"{field} must be a bounded decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise PairingInputError(f"{field} must be a finite decimal string") from exc
    if not decimal_value.is_finite():
        raise PairingInputError(f"{field} must be a finite decimal string")
    return value


def _parse_utc_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise PairingInputError(f"{field} must be a bounded UTC timestamp")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise PairingInputError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise PairingInputError(f"{field} must identify UTC")
    return parsed.astimezone(timezone.utc)


def _canonical_sha256(document: dict[str, Any]) -> str:
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_source_receipt(receipt: Any, *, gas: str, source_name: str) -> tuple[dict[str, Any], datetime]:
    receipt_keys = {
        "url", "acquisition_status", "parse_status", "http_status", "etag",
        "last_modified", "retrieved_at_utc", "response_bytes", "response_sha256",
        "records", "raw_response_retained",
    }
    row = _require_object(receipt, f"{gas}.{source_name}", receipt_keys)
    if row["url"] != SOURCE_URLS[gas][source_name]:
        raise PairingInputError(f"{gas}.{source_name} must use its declared fixed NOAA URL")
    if row["acquisition_status"] != "OK" or row["http_status"] != 200:
        raise PairingInputError(f"{gas}.{source_name} must be a captured HTTP 200 response")
    if row["parse_status"] not in {"FOUND", "PARTIAL_DATA", "NO_MATCH"}:
        raise PairingInputError(f"{gas}.{source_name} has no usable parsed source status")
    if row["raw_response_retained"] is not False:
        raise PairingInputError(f"{gas}.{source_name} must not carry a raw response body")
    if type(row["response_bytes"]) is not int or row["response_bytes"] < 0:
        raise PairingInputError(f"{gas}.{source_name}.response_bytes must be a nonnegative integer")
    if not isinstance(row["response_sha256"], str) or SHA256_RE.fullmatch(row["response_sha256"]) is None:
        raise PairingInputError(f"{gas}.{source_name}.response_sha256 must be lowercase SHA-256")
    if row["etag"] is not None and (not isinstance(row["etag"], str) or len(row["etag"]) > 256):
        raise PairingInputError(f"{gas}.{source_name}.etag must be null or bounded text")
    if row["last_modified"] is not None and (not isinstance(row["last_modified"], str) or len(row["last_modified"]) > 256):
        raise PairingInputError(f"{gas}.{source_name}.last_modified must be null or bounded text")
    captured_at = _parse_utc_timestamp(row["retrieved_at_utc"], f"{gas}.{source_name}.retrieved_at_utc")

    records = row["records"]
    if not isinstance(records, list) or len(records) > MAX_RANGE_YEARS:
        raise PairingInputError(f"{gas}.{source_name}.records must be a bounded array")
    fields = UNIT_FIELDS[gas]
    seen_years: set[int] = set()
    for index, record in enumerate(records):
        record = _require_object(
            record,
            f"{gas}.{source_name}.records[{index}]",
            {"year", fields["annual"], fields["uncertainty"]},
        )
        year = _require_integer(record["year"], f"{gas}.{source_name}.records[{index}].year", fields["min_year"], 2100)
        if year in seen_years:
            raise PairingInputError(f"{gas}.{source_name}.records contains a duplicate year")
        seen_years.add(year)
        _require_decimal_text(record[fields["annual"]], f"{gas}.{source_name}.records[{index}].{fields['annual']}")
        uncertainty = Decimal(_require_decimal_text(record[fields["uncertainty"]], f"{gas}.{source_name}.records[{index}].{fields['uncertainty']}"))
        if uncertainty < 0:
            raise PairingInputError(f"{gas}.{source_name}.records[{index}] uncertainty must not be negative")
    return row, captured_at


def _validate_comparison_output(document: Any, gas: str) -> dict[str, Any]:
    fields = UNIT_FIELDS[gas]
    top_keys = {
        "schema_version", "tool_id", "tool_version", "status", "requested_range",
        "invocation", "sources", "comparison", "claim_ceiling", "non_claims",
    }
    output = _require_object(document, f"{gas}_output", top_keys)
    if output["schema_version"] != fields["input_schema_version"]:
        raise PairingInputError(f"{gas}_output has an unsupported schema_version")
    if output["tool_id"] != fields["tool_id"] or output["tool_version"] != "0.1.0":
        raise PairingInputError(f"{gas}_output must come from the supported NOAA surface comparator")
    if output["status"] != "COMPARED":
        raise PairingInputError(f"{gas}_output status must be COMPARED; partial or unavailable outputs cannot be paired")
    if not isinstance(output["claim_ceiling"], str) or not output["claim_ceiling"].strip():
        raise PairingInputError(f"{gas}_output claim_ceiling is missing")
    if not isinstance(output["non_claims"], list) or not output["non_claims"] or any(not isinstance(item, str) for item in output["non_claims"]):
        raise PairingInputError(f"{gas}_output non_claims must be a nonempty string array")

    requested_range = _require_object(output["requested_range"], f"{gas}_output.requested_range", {"start_year", "end_year"})
    start = _require_integer(requested_range["start_year"], f"{gas}_output.requested_range.start_year", fields["min_year"], 2100)
    end = _require_integer(requested_range["end_year"], f"{gas}_output.requested_range.end_year", fields["min_year"], 2100)
    if start > end or end - start + 1 > MAX_RANGE_YEARS:
        raise PairingInputError(f"{gas}_output requested range is reversed or exceeds {MAX_RANGE_YEARS} years")

    invocation = _require_object(output["invocation"], f"{gas}_output.invocation", {"allow_public_network_flag", "requests_made"})
    if invocation["allow_public_network_flag"] is not True or invocation["requests_made"] != 2 or type(invocation["requests_made"]) is not int:
        raise PairingInputError(f"{gas}_output must retain the comparator's two-request invocation record")

    sources = _require_object(output["sources"], f"{gas}_output.sources", {"provider_page", "fixed_raw_table"})
    parsed_sources: dict[str, Any] = {}
    captured_times: list[datetime] = []
    for source_name in ("provider_page", "fixed_raw_table"):
        receipt, captured_at = _validate_source_receipt(sources[source_name], gas=gas, source_name=source_name)
        if any(not start <= record["year"] <= end for record in receipt["records"]):
            raise PairingInputError(f"{gas}.{source_name} contains a record outside its requested year range")
        parsed_sources[source_name] = receipt
        captured_times.append(captured_at)

    comparison_keys = {
        "status", "requested_year_count", "exact_match_count",
        "numeric_difference_count", "missing_year_count", "rows",
    }
    comparison = _require_object(output["comparison"], f"{gas}_output.comparison", comparison_keys)
    if comparison["status"] not in COMPARISON_STATUSES - {"NOT_COMPARED"}:
        raise PairingInputError(f"{gas}_output comparison is not a completed comparison")
    expected_years = list(range(start, end + 1))
    if comparison["requested_year_count"] != len(expected_years) or type(comparison["requested_year_count"]) is not int:
        raise PairingInputError(f"{gas}_output requested_year_count does not match its range")
    counts = {}
    for name in ("exact_match_count", "numeric_difference_count", "missing_year_count"):
        value = comparison[name]
        if type(value) is not int or value < 0:
            raise PairingInputError(f"{gas}_output comparison.{name} must be a nonnegative integer")
        counts[name] = value

    rows = comparison["rows"]
    if not isinstance(rows, list) or len(rows) != len(expected_years):
        raise PairingInputError(f"{gas}_output rows must include one record for every requested year")
    parsed_rows: dict[int, dict[str, Any]] = {}
    allowed_row_keys = {"year", "status", "page", "raw_table", *fields["row_fields"]}
    for index, row_value in enumerate(rows):
        row = row_value
        if not isinstance(row, dict) or not {"year", "status"} <= set(row) or not set(row) <= allowed_row_keys:
            raise PairingInputError(f"{gas}_output.rows[{index}] has unsupported fields")
        year = _require_integer(row["year"], f"{gas}_output.rows[{index}].year", start, end)
        if year in parsed_rows:
            raise PairingInputError(f"{gas}_output rows contain a duplicate year")
        if row["status"] not in YEAR_STATUSES:
            raise PairingInputError(f"{gas}_output.rows[{index}].status is unsupported")
        for field_name in fields["row_fields"] & set(row):
            _require_decimal_text(row[field_name], f"{gas}_output.rows[{index}].{field_name}")
        parsed_rows[year] = dict(row)
    if sorted(parsed_rows) != expected_years:
        raise PairingInputError(f"{gas}_output rows do not match the requested year range")
    source_year_maps: dict[str, dict[int, dict[str, Any]]] = {}
    for source_name, field_name in (("provider_page", "page"), ("fixed_raw_table", "raw_table")):
        source_year_maps[field_name] = {
            record["year"]: record for record in parsed_sources[source_name]["records"]
        }
    annual_field = fields["annual"]
    uncertainty_field = fields["uncertainty"]
    for year, row in parsed_rows.items():
        page_record = source_year_maps["page"].get(year)
        raw_record = source_year_maps["raw_table"].get(year)
        expected_status = (
            "MISSING_FROM_BOTH" if page_record is None and raw_record is None
            else "MISSING_FROM_PAGE" if page_record is None
            else "MISSING_FROM_RAW_TABLE" if raw_record is None
            else "EXACT_MATCH" if (
                page_record[annual_field] == raw_record[annual_field]
                and page_record[uncertainty_field] == raw_record[uncertainty_field]
            ) else "NUMERIC_DIFFERENCE"
        )
        if row["status"] != expected_status:
            raise PairingInputError(f"{gas}_output row status for {year} conflicts with its source records")
        expected_row_keys = {"year", "status"}
        if page_record is not None and raw_record is not None:
            expected_row_keys.update(fields["row_fields"])
        elif page_record is not None:
            expected_row_keys.add("page")
        elif raw_record is not None:
            expected_row_keys.add("raw_table")
        if set(row) != expected_row_keys:
            raise PairingInputError(f"{gas}_output row {year} does not match its source-comparison shape")
        if page_record is None and "page" in row:
            raise PairingInputError(f"{gas}_output row {year} includes a page record absent from its receipt")
        if raw_record is None and "raw_table" in row:
            raise PairingInputError(f"{gas}_output row {year} includes a raw record absent from its receipt")
        if page_record is not None and raw_record is not None:
            expected_values = {
                f"page_{annual_field}": page_record[annual_field],
                f"raw_table_{annual_field}": raw_record[annual_field],
                f"page_{uncertainty_field}": page_record[uncertainty_field],
                f"raw_table_{uncertainty_field}": raw_record[uncertainty_field],
                f"page_minus_raw_{annual_field}": format(Decimal(page_record[annual_field]) - Decimal(raw_record[annual_field]), "f"),
                f"page_minus_raw_{uncertainty_field}": format(Decimal(page_record[uncertainty_field]) - Decimal(raw_record[uncertainty_field]), "f"),
            }
            if any(row.get(key) != value for key, value in expected_values.items()):
                raise PairingInputError(f"{gas}_output row values for {year} conflict with its source records")
        else:
            for record_key, record in (("page", page_record), ("raw_table", raw_record)):
                if record is None:
                    continue
                nested = row.get(record_key)
                if nested != record:
                    raise PairingInputError(f"{gas}_output row {year} missing-source projection conflicts with its source receipt")
    observed_counts = {
        "exact_match_count": sum(row["status"] == "EXACT_MATCH" for row in parsed_rows.values()),
        "numeric_difference_count": sum(row["status"] == "NUMERIC_DIFFERENCE" for row in parsed_rows.values()),
        "missing_year_count": sum(row["status"].startswith("MISSING_") for row in parsed_rows.values()),
    }
    if counts != observed_counts or sum(counts.values()) != len(expected_years):
        raise PairingInputError(f"{gas}_output comparison counts do not match its row statuses")
    expected_comparison_status = (
        "DIFFERENT" if counts["numeric_difference_count"]
        else "PARTIAL" if counts["missing_year_count"]
        else "EXACT_MATCH"
    )
    if comparison["status"] != expected_comparison_status:
        raise PairingInputError(f"{gas}_output comparison status conflicts with its row statuses")

    return {
        "document": output,
        "range": {"start_year": start, "end_year": end},
        "invocation": invocation,
        "sources": parsed_sources,
        "comparison": comparison,
        "rows": parsed_rows,
        "captured_times": captured_times,
    }


def parse_request(raw: bytes) -> tuple[dict[str, Any], str]:
    if len(raw) > MAX_INPUT_BYTES:
        raise PairingInputError(f"request exceeds {MAX_INPUT_BYTES} bytes")
    try:
        envelope = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PairingInputError("request must be valid UTF-8 JSON with unique keys") from exc
    required_keys = {"schema_version", "co2_output", "ch4_output"}
    allowed_keys = required_keys | {"n2o_output", "sf6_output"}
    if not isinstance(envelope, dict) or not required_keys <= set(envelope) <= allowed_keys:
        raise PairingInputError(f"request must contain {sorted(required_keys)} and only optional n2o_output/sf6_output")
    if envelope["schema_version"] not in {
        LEGACY_INPUT_SCHEMA_VERSION,
        INPUT_SCHEMA_R1_VERSION,
        INPUT_SCHEMA_VERSION,
    }:
        raise PairingInputError("unsupported schema_version")
    if envelope["schema_version"] == LEGACY_INPUT_SCHEMA_VERSION and {"n2o_output", "sf6_output"} & set(envelope):
        raise PairingInputError("legacy input schema does not accept optional gas outputs")
    if envelope["schema_version"] == INPUT_SCHEMA_R1_VERSION and "sf6_output" in envelope:
        raise PairingInputError("schema r1 does not accept sf6_output")
    co2 = _validate_comparison_output(envelope["co2_output"], "co2")
    ch4 = _validate_comparison_output(envelope["ch4_output"], "ch4")
    parsed = {"co2": co2, "ch4": ch4}
    if "n2o_output" in envelope:
        parsed["n2o"] = _validate_comparison_output(envelope["n2o_output"], "n2o")
    if "sf6_output" in envelope:
        parsed["sf6"] = _validate_comparison_output(envelope["sf6_output"], "sf6")
    ranges = {gas: result["range"] for gas, result in parsed.items()}
    if any(year_range != co2["range"] for year_range in ranges.values()):
        raise PairingInputError("all supplied gas comparison outputs must request the same year range")
    return parsed, hashlib.sha256(raw).hexdigest()


def _source_receipt_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "records"}


def _capture_summary(parsed: dict[str, Any], gas: str) -> dict[str, Any]:
    document = parsed["document"]
    times = parsed["captured_times"]
    comparison = parsed["comparison"]
    return {
        "source_tool_id": document["tool_id"],
        "source_tool_version": document["tool_version"],
        "source_schema_version": document["schema_version"],
        "source_output_canonical_sha256": _canonical_sha256(document),
        "requested_range": parsed["range"],
        "upstream_invocation": document["invocation"],
        "comparison_status": comparison["status"],
        "comparison_counts": {
            "requested_year_count": comparison["requested_year_count"],
            "exact_match_count": comparison["exact_match_count"],
            "numeric_difference_count": comparison["numeric_difference_count"],
            "missing_year_count": comparison["missing_year_count"],
        },
        "capture_span_seconds": int((max(times) - min(times)).total_seconds()),
        "source_receipts": {
            name: _source_receipt_projection(receipt)
            for name, receipt in parsed["sources"].items()
        },
    }


def pair_outputs(parsed: dict[str, Any], input_payload_sha256: str) -> dict[str, Any]:
    co2 = parsed["co2"]
    ch4 = parsed["ch4"]
    years = range(co2["range"]["start_year"], co2["range"]["end_year"] + 1)
    gases = list(parsed)
    rows = [
        {"year": year, **{gas: parsed[gas]["rows"][year] for gas in gases}}
        for year in years
    ]
    values_by_gas = {
        gas: [row[gas]["status"] in {"EXACT_MATCH", "NUMERIC_DIFFERENCE"} for row in rows]
        for gas in gases
    }
    all_values_for_year = [all(values_by_gas[gas][index] for gas in gases) for index in range(len(rows))]
    all_capture_times = [time for gas in gases for time in parsed[gas]["captured_times"]]
    pairing = {
        "join_key": "year",
        "co2_unit": "ppm",
        "ch4_unit": "ppb",
        "cross_gas_arithmetic_performed": False,
        "simultaneous_capture_claimed": False,
    }
    metrics = {
        "paired_year_count": len(rows),
        "co2_rows_with_two_surface_values": sum(values_by_gas["co2"]),
        "ch4_rows_with_two_surface_values": sum(values_by_gas["ch4"]),
        "years_with_two_surface_values_for_both_gases": sum(
            co2_ok and ch4_ok for co2_ok, ch4_ok in zip(values_by_gas["co2"], values_by_gas["ch4"])
        ),
        "years_with_a_missing_surface_value": sum(not (co2_ok and ch4_ok) for co2_ok, ch4_ok in zip(values_by_gas["co2"], values_by_gas["ch4"])),
    }
    if "n2o" in parsed:
        pairing["n2o_unit"] = "ppb"
    if "sf6" in parsed:
        pairing["sf6_unit"] = "ppt"
    if "n2o" in parsed or "sf6" in parsed:
        metrics.update({
            f"{gas}_rows_with_two_surface_values": sum(values_by_gas[gas])
            for gas in ("n2o", "sf6") if gas in parsed
        })
        gas_count = len(parsed)
        suffix = {3: "three", 4: "four"}.get(gas_count)
        if suffix is None:
            raise PairingInputError("the paired gas set has an unsupported size")
        metrics.update({
            f"years_with_two_surface_values_for_all_{suffix}_gases": sum(all_values_for_year),
            "years_with_a_missing_surface_value_for_any_gas": sum(not value for value in all_values_for_year),
        })
    result = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "status": "PAIRED",
        "requested_range": co2["range"],
        "input_payload_sha256": input_payload_sha256,
        "pairing": pairing,
        "metrics": metrics,
        "source_captures": {gas: _capture_summary(parsed[gas], gas) for gas in gases},
        "cohort_capture_span_seconds": int((max(all_capture_times) - min(all_capture_times)).total_seconds()),
        "rows": rows,
    }
    if "sf6" in parsed:
        result["claim_ceiling"] = SF6_CLAIM_CEILING
        result["non_claims"] = list(SF6_NON_CLAIMS)
    elif "n2o" in parsed:
        result["claim_ceiling"] = CLAIM_CEILING
        result["non_claims"] = list(NON_CLAIMS)
    else:
        result["claim_ceiling"] = LEGACY_CLAIM_CEILING
        result["non_claims"] = list(LEGACY_NON_CLAIMS)
    return result


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON envelope from stdin")
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        parsed, payload_sha256 = parse_request(raw)
        result = pair_outputs(parsed, payload_sha256)
    except PairingInputError as exc:
        print(f"PAIR_INPUT_INVALID: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
