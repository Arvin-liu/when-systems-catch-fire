from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import socket
import sys
import unittest
from typing import Optional
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_pair_noaa_co2_ch4_growth_by_year as TOOL  # noqa: E402


OPERATIONS = IGNITION_ROOT / "data/operations"
OUTPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-noaa-co2-ch4-growth-pair-output-r0.schema.json"


class FakeStdin:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


def captured_outputs() -> tuple[dict, dict]:
    co2 = json.loads((OPERATIONS / "toolbox-noaa-co2-source-surface-comparison-real-task-output-r0.json").read_text(encoding="utf-8"))
    ch4 = json.loads((OPERATIONS / "toolbox-noaa-ch4-source-surface-comparison-real-task-output-r0.json").read_text(encoding="utf-8"))
    return co2, ch4


def request_bytes(co2: Optional[dict] = None, ch4: Optional[dict] = None) -> bytes:
    real_co2, real_ch4 = captured_outputs()
    envelope = {
        "schema_version": TOOL.INPUT_SCHEMA_VERSION,
        "co2_output": deepcopy(co2 if co2 is not None else real_co2),
        "ch4_output": deepcopy(ch4 if ch4 is not None else real_ch4),
    }
    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def subset_output(document: dict, start: int, end: int) -> dict:
    result = deepcopy(document)
    result["requested_range"] = {"start_year": start, "end_year": end}
    for receipt in result["sources"].values():
        receipt["records"] = [row for row in receipt["records"] if start <= row["year"] <= end]
        receipt["parse_status"] = "FOUND" if len(receipt["records"]) == end - start + 1 else "PARTIAL_DATA"
    rows = [row for row in result["comparison"]["rows"] if start <= row["year"] <= end]
    counts = {
        "exact_match_count": sum(row["status"] == "EXACT_MATCH" for row in rows),
        "numeric_difference_count": sum(row["status"] == "NUMERIC_DIFFERENCE" for row in rows),
        "missing_year_count": sum(row["status"].startswith("MISSING_") for row in rows),
        "requested_year_count": end - start + 1,
    }
    result["comparison"].update(counts)
    result["comparison"]["rows"] = rows
    result["comparison"]["status"] = (
        "DIFFERENT" if counts["numeric_difference_count"]
        else "PARTIAL" if counts["missing_year_count"]
        else "EXACT_MATCH"
    )
    return result


