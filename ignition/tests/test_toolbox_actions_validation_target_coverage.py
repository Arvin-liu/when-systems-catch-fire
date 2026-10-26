from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_actions_validation_target_coverage.py"
INPUT_PATH = IGNITION_ROOT / "tests/fixtures/toolbox-actions-validation-target-coverage/pr264-four-runs-r0.json"
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-actions-validation-target-coverage-input-r0.schema.json"
OUTPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-actions-validation-target-coverage-output-r0.schema.json"
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_actions_validation_target_coverage as coverage  # noqa: E402


class ActionsValidationTargetCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_fixture = INPUT_PATH.read_bytes()
        self.payload = json.loads(self.raw_fixture)

    def invoke(self, raw: bytes, *, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            check=False,
        )

    def test_four_real_runs_compare_target_coverage_without_promoting_claims(self) -> None:
        first = coverage.analyze_validation_target_coverage(self.raw_fixture)
        second = coverage.analyze_validation_target_coverage(self.raw_fixture)
        self.assertEqual(first, second)
        input_schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(input_schema)
        Draft202012Validator.check_schema(output_schema)
        self.assertEqual(list(Draft202012Validator(input_schema).iter_errors(self.payload)), [])
        self.assertEqual(list(Draft202012Validator(output_schema).iter_errors(first)), [])

        self.assertEqual(first["shared_context"]["pull_request_number"], 264)
        self.assertEqual(first["summary"]["run_count"], 4)
        self.assertEqual(first["summary"]["distinct_head_sha_count"], 4)
        self.assertEqual(len(first["summary"]["coverage_union_target_ids"]), 11)
        self.assertEqual(len(first["summary"]["coverage_intersection_target_ids"]), 10)
        self.assertEqual(first["summary"]["repeated_coverage_signature_count"], 1)

        runs = first["runs"]
        self.assertEqual([row["workflow_run"]["run_id"] for row in runs], [39889835854, 39899735096, 39910840268, 40064357026])
        self.assertEqual([len(row["plan"]["selected_target_ids"]) for row in runs], [10, 10, 10, 11])
        self.assertEqual([len(row["validation_receipt"]["declared_target_results"]) for row in runs], [10, 10, 10, 0])
        self.assertEqual(runs[3]["workflow_run"]["conclusion"], "cancelled")
        self.assertEqual(runs[3]["validation_receipt"]["presence"], "ABSENT_FROM_SUPPLIED_COMPLETE_FILE_LIST")
        self.assertEqual(runs[3]["validation_receipt"]["target_result_trust"], "NO_TARGET_RESULT_CLAIM")

        result_totals = {
            key: sum(row[key] for row in first["per_target"])
            for key in (
                "caller_declared_success_count",
                "caller_declared_failure_count",
                "no_target_result_claim_count",
            )
        }
        self.assertEqual(result_totals, {
            "caller_declared_success_count": 23,
            "caller_declared_failure_count": 7,
            "no_target_result_claim_count": 11,
        })
        operating_method = next(row for row in first["per_target"] if row["target_id"] == "g_operating_method_consumers")
        self.assertEqual(operating_method["plan_presence_count"], 1)
        self.assertEqual(operating_method["caller_declared_failure_count"], 0)
        self.assertEqual(operating_method["no_target_result_claim_count"], 1)

        self.assertEqual(
            [(len(row["added_target_ids"]), len(row["removed_target_ids"])) for row in first["adjacent_run_deltas"]],
            [(0, 0), (0, 0), (1, 0)],
        )
        repeated = first["repeated_coverage_signatures"][0]
        self.assertEqual(len(repeated["runs"]), 3)
        self.assertEqual(repeated["classification"], "REPEATED_COVERAGE_SET_NOT_EVIDENCE_OF_REDUNDANCY_OR_WASTE")
        self.assertEqual(len(first["timestamp_anomalies"]), 2)
        self.assertFalse(first["non_claims"]["missing_receipt_means_target_failure"])
        self.assertFalse(first["non_claims"]["component_validation_receipt_officially_verified"])
        self.assertFalse(first["non_claims"]["merge_or_release_authorized"])

    def test_rejects_mixed_context_duplicate_run_pair_and_corrupt_receipt(self) -> None:
        changed = copy.deepcopy(self.payload)
        changed["runs"][1]["actions_snapshot"]["workflow_run"]["pull_requests"][0]["number"] = 265
        with self.assertRaises(coverage.InputError):
            coverage.analyze_validation_target_coverage(json.dumps(changed).encode())

        changed = copy.deepcopy(self.payload)
        changed["runs"][1] = copy.deepcopy(changed["runs"][0])
        with self.assertRaisesRegex(coverage.InputError, "duplicate workflow run/attempt pair"):
            coverage.analyze_validation_target_coverage(json.dumps(changed).encode())

        changed = copy.deepcopy(self.payload)
        changed["runs"][0]["validation_receipt"]["receipt_sha256"] = "0" * 64
        with self.assertRaisesRegex(coverage.InputError, "receipt_sha256"):
            coverage.analyze_validation_target_coverage(json.dumps(changed).encode())

    def test_duplicate_json_keys_and_oversized_input_fail_without_partial_stdout(self) -> None:
        with self.assertRaisesRegex(coverage.InputError, "duplicate JSON key"):
            coverage.analyze_validation_target_coverage(
                b'{"schema_version":"x","schema_version":"y","runs":[]}'
            )
        result = self.invoke(b" " * (coverage.MAX_INPUT_BYTES + 1))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"ACTIONS_VALIDATION_TARGET_COVERAGE_INVALID", result.stderr)

    def test_cli_is_deterministic_and_creates_no_files(self) -> None:
        first = self.invoke(self.raw_fixture)
        second = self.invoke(self.raw_fixture)
        self.assertEqual(first.returncode, 0, first.stderr.decode())
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(hashlib.sha256(first.stdout).hexdigest(), hashlib.sha256(second.stdout).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            result = self.invoke(self.raw_fixture, cwd=Path(directory))
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
