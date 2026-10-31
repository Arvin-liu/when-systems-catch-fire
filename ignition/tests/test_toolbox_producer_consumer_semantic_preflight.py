from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_producer_consumer_semantic_preflight as preflight  # noqa: E402


SOURCE = '''import re

def parse_a_handoff(raw, freeze):
    text = raw.decode("utf-8")
    m2 = re.search(r"(?m)Case M2 fact: expected=`([^`]+)`; count=(\\d+)\\.", text)
    p2 = re.search(r"(?m)Case P2 fact: expected=`([^`]+)`; focused_repair_checker_pass=(true|false); ids=`([^`]+)`\\.", text)
    if not m2 or not p2:
        raise ValueError("frozen prose fields missing")
    return m2.group(1), p2.group(1)
'''

M2 = "Case M2 fact: expected=`OK`; count=2."
P2 = "Case P2 fact: expected=`OK`; ids=`repair-1`."
P2_COMPLETE = "Case P2 fact: expected=`OK`; focused_repair_checker_pass=true; ids=`repair-1`."


def payload(producer: str, source: str = SOURCE) -> dict:
    return {
        "schema_version": preflight.INPUT_SCHEMA_VERSION,
        "consumer_source": {
            "python_source": source,
            "function_name": "parse_a_handoff",
            "expected_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        },
        "producer_text": {
            "text": producer,
            "expected_sha256": hashlib.sha256(producer.encode("utf-8")).hexdigest(),
        },
    }


class ProducerConsumerSemanticPreflightTests(unittest.TestCase):
    def test_static_required_patterns_match_without_executing_consumer(self) -> None:
        result = preflight.evaluate(payload(M2 + "\n" + P2_COMPLETE))
        self.assertEqual(result["analysis_status"], "EVALUATED")
        self.assertEqual(result["contract_status"], "STATIC_REQUIRED_PATTERNS_MATCHED")
        self.assertEqual([row["status"] for row in result["checks"]], ["PRESENT", "PRESENT"])
        self.assertEqual(result["checks"][1]["capture_fields"][1]["field_id"], "focused_repair_checker_pass")
        self.assertEqual(result["checks"][1]["capture_fields"][1]["status"], "PRESENT")
        self.assertNotIn("true", json.dumps(result))
        self.assertFalse(result["claim_flags"]["consumer_code_executed"])
        self.assertFalse(result["claim_flags"]["semantic_equivalence_proven"])
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-producer-consumer-semantic-output-r0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(result)), [])

    def test_missing_required_field_is_identified(self) -> None:
        result = preflight.evaluate(payload(M2 + "\n" + P2))
        self.assertEqual(result["contract_status"], "STATIC_REQUIRED_PATTERN_MISMATCH")
        check = next(row for row in result["checks"] if row["consumer_variable"] == "p2")
        self.assertEqual(check["status"], "MALFORMED_OR_REORDERED")
        missing = next(row for row in check["capture_fields"] if row["field_id"] == "focused_repair_checker_pass")
        self.assertEqual(missing["status"], "ABSENT")

    def test_duplicate_identical_required_records_are_ambiguous(self) -> None:
        result = preflight.evaluate(payload(M2 + "\n" + P2_COMPLETE + "\n" + P2_COMPLETE))
        check = next(row for row in result["checks"] if row["consumer_variable"] == "p2")
        self.assertEqual(check["status"], "AMBIGUOUS")
        self.assertEqual(result["contract_status"], "STATIC_REQUIRED_PATTERN_MISMATCH")

    def test_conflicting_duplicate_records_are_contradictory(self) -> None:
        other = P2_COMPLETE.replace("expected=`OK`", "expected=`DIFFERENT`")
        result = preflight.evaluate(payload(M2 + "\n" + P2_COMPLETE + "\n" + other))
        check = next(row for row in result["checks"] if row["consumer_variable"] == "p2")
        self.assertEqual(check["status"], "CONTRADICTORY")

    def test_reordered_fields_do_not_pass(self) -> None:
        reordered = "Case P2 fact: focused_repair_checker_pass=true; expected=`OK`; ids=`repair-1`."
        result = preflight.evaluate(payload(M2 + "\n" + reordered))
        check = next(row for row in result["checks"] if row["consumer_variable"] == "p2")
        self.assertEqual(check["status"], "MALFORMED_OR_REORDERED")
        self.assertTrue(all(row["status"] == "PRESENT_UNVALIDATED" for row in check["capture_fields"]))

    def test_case_variant_does_not_pass(self) -> None:
        result = preflight.evaluate(payload(M2 + "\n" + P2_COMPLETE.replace("Case P2", "case P2")))
        check = next(row for row in result["checks"] if row["consumer_variable"] == "p2")
        self.assertEqual(check["status"], "CASE_VARIANT")

    def test_malformed_value_does_not_pass(self) -> None:
        malformed = P2_COMPLETE.replace("checker_pass=true", "checker_pass=maybe")
        result = preflight.evaluate(payload(M2 + "\n" + malformed))
        check = next(row for row in result["checks"] if row["consumer_variable"] == "p2")
        self.assertEqual(check["status"], "MALFORMED_OR_REORDERED")

    def test_dynamic_pattern_is_not_evaluated(self) -> None:
        dynamic_lines = SOURCE.splitlines()
        m2_line = next(index for index, line in enumerate(dynamic_lines) if "m2 = re.search" in line)
        dynamic_lines[m2_line] = dynamic_lines[m2_line].replace(", text)", " + freeze, text)", 1)
        dynamic = "\n".join(dynamic_lines) + "\n"
        result = preflight.evaluate(payload(M2 + "\n" + P2_COMPLETE, dynamic))
        self.assertEqual(result["contract_status"], "NOT_EVALUABLE")
        self.assertEqual(result["unsupported_reasons"], ["CONSUMER_REGEX_PATTERN_NOT_CONSTANT"])

    def test_nested_consumer_function_is_not_evaluated(self) -> None:
        nested = SOURCE.replace(
            "def parse_a_handoff(raw, freeze):\n",
            'def parse_a_handoff(raw, freeze):\n    def nested(text):\n        return re.search("Case M2 fact", text)\n',
            1,
        )
        result = preflight.evaluate(payload(M2 + "\n" + P2_COMPLETE, nested))
        self.assertEqual(result["contract_status"], "NOT_EVALUABLE")
        self.assertEqual(result["unsupported_reasons"], ["NESTED_CONSUMER_CODE_UNSUPPORTED"])

    def test_nested_repeat_regex_is_not_evaluated(self) -> None:
        dangerous = SOURCE.replace("([^`]+)", "(a+)+")
        result = preflight.evaluate(payload(M2 + "\n" + P2_COMPLETE, dangerous))
        self.assertEqual(result["contract_status"], "NOT_EVALUABLE")
        self.assertIn(result["unsupported_reasons"][0], {"REGEX_REPEAT_MUST_FOLLOW_A_CHARACTER_CLASS", "REGEX_REPEATED_GROUP_UNSUPPORTED"})

    def test_caller_expected_digest_mismatch_stops_analysis(self) -> None:
        value = payload(M2 + "\n" + P2_COMPLETE)
        value["consumer_source"]["expected_sha256"] = "0" * 64
        result = preflight.evaluate(value)
        self.assertEqual(result["analysis_status"], "NOT_RUN")
        self.assertEqual(result["contract_status"], "SOURCE_BINDING_MISMATCH")

    def test_ast_parse_does_not_execute_top_level_consumer_statements(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            marker = Path(temp_dir) / "consumer-ran"
            source = f'open({str(marker)!r}, "w").write("bad")\n' + SOURCE
            result = preflight.evaluate(payload(M2 + "\n" + P2_COMPLETE, source))
            self.assertEqual(result["contract_status"], "STATIC_REQUIRED_PATTERNS_MATCHED")
            self.assertFalse(marker.exists())

    def test_cli_rejects_invalid_unicode_surrogates_with_typed_json(self) -> None:
        value = payload("")
        value["producer_text"]["text"] = "\ud800"
        value["producer_text"]["expected_sha256"] = "0" * 64
        serialized = json.dumps(value, ensure_ascii=True).encode("utf-8")
        script = IGNITION_ROOT / "tools/toolbox_producer_consumer_semantic_preflight.py"
        completed = subprocess.run(
            [sys.executable, "-B", str(script), "--stdin"],
            input=serialized,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        output = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(output["contract_status"], "INPUT_INVALID")
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-producer-consumer-semantic-output-r0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(output)), [])

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaises(preflight.DuplicateJSONKey):
            preflight._unique_object([("schema_version", "a"), ("schema_version", "b")])


if __name__ == "__main__":
    unittest.main()