class NoaaCo2Ch4YearPairingTests(unittest.TestCase):
    def test_real_captured_outputs_pair_by_year_and_preserve_independent_units(self) -> None:
        raw = request_bytes()
        parsed, input_sha = TOOL.parse_request(raw)
        result = TOOL.pair_outputs(parsed, input_sha)
        self.assertEqual(result["tool_id"], TOOL.TOOL_ID)
        self.assertEqual(result["status"], "PAIRED")
        self.assertEqual([row["year"] for row in result["rows"]], [2023, 2024, 2025])
        self.assertEqual(result["pairing"], {
            "join_key": "year",
            "co2_unit": "ppm",
            "ch4_unit": "ppb",
            "cross_gas_arithmetic_performed": False,
            "simultaneous_capture_claimed": False,
        })
        self.assertEqual(result["rows"][0]["co2"]["page_annual_increase_ppm"], "2.69")
        self.assertEqual(result["rows"][0]["ch4"]["page_annual_increase_ppb"], "8.29")
        self.assertNotIn("ratio", result["rows"][0])
        self.assertEqual(result["source_captures"]["co2"]["source_receipts"]["provider_page"]["retrieved_at_utc"], "2026-10-26T16:29:02Z")
        self.assertEqual(result["source_captures"]["ch4"]["source_receipts"]["fixed_raw_table"]["response_sha256"], "0501e15f5ffea518f8dfb90477ad28a7dbcdb26285c2792118f49b3a71e076eb")
        self.assertEqual(result["cohort_capture_span_seconds"], 3635)
        self.assertEqual(result["input_payload_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIn("source authenticity", result["claim_ceiling"])

    def test_output_schema_accepts_real_task_result(self) -> None:
        parsed, input_sha = TOOL.parse_request(request_bytes())
        result = TOOL.pair_outputs(parsed, input_sha)
        schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(result))
        self.assertEqual(errors, [])

    def test_pairing_is_deterministic_for_the_same_input_payload(self) -> None:
        raw = request_bytes()
        first, first_sha = TOOL.parse_request(raw)
        second, second_sha = TOOL.parse_request(raw)
        self.assertEqual(TOOL.pair_outputs(first, first_sha), TOOL.pair_outputs(second, second_sha))

    def test_missing_source_years_remain_explicit_in_each_gas_lane(self) -> None:
        co2, ch4 = captured_outputs()
        co2["sources"]["provider_page"]["records"] = [row for row in co2["sources"]["provider_page"]["records"] if row["year"] != 2025]
        co2["sources"]["provider_page"]["parse_status"] = "PARTIAL_DATA"
        row = next(row for row in co2["comparison"]["rows"] if row["year"] == 2025)
        raw_record = next(row for row in co2["sources"]["fixed_raw_table"]["records"] if row["year"] == 2025)
        co2["comparison"]["rows"][-1] = {"year": 2025, "status": "MISSING_FROM_PAGE", "raw_table": raw_record}
        co2["comparison"].update({"status": "PARTIAL", "exact_match_count": 2, "numeric_difference_count": 0, "missing_year_count": 1})
        parsed, input_sha = TOOL.parse_request(request_bytes(co2, ch4))
        result = TOOL.pair_outputs(parsed, input_sha)
        self.assertEqual(result["rows"][-1]["co2"]["status"], "MISSING_FROM_PAGE")
        self.assertEqual(result["rows"][-1]["ch4"]["status"], "EXACT_MATCH")
        self.assertEqual(result["metrics"]["years_with_a_missing_surface_value"], 1)

    def test_rejects_mismatched_ranges_species_urls_and_inconsistent_rows(self) -> None:
        co2, ch4 = captured_outputs()
        ch4 = subset_output(ch4, 2024, 2025)
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(request_bytes(co2, ch4))
        altered = deepcopy(captured_outputs()[1])
        altered["sources"]["provider_page"]["url"] = "https://example.invalid/data"
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(request_bytes(captured_outputs()[0], altered))
        altered = deepcopy(captured_outputs()[0])
        altered["comparison"]["rows"][0]["status"] = "NUMERIC_DIFFERENCE"
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(request_bytes(altered, captured_outputs()[1]))

    def test_rejects_invalid_digest_boolean_year_duplicate_rows_and_unavailable_output(self) -> None:
        co2, ch4 = captured_outputs()
        for mutate in (
            lambda c, m: c["sources"]["provider_page"].update(response_sha256="0"),
            lambda c, m: c["requested_range"].update(start_year=True),
            lambda c, m: c["comparison"]["rows"].__setitem__(1, deepcopy(c["comparison"]["rows"][0])),
            lambda c, m: c.update(status="SOURCE_UNAVAILABLE"),
        ):
            candidate = deepcopy(co2)
            mutate(candidate, None)
            with self.subTest(mutate=mutate), self.assertRaises(TOOL.PairingInputError):
                TOOL.parse_request(request_bytes(candidate, ch4))

    def test_rejects_duplicate_keys_extra_urls_nonstandard_numbers_and_oversized_payload(self) -> None:
        duplicate = b'{"schema_version":"wrong","schema_version":"wrong","co2_output":{},"ch4_output":{}}'
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(duplicate)
        raw = request_bytes()
        envelope = json.loads(raw)
        envelope["untrusted_url"] = "https://example.invalid/"
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(json.dumps(envelope).encode())
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(b'{"schema_version":NaN,"co2_output":{},"ch4_output":{}}')
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(b" " * (TOOL.MAX_INPUT_BYTES + 1))

    def test_cli_reads_stdin_without_network_or_file_side_effects(self) -> None:
        raw = request_bytes()
        with patch.object(sys, "stdin", FakeStdin(raw)), patch.object(socket, "create_connection", side_effect=AssertionError("network use")) as connect:
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                code = TOOL.main(["--stdin"])
        self.assertEqual(code, 0, stderr.getvalue())
        connect.assert_not_called()
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["status"], "PAIRED")
        self.assertEqual(result["pairing"]["cross_gas_arithmetic_performed"], False)

    def test_cli_invalid_input_emits_no_result(self) -> None:
        with patch.object(sys, "stdin", FakeStdin(b"{}")):
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("PAIR_INPUT_INVALID", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
