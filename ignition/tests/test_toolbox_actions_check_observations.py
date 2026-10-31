from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_actions_check_observations.py"
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-actions-check-observations-input-r0.schema.json"
OUTPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-actions-check-observations-output-r0.schema.json"
FIXTURE_PATH = IGNITION_ROOT / "tests/fixtures/toolbox-actions-check-observations/pr264-8230dc6-check-runs-r0.json"
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location("toolbox_actions_check_observations", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class ActionsCheckObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = FIXTURE_PATH.read_bytes()
        self.payload = json.loads(self.raw)

    def invoke(self, raw: bytes) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def classify(self, payload: dict | None = None) -> dict:
        raw = self.raw if payload is None else TOOL.canonical_json(payload).encode("utf-8")
        return TOOL.classify_check_observations(raw)

    def test_real_pr264_snapshot_is_exact_sha_app_and_context_bound(self) -> None:
        first = self.invoke(self.raw)
        second = self.invoke(self.raw)
        self.assertEqual(first.returncode, 0, first.stderr.decode())
        self.assertEqual(first.stdout, second.stdout)
        output = json.loads(first.stdout)
        input_schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(input_schema)
        Draft202012Validator.check_schema(output_schema)
        self.assertEqual(list(Draft202012Validator(input_schema).iter_errors(self.payload)), [])
        self.assertEqual(list(Draft202012Validator(output_schema).iter_errors(output)), [])
        self.assertEqual(output["expected_head_sha"], "8230dc6c13ec12c57f9c81f81994ee775ebb2ce8")
        self.assertEqual(output["check_runs_snapshot"], {"total_count": 11, "supplied_count": 11, "complete_caller_assertion": True})
        by_name = {row["name"]: row for row in output["requested_contexts"]}
        self.assertEqual(by_name["repository-path-accounting-preflight"]["observation"], "OBSERVED_SUCCESS")
        self.assertEqual(by_name["release-transaction-protocol-validation"]["observation"], "OBSERVED_SUCCESS")
        self.assertEqual(by_name["foundation-validation"]["observation"], "CONTEXT_NOT_OBSERVED")
        self.assertFalse(output["non_claims"]["snapshot_source_authenticated"])
        self.assertFalse(output["non_claims"]["required_check_satisfaction_interpreted"])
        self.assertFalse(output["non_claims"]["merge_or_release_authorized"])

    def test_exact_sha_wrong_app_and_stale_sha_are_distinct(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["requested_contexts"] = [
            {"name": "wrong-app", "app_id": 7},
            {"name": "stale-only", "app_id": 15368},
        ]
        base = payload["check_runs_snapshot"]["check_runs"][0]
        payload["check_runs_snapshot"] = {
            "total_count": 2,
            "check_runs": [
                {"id": 1, "name": "wrong-app", "head_sha": payload["expected_head_sha"], "status": "completed", "conclusion": "success", "app": {"id": 8, "slug": "other"}},
                {"id": 2, "name": "stale-only", "head_sha": "0" * 40, "status": "completed", "conclusion": "success", "app": {"id": 15368, "slug": "github-actions"}},
            ],
        }
        result = {row["name"]: row for row in self.classify(payload)["requested_contexts"]}
        self.assertEqual(result["wrong-app"]["observation"], "WRONG_APP_ONLY")
        self.assertEqual(result["stale-only"]["observation"], "STALE_SHA_ONLY")

    def test_duplicate_pending_cancelled_and_incomplete_are_not_promoted(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["requested_contexts"] = [
            {"name": "duplicated", "app_id": 15368},
            {"name": "pending", "app_id": 15368},
            {"name": "cancelled", "app_id": 15368},
        ]
        head = payload["expected_head_sha"]
        payload["check_runs_snapshot"] = {"total_count": 4, "check_runs": [
            {"id": 10, "name": "duplicated", "head_sha": head, "status": "completed", "conclusion": "success", "app": {"id": 15368, "slug": "github-actions"}},
            {"id": 11, "name": "duplicated", "head_sha": head, "status": "completed", "conclusion": "success", "app": {"id": 15368, "slug": "github-actions"}},
            {"id": 12, "name": "pending", "head_sha": head, "status": "in_progress", "conclusion": None, "app": {"id": 15368, "slug": "github-actions"}},
            {"id": 13, "name": "cancelled", "head_sha": head, "status": "completed", "conclusion": "cancelled", "app": {"id": 15368, "slug": "github-actions"}},
        ]}
        result = {row["name"]: row for row in self.classify(payload)["requested_contexts"]}
        self.assertEqual(result["duplicated"]["observation"], "DUPLICATE_AMBIGUOUS")
        self.assertEqual(result["pending"]["observation"], "PENDING")
        self.assertEqual(result["cancelled"]["observation"], "OBSERVED_NON_SUCCESS")
        payload["check_runs_complete"] = False
        incomplete = {row["name"]: row for row in self.classify(payload)["requested_contexts"]}
        self.assertTrue(all(row["observation"] == "SNAPSHOT_INCOMPLETE" for row in incomplete.values()))

    def test_missing_app_identity_is_unknown_not_a_wrong_app_or_success(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["requested_contexts"] = [{"name": "unknown-provider", "app_id": 15368}]
        payload["check_runs_snapshot"] = {"total_count": 1, "check_runs": [{
            "id": 21,
            "name": "unknown-provider",
            "head_sha": payload["expected_head_sha"],
            "status": "completed",
            "conclusion": "success",
            "app": None,
        }]}
        row = self.classify(payload)["requested_contexts"][0]
        self.assertEqual(row["observation"], "UNKNOWN_PROVIDER_STATE")
        self.assertEqual(row["matching_check_run_ids"], [])

    def test_invalid_inputs_fail_closed(self) -> None:
        bad_payloads = []
        changed = copy.deepcopy(self.payload)
        changed["expected_head_sha"] = "A" * 40
        bad_payloads.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["check_runs_complete"] = True
        changed["check_runs_snapshot"]["total_count"] -= 1
        bad_payloads.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["check_runs_snapshot"]["check_runs"].append(changed["check_runs_snapshot"]["check_runs"][0])
        changed["check_runs_snapshot"]["total_count"] += 1
        bad_payloads.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["extra_unrecognized_field"] = "must fail closed"
        bad_payloads.append(changed)
        for payload in bad_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(TOOL.InputError):
                    self.classify(payload)
        result = self.invoke(b'{"schema_version":"toolbox-actions-check-observations-input-r0","schema_version":"duplicate"}')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"duplicate JSON key", result.stderr)

    def test_cli_has_no_filesystem_side_effects_and_rejects_oversize_without_output(self) -> None:
        with self.subTest("no files"):
            with __import__("tempfile").TemporaryDirectory() as directory:
                result = subprocess.run([sys.executable, "-B", str(TOOL_PATH), "--stdin"], input=self.raw,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=directory, check=False)
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                self.assertEqual(list(Path(directory).iterdir()), [])
        with self.subTest("oversized"):
            result = self.invoke(b" " * (TOOL.MAX_INPUT_BYTES + 1))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b"")
            self.assertIn(b"input exceeds", result.stderr)


if __name__ == "__main__":
    unittest.main()
