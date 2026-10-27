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
INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-noaa-co2-ch4-growth-pair-input-r1.schema.json"
LEGACY_INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-noaa-co2-ch4-growth-pair-input-r0.schema.json"
OUTPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-noaa-co2-ch4-growth-pair-output-r1.schema.json"
FOUR_GAS_INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-noaa-co2-ch4-growth-pair-input-r2.schema.json"
FOUR_GAS_OUTPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-noaa-co2-ch4-growth-pair-output-r2.schema.json"


class FakeStdin:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


def captured_outputs() -> tuple[dict, dict]:
    co2 = json.loads((OPERATIONS / "toolbox-noaa-co2-source-surface-comparison-real-task-output-r0.json").read_text(encoding="utf-8"))
    ch4 = json.loads((OPERATIONS / "toolbox-noaa-ch4-source-surface-comparison-real-task-output-r0.json").read_text(encoding="utf-8"))
    return co2, ch4


def captured_n2o_output() -> dict:
    return json.loads((OPERATIONS / "toolbox-noaa-n2o-source-surface-comparison-real-task-output-r0.json").read_text(encoding="utf-8"))


def captured_sf6_output() -> dict:
    return json.loads((OPERATIONS / "toolbox-noaa-sf6-source-surface-comparison-real-task-output-r0.json").read_text(encoding="utf-8"))


