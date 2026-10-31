from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

from tools.toolbox_compare_task_decomposition_solvability import (
    DecompositionError,
    MAX_INPUT_BYTES,
    analyze_bytes,
    parse_request,
)


IGNITION_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-task-decomposition-solvability/valid-input-r0.json"
TOOL = IGNITION_ROOT / "tools/toolbox_compare_task_decomposition_solvability.py"
REAL_TASK_INPUT = IGNITION_ROOT / "data/operations/toolbox-task-decomposition-solvability-real-task-input-r0.json"
REAL_TASK_OUTPUT = IGNITION_ROOT / "data/operations/toolbox-task-decomposition-solvability-real-task-output-r0.json"
REAL_TASK_EVIDENCE = IGNITION_ROOT / "data/operations/toolbox-task-decomposition-solvability-real-task-evidence-r0.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def encode(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


class TaskDecompositionSolvabilityTests(unittest.TestCase):
    def test_fixture_rejects_unchecked_shortcut_and_retains_pareto_tradeoff(self):
        result = analyze_bytes(FIXTURE.read_bytes())
        alternatives = {item["alternative_id"]: item for item in result["alternatives"]}

        self.assertEqual(alternatives["unchecked_shortcut"]["status"], "UNSOLVABLE_AS_DECLARED")
        self.assertIn("draft_only:NO_OUTPUT_VALIDATOR_DECLARED", alternatives["unchecked_shortcut"]["blockers"])
        self.assertIn("draft_only:CAPABILITY_CANNOT_PRODUCE_OUTPUT_TYPES:validated_report", alternatives["unchecked_shortcut"]["blockers"])
        self.assertEqual(alternatives["staged_verified"]["status"], "SOLVABLE_AS_DECLARED")
        self.assertEqual(alternatives["combined_verified"]["status"], "SOLVABLE_AS_DECLARED")
        self.assertIsNone(result["structural_leader_id"])
        self.assertEqual(result["resource_frontier"]["status"], "CALLER_ESTIMATE_PARETO_FRONTIER")
        self.assertEqual(result["resource_frontier"]["alternative_ids"], ["staged_verified", "combined_verified"])
        self.assertFalse(result["validators_executed"])
        self.assertFalse(result["executors_invoked"])
        self.assertFalse(result["execution_authorized"])

    def test_missing_validator_blocks_work_unit(self):
        request = load_fixture()
        request["alternatives"][1]["work_units"][1]["validator_ids"] = []
        result = analyze_bytes(encode(request))
        alternative = next(item for item in result["alternatives"] if item["alternative_id"] == "staged_verified")
        self.assertEqual(alternative["status"], "UNSOLVABLE_AS_DECLARED")
        self.assertTrue(any("NO_OUTPUT_VALIDATOR_DECLARED" in reason for reason in alternative["blockers"]))

    def test_unreachable_input_is_not_supplied_by_an_unrelated_unit(self):
        request = load_fixture()
        request["alternatives"][1]["work_units"][1]["depends_on"] = []
        result = analyze_bytes(encode(request))
        alternative = next(item for item in result["alternatives"] if item["alternative_id"] == "staged_verified")
        self.assertIn("synthesize:REQUIRED_INPUT_TYPES_NOT_REACHABLE:source_notes", alternative["blockers"])

    def test_dependency_cycle_is_blocked(self):
        request = load_fixture()
        request["alternatives"][1]["work_units"][0]["depends_on"] = ["review"]
        result = analyze_bytes(encode(request))
        alternative = next(item for item in result["alternatives"] if item["alternative_id"] == "staged_verified")
        self.assertIn("DEPENDENCY_CYCLE", alternative["blockers"])

    def test_unknown_executor_availability_stays_unknown(self):
        request = load_fixture()
        contract = next(item for item in request["capability_contracts"] if item["capability_id"] == "independent_review")
        contract["availability"] = "UNKNOWN"
        result = analyze_bytes(encode(request))
        alternative = next(item for item in result["alternatives"] if item["alternative_id"] == "staged_verified")
        self.assertEqual(alternative["status"], "SOLVABILITY_UNKNOWN")
        self.assertIn("review:CAPABILITY_AVAILABILITY_UNKNOWN", alternative["unknowns"])

    def test_unknown_validator_availability_stays_unknown_when_its_contract_covers_output(self):
        request = load_fixture()
        contract = next(item for item in request["validator_contracts"] if item["validator_id"] == "validated_report_validator")
        contract["availability"] = "UNKNOWN"
        result = analyze_bytes(encode(request))
        alternative = next(item for item in result["alternatives"] if item["alternative_id"] == "combined_verified")
        self.assertEqual(alternative["status"], "SOLVABILITY_UNKNOWN")
        self.assertIn("combined:VALIDATOR_AVAILABILITY_UNKNOWN:validated_report_validator", alternative["unknowns"])

    def test_declared_unavailable_validator_is_blocked(self):
        request = load_fixture()
        contract = next(item for item in request["validator_contracts"] if item["validator_id"] == "validated_report_validator")
        contract["availability"] = "UNAVAILABLE"
        result = analyze_bytes(encode(request))
        alternative = next(item for item in result["alternatives"] if item["alternative_id"] == "combined_verified")
        self.assertEqual(alternative["status"], "UNSOLVABLE_AS_DECLARED")
        self.assertIn("combined:VALIDATOR_DECLARED_UNAVAILABLE:validated_report_validator", alternative["blockers"])

    def test_unknown_cost_preserves_uncertainty(self):
        request = load_fixture()
        request["alternatives"][1]["work_units"][0]["estimated_cost"]["wall_clock_seconds"] = None
        result = analyze_bytes(encode(request))
        alternative = next(item for item in result["alternatives"] if item["alternative_id"] == "staged_verified")
        self.assertEqual(alternative["status"], "SOLVABILITY_UNKNOWN")
        self.assertEqual(alternative["resource_estimate"]["status"], "UNKNOWN")
        self.assertIsNone(alternative["resource_estimate"]["total"])
        self.assertIsNone(result["structural_leader_id"])

    def test_resource_budget_excess_is_blocked(self):
        request = load_fixture()
        request["resource_budget"]["max_action_count"] = 0
        result = analyze_bytes(encode(request))
        alternative = next(item for item in result["alternatives"] if item["alternative_id"] == "combined_verified")
        self.assertEqual(alternative["status"], "UNSOLVABLE_AS_DECLARED")
        self.assertIn("RESOURCE_BUDGET_EXCEEDED:ACTION_COUNT", alternative["blockers"])

    def test_bad_availability_type_is_controlled_input_error(self):
        request = load_fixture()
        request["capability_contracts"][0]["availability"] = ["AVAILABLE"]
        with self.assertRaisesRegex(DecompositionError, "availability is invalid"):
            parse_request(encode(request))

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(DecompositionError, "duplicate JSON key"):
            parse_request(b'{"schema_version":"x","schema_version":"y"}')

    def test_boolean_cost_and_nonstandard_json_numbers_are_rejected(self):
        request = load_fixture()
        request["alternatives"][1]["work_units"][0]["estimated_cost"]["action_count"] = True
        with self.assertRaisesRegex(DecompositionError, "finite non-negative number"):
            parse_request(encode(request))
        with self.assertRaisesRegex(DecompositionError, "non-standard JSON number"):
            parse_request(b'{"schema_version":NaN}')

    def test_large_cost_numbers_fail_closed_at_schema_boundary(self):
        for value in (10**32, 1e32):
            with self.subTest(value=repr(value)):
                request = load_fixture()
                request["alternatives"][1]["work_units"][0]["estimated_cost"]["wall_clock_seconds"] = value
                with self.assertRaises(DecompositionError):
                    parse_request(encode(request))

    def test_input_size_is_bounded(self):
        with self.assertRaisesRegex(DecompositionError, "input exceeds"):
            parse_request(b" " * (MAX_INPUT_BYTES + 1))

    def test_cli_emits_json_and_invalid_input_does_not_echo_caller_bytes(self):
        valid = subprocess.run([sys.executable, "-B", str(TOOL), "--stdin"], input=FIXTURE.read_bytes(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(valid.returncode, 0, valid.stderr.decode("utf-8", errors="replace"))
        result = json.loads(valid.stdout)
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["executors_invoked"])

        secret_like_input = b"not-json user-secret-marker"
        invalid = subprocess.run([sys.executable, "-B", str(TOOL), "--stdin"], input=secret_like_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(invalid.returncode, 2)
        error = json.loads(invalid.stdout)
        self.assertEqual(error["status"], "INVALID_INPUT")
        self.assertNotIn(b"user-secret-marker", invalid.stdout)
        self.assertNotIn(b"user-secret-marker", invalid.stderr)

    def test_actual_task_receipt_replays_against_exact_input_and_tool_source(self):
        raw = REAL_TASK_INPUT.read_bytes()
        evidence = json.loads(REAL_TASK_EVIDENCE.read_text(encoding="utf-8"))
        expected = json.loads(REAL_TASK_OUTPUT.read_text(encoding="utf-8"))
        proc = subprocess.run([sys.executable, "-B", str(TOOL), "--stdin"], input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", errors="replace"))
        actual = json.loads(proc.stdout)
        self.assertEqual(actual, expected)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence["invocation"]["input_sha256"])
        self.assertEqual(hashlib.sha256(proc.stdout).hexdigest(), evidence["invocation"]["stdout_sha256"])
        self.assertEqual(git_blob_sha1(TOOL.read_bytes()), evidence["invocation"]["tool_git_blob_sha1"])
        alternatives = {item["alternative_id"]: item for item in actual["alternatives"]}
        self.assertEqual(alternatives["focused_homepage_checks_only"]["status"], "UNSOLVABLE_AS_DECLARED")
        self.assertIn("REQUIRED_TASK_OUTPUTS_NOT_PRODUCED:formal_main_release_readiness", alternatives["focused_homepage_checks_only"]["blockers"])
        self.assertIn("run_full_foundation_gate:CAPABILITY_DECLARED_UNAVAILABLE", alternatives["current_protected_main_release_path"]["blockers"])
        self.assertFalse(actual["execution_authorized"])
        self.assertFalse(actual["executors_invoked"])
        self.assertFalse(actual["validators_executed"])


if __name__ == "__main__":
    unittest.main()