def request_bytes(
    co2: Optional[dict] = None,
    ch4: Optional[dict] = None,
    n2o: Optional[dict] = None,
    sf6: Optional[dict] = None,
    schema_version: Optional[str] = None,
) -> bytes:
    real_co2, real_ch4 = captured_outputs()
    selected_schema = schema_version or (
        TOOL.INPUT_SCHEMA_VERSION if sf6 is not None
        else TOOL.INPUT_SCHEMA_R1_VERSION if n2o is not None
        else TOOL.LEGACY_INPUT_SCHEMA_VERSION
    )
    envelope = {
        "schema_version": selected_schema,
        "co2_output": deepcopy(co2 if co2 is not None else real_co2),
        "ch4_output": deepcopy(ch4 if ch4 is not None else real_ch4),
    }
    if n2o is not None:
        envelope["n2o_output"] = deepcopy(n2o)
    if sf6 is not None:
        envelope["sf6_output"] = deepcopy(sf6)
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
        raw = (OPERATIONS / "toolbox-noaa-co2-ch4-growth-pair-real-task-input-r0.json").read_bytes()
        parsed, input_sha = TOOL.parse_request(raw)
        result = TOOL.pair_outputs(parsed, input_sha)
        self.assertEqual(result["tool_id"], TOOL.TOOL_ID)
        self.assertEqual(result["tool_version"], "0.3.0")
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

        legacy = json.loads((OPERATIONS / "toolbox-noaa-co2-ch4-growth-pair-real-task-output-r0.json").read_text(encoding="utf-8"))
        normalized = deepcopy(result)
        normalized["schema_version"] = legacy["schema_version"]
        normalized["tool_version"] = legacy["tool_version"]
        self.assertEqual(normalized, legacy)

    def test_real_captured_n2o_output_extends_the_pair_to_three_gases(self) -> None:
        raw = request_bytes(n2o=captured_n2o_output())
        parsed, input_sha = TOOL.parse_request(raw)
        result = TOOL.pair_outputs(parsed, input_sha)
        self.assertEqual(result["schema_version"], TOOL.OUTPUT_SCHEMA_VERSION)
        self.assertEqual(result["tool_version"], "0.3.0")
        self.assertEqual([row["year"] for row in result["rows"]], [2023, 2024, 2025])
        self.assertEqual(result["rows"][0]["n2o"]["page_annual_increase_ppb"], "1.01")
        self.assertEqual(result["rows"][1]["n2o"]["page_annual_increase_ppb"], "1.02")
        self.assertEqual(result["rows"][2]["n2o"]["page_annual_increase_ppb"], "1.23")
        self.assertEqual(result["pairing"]["n2o_unit"], "ppb")
        self.assertEqual(result["metrics"]["years_with_two_surface_values_for_all_three_gases"], 3)
        self.assertEqual(result["metrics"]["years_with_a_missing_surface_value_for_any_gas"], 0)
        self.assertEqual(result["source_captures"]["n2o"]["source_tool_id"], "research.compare_noaa_n2o_source_surfaces")
        self.assertEqual(result["pairing"]["cross_gas_arithmetic_performed"], False)
        self.assertEqual(result["pairing"]["simultaneous_capture_claimed"], False)

    def test_output_schema_accepts_real_task_result(self) -> None:
        schema = json.loads(FOUR_GAS_OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        for raw in (request_bytes(), request_bytes(n2o=captured_n2o_output())):
            parsed, input_sha = TOOL.parse_request(raw)
            result = TOOL.pair_outputs(parsed, input_sha)
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(result))
            self.assertEqual(errors, [])

    def test_four_gas_real_task_preserves_units_statuses_and_capture_receipts(self) -> None:
        raw = (OPERATIONS / "toolbox-noaa-co2-ch4-growth-pair-n2o-sf6-extension-real-task-input-r2.json").read_bytes()
        parsed, input_sha = TOOL.parse_request(raw)
        result = TOOL.pair_outputs(parsed, input_sha)
        self.assertEqual(result["tool_version"], "0.3.0")
        self.assertEqual(result["schema_version"], "toolbox-noaa-co2-ch4-growth-pair-output-r2")
        self.assertEqual(result["pairing"]["sf6_unit"], "ppt")
        self.assertEqual(result["rows"][0]["sf6"]["page_annual_increase_ppt"], "0.41")
        self.assertEqual(result["rows"][0]["sf6"]["page_minus_raw_uncertainty_ppt"], "0.004")
        self.assertEqual(result["rows"][0]["sf6"]["status"], "NUMERIC_DIFFERENCE")
        self.assertEqual(result["metrics"]["years_with_two_surface_values_for_all_four_gases"], 3)
        self.assertEqual(result["metrics"]["years_with_a_missing_surface_value_for_any_gas"], 0)
        self.assertEqual(result["source_captures"]["sf6"]["source_tool_id"], "research.compare_noaa_sf6_source_surfaces")
        self.assertEqual(len(result["source_captures"]["sf6"]["source_receipts"]), 2)
        self.assertFalse(result["pairing"]["cross_gas_arithmetic_performed"])
        self.assertFalse(result["pairing"]["simultaneous_capture_claimed"])
        self.assertIn("ppt values directly comparable", " ".join(result["non_claims"]))

        schema = json.loads(FOUR_GAS_OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(result))
        self.assertEqual(errors, [])

    def test_four_gas_input_schema_accepts_captured_outputs_and_r1_rejects_sf6(self) -> None:
        schema = json.loads(FOUR_GAS_INPUT_SCHEMA.read_text(encoding="utf-8"))
        four_gas = json.loads(request_bytes(n2o=captured_n2o_output(), sf6=captured_sf6_output()))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(four_gas)), [])
        three_gas_r1 = json.loads(request_bytes(n2o=captured_n2o_output()))
        self.assertEqual(three_gas_r1["schema_version"], TOOL.INPUT_SCHEMA_R1_VERSION)
        three_gas_r1["sf6_output"] = captured_sf6_output()
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(json.dumps(three_gas_r1).encode("utf-8"))

    def test_four_gas_cli_is_offline_and_rejects_wrong_sf6_source(self) -> None:
        raw = request_bytes(n2o=captured_n2o_output(), sf6=captured_sf6_output())
        with patch.object(sys, "stdin", FakeStdin(raw)), patch.object(socket, "create_connection", side_effect=AssertionError("network use")) as connect:
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                code = TOOL.main(["--stdin"])
        self.assertEqual(code, 0, stderr.getvalue())
        connect.assert_not_called()
        result = json.loads(stdout.getvalue())
        self.assertIn("sf6", result["rows"][-1])
        self.assertEqual(result["pairing"]["sf6_unit"], "ppt")

        altered_sf6 = captured_sf6_output()
        altered_sf6["sources"]["provider_page"]["url"] = "https://example.invalid/sf6"
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(request_bytes(n2o=captured_n2o_output(), sf6=altered_sf6))

    def test_four_gas_rejects_mismatched_range_and_keeps_missing_sf6_explicit(self) -> None:
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(request_bytes(n2o=captured_n2o_output(), sf6=subset_output(captured_sf6_output(), 2024, 2025)))

        sf6 = captured_sf6_output()
        sf6["sources"]["provider_page"]["records"] = [
            record for record in sf6["sources"]["provider_page"]["records"] if record["year"] != 2025
        ]
        sf6["sources"]["provider_page"]["parse_status"] = "PARTIAL_DATA"
        raw_record = next(record for record in sf6["sources"]["fixed_raw_table"]["records"] if record["year"] == 2025)
        sf6["comparison"]["rows"][-1] = {"year": 2025, "status": "MISSING_FROM_PAGE", "raw_table": raw_record}
        sf6["comparison"].update({
            "status": "DIFFERENT",
            "exact_match_count": 0,
            "numeric_difference_count": 2,
            "missing_year_count": 1,
        })
        parsed, input_sha = TOOL.parse_request(request_bytes(n2o=captured_n2o_output(), sf6=sf6))
        result = TOOL.pair_outputs(parsed, input_sha)
        last_sf6 = result["rows"][-1]["sf6"]
        self.assertEqual(last_sf6["status"], "MISSING_FROM_PAGE")
        self.assertNotIn("page_annual_increase_ppt", last_sf6)
        self.assertEqual(result["metrics"]["sf6_rows_with_two_surface_values"], 2)
        self.assertEqual(result["metrics"]["years_with_two_surface_values_for_all_four_gases"], 2)
        self.assertEqual(result["metrics"]["years_with_a_missing_surface_value_for_any_gas"], 1)

    def test_input_schemas_accept_legacy_pair_and_versioned_optional_n2o(self) -> None:
        legacy_schema = json.loads(LEGACY_INPUT_SCHEMA.read_text(encoding="utf-8"))
        three_gas_schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
        current_schema = json.loads(FOUR_GAS_INPUT_SCHEMA.read_text(encoding="utf-8"))
        legacy = json.loads(request_bytes())
        two_gas_r1 = json.loads(request_bytes(schema_version=TOOL.INPUT_SCHEMA_R1_VERSION))
        three_gas_r1 = json.loads(request_bytes(n2o=captured_n2o_output()))
        four_gas_r2 = json.loads(request_bytes(n2o=captured_n2o_output(), sf6=captured_sf6_output()))
        self.assertEqual(list(Draft202012Validator(legacy_schema).iter_errors(legacy)), [])
        old_validator = Draft202012Validator(three_gas_schema)
        self.assertEqual(list(old_validator.iter_errors(two_gas_r1)), [])
        self.assertEqual(list(old_validator.iter_errors(three_gas_r1)), [])
        current_validator = Draft202012Validator(current_schema)
        self.assertEqual(list(current_validator.iter_errors(four_gas_r2)), [])

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

    def test_missing_n2o_surface_value_remains_explicit_without_zero_fill(self) -> None:
        n2o = captured_n2o_output()
        n2o["sources"]["provider_page"]["records"] = [
            row for row in n2o["sources"]["provider_page"]["records"] if row["year"] != 2025
        ]
        n2o["sources"]["provider_page"]["parse_status"] = "PARTIAL_DATA"
        raw_record = next(row for row in n2o["sources"]["fixed_raw_table"]["records"] if row["year"] == 2025)
        n2o["comparison"]["rows"][-1] = {"year": 2025, "status": "MISSING_FROM_PAGE", "raw_table": raw_record}
        n2o["comparison"].update({"status": "PARTIAL", "exact_match_count": 2, "numeric_difference_count": 0, "missing_year_count": 1})
        parsed, input_sha = TOOL.parse_request(request_bytes(n2o=n2o))
        result = TOOL.pair_outputs(parsed, input_sha)
        self.assertEqual(result["rows"][-1]["n2o"]["status"], "MISSING_FROM_PAGE")
        self.assertNotIn("page_annual_increase_ppb", result["rows"][-1]["n2o"])
        self.assertEqual(result["metrics"]["years_with_two_surface_values_for_all_three_gases"], 2)
        self.assertEqual(result["metrics"]["years_with_a_missing_surface_value_for_any_gas"], 1)

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
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(request_bytes(n2o=subset_output(captured_n2o_output(), 2024, 2025)))
        altered_n2o = captured_n2o_output()
        altered_n2o["sources"]["provider_page"]["url"] = "https://example.invalid/n2o"
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(request_bytes(n2o=altered_n2o))

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
        altered_n2o = captured_n2o_output()
        altered_n2o["sources"]["provider_page"]["response_sha256"] = "0"
        with self.assertRaises(TOOL.PairingInputError):
            TOOL.parse_request(request_bytes(n2o=altered_n2o))

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
        raw = request_bytes(n2o=captured_n2o_output())
        with patch.object(sys, "stdin", FakeStdin(raw)), patch.object(socket, "create_connection", side_effect=AssertionError("network use")) as connect:
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                code = TOOL.main(["--stdin"])
        self.assertEqual(code, 0, stderr.getvalue())
        connect.assert_not_called()
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["status"], "PAIRED")
        self.assertEqual(len(result["rows"][-1]), 4)
        self.assertIn("n2o", result["rows"][-1])
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
