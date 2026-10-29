from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_actions_validation_attribution.py"
TIMELINE_PATH = IGNITION_ROOT / "tools/toolbox_actions_step_timeline.py"
FIXTURE_PATH = IGNITION_ROOT / "tests/fixtures/toolbox-actions-validation-attribution/input-run-40064357026-r0.json"
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-actions-validation-attribution-input-r0.schema.json"
OUTPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-actions-validation-attribution-output-r0.schema.json"

sys.path.insert(0, str(IGNITION_ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location("toolbox_actions_validation_attribution", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)

TIMELINE_SPEC = importlib.util.spec_from_file_location("toolbox_actions_step_timeline", TIMELINE_PATH)
TIMELINE = importlib.util.module_from_spec(TIMELINE_SPEC)
assert TIMELINE_SPEC.loader is not None
TIMELINE_SPEC.loader.exec_module(TIMELINE)


class ActionsValidationAttributionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_fixture = FIXTURE_PATH.read_bytes()
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

    def test_real_run_binds_plan_jobs_and_complete_artifact_file_list(self) -> None:
        first = self.invoke(self.raw_fixture)
        second = self.invoke(self.raw_fixture)
        self.assertEqual(first.returncode, 0, first.stderr.decode())
        self.assertEqual(first.stdout, second.stdout)
        receipt = json.loads(first.stdout)
        Draft202012Validator.check_schema(json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8")))
        Draft202012Validator.check_schema(json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8")))
        self.assertEqual(Draft202012Validator(json.loads(INPUT_SCHEMA_PATH.read_text())).validate(self.payload), None)
        output_errors = list(Draft202012Validator(json.loads(OUTPUT_SCHEMA_PATH.read_text())).iter_errors(receipt))
        self.assertEqual(output_errors, [])
        self.assertEqual(receipt["workflow_binding"]["run_id"], 40064357026)
        self.assertEqual(receipt["workflow_binding"]["run_attempt"], 1)
        self.assertTrue(receipt["workflow_binding"]["head_sha_matches_plan"])
        self.assertEqual(receipt["workflow_binding"]["base_sha_binding"], "SUPPLIED_PULL_REQUEST_BASE_MATCHES_PLAN")
        self.assertEqual(receipt["plan_binding"]["mode"], "FULL")
        self.assertEqual(receipt["plan_binding"]["plan_sha256"], "0bc5139b39c140cbb995d937276e332984d7ed6755c83acdbf489e8e07e1329f")
        self.assertEqual(len(receipt["plan_binding"]["selected_target_ids"]), 11)
        self.assertEqual(
            receipt["artifact_inventory"]["validation_receipt_presence"],
            "ABSENT_FROM_SUPPLIED_COMPLETE_FILE_LIST",
        )
        persisted_evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-actions-validation-attribution-real-task-r0.json").read_text(encoding="utf-8")
        )
        self.assertEqual(persisted_evidence["tool_output"], receipt)
        self.assertEqual(persisted_evidence["invocation"]["exit_code"], 0)
        self.assertEqual(receipt["validation_receipt"]["declared_target_results"], [])
        self.assertEqual(receipt["workflow_binding"]["conclusion"], "cancelled")
        jobs = {row["name"]: row for row in receipt["observed_jobs"]}
        self.assertEqual(jobs["foundation-validation-route"]["conclusion"], "cancelled")
        self.assertEqual(jobs["foundation-validation-route"]["observed_elapsed_seconds"], 1949.0)
        self.assertEqual(jobs["Full Foundation regression"]["conclusion"], "cancelled")
        self.assertEqual(jobs["Full Foundation regression"]["observed_elapsed_seconds"], 49.0)
        self.assertEqual(receipt["timeline_summary"]["sum_observed_job_intervals_seconds"], 1998.0)
        self.assertIn("NOT_BILLABLE_MINUTES", receipt["timeline_summary"]["interval_sum_semantics"])
        self.assertFalse(receipt["non_claims"]["component_validation_receipt_officially_verified"])
        self.assertFalse(receipt["non_claims"]["required_check_satisfaction_interpreted"])
        self.assertFalse(receipt["non_claims"]["merge_or_release_authorized"])

    def test_single_run_timeline_compatibility_and_unclassified_job_names(self) -> None:
        changed = copy.deepcopy(self.payload)
        run = changed["actions_snapshot"]["workflow_run"]
        jobs_response = changed["actions_snapshot"]["jobs_response"]
        jobs_response["jobs"].append({
            "id": 120790658354,
            "run_id": run["id"],
            "run_attempt": run["run_attempt"],
            "head_sha": run["head_sha"],
            "name": "unclassified sample job",
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-10-24T05:31:00Z",
            "completed_at": "2026-10-24T05:31:02Z",
            "steps": [],
        })
        jobs_response["total_count"] += 1
        raw = TOOL.canonical_json(changed).encode("utf-8")
        attributed = TOOL.attribute_validation_evidence(raw)
        legacy_snapshot = TIMELINE.summarize_snapshot(TOOL.canonical_json(changed["actions_snapshot"]).encode("utf-8"))
        self.assertEqual(attributed["timeline_summary"], legacy_snapshot["summary"])
        baseline = TIMELINE.summarize_snapshot(TOOL.canonical_json(self.payload["actions_snapshot"]).encode("utf-8"))
        comparison_evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-actions-validation-attribution-c1-evidence-r0.json").read_text(encoding="utf-8")
        )
        self.assertTrue(comparison_evidence["comparison"]["timeline_summary_equal"])
        self.assertEqual(comparison_evidence["comparison"]["existing_tool_summary"], baseline["summary"])
        self.assertEqual(comparison_evidence["decision"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertIn("unclassified sample job", {row["name"] for row in attributed["observed_jobs"]})
        self.assertEqual(attributed["workflow_binding"]["conclusion"], "cancelled")

    def test_matching_receipt_is_digest_bound_but_not_officially_validated(self) -> None:
        changed = copy.deepcopy(self.payload)
        plan = changed["validation_plan"]
        receipt = {
            "schema_version": "1.0.0",
            "base_sha": plan["source"]["base_sha"],
            "head_sha": plan["source"]["head_sha"],
            "validation_sha": plan["source"]["validation_sha"],
            "plan_sha256": plan["plan_sha256"],
            "validation_map_sha256": plan["validation_map_sha256"],
            "target_results": [
                {"target_id": target_id, "successful": True}
                for target_id in plan["selected_target_ids"]
            ],
        }
        receipt["receipt_sha256"] = TOOL.digest_json(receipt)
        changed["artifact_inventory"]["files"].append("component-validation-receipt.json")
        changed["validation_receipt"] = receipt
        output = TOOL.attribute_validation_evidence(TOOL.canonical_json(changed).encode("utf-8"))
        self.assertEqual(output["artifact_inventory"]["validation_receipt_presence"], "CONTENT_SUPPLIED_AND_BOUND")
        self.assertEqual(output["validation_receipt"]["binding_status"], "DIGEST_AND_PLAN_BINDING_MATCH")
        self.assertTrue(output["validation_receipt"]["declared_target_results"][0]["caller_declared_successful"])
        self.assertEqual(
            output["validation_receipt"]["target_result_trust"],
            "CALLER_SUPPLIED_DECLARATIONS_NOT_OFFICIAL_CI_VALIDATION",
        )
        self.assertFalse(output["non_claims"]["component_validation_receipt_officially_verified"])

    def test_incomplete_file_list_does_not_claim_receipt_absence(self) -> None:
        changed = copy.deepcopy(self.payload)
        changed["artifact_inventory"]["files_complete"] = False
        output = TOOL.attribute_validation_evidence(TOOL.canonical_json(changed).encode("utf-8"))
        self.assertEqual(
            output["artifact_inventory"]["validation_receipt_presence"],
            "UNKNOWN_IN_INCOMPLETE_FILE_LIST",
        )

    def test_binding_digest_inventory_and_duplicate_key_fail_closed(self) -> None:
        cases = []
        changed = copy.deepcopy(self.payload)
        changed["actions_snapshot"]["workflow_run"]["head_sha"] = "0" * 40
        cases.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["artifact_inventory"]["run_attempt"] = 2
        cases.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["validation_plan"]["plan_sha256"] = "0" * 64
        cases.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["artifact_inventory"]["files"].append("../component-validation-receipt.json")
        cases.append(changed)
        changed = copy.deepcopy(self.payload)
        changed["validation_receipt"] = {"schema_version": "1.0.0"}
        cases.append(changed)
        for index, payload in enumerate(cases):
            with self.subTest(case=index):
                with self.assertRaises(TOOL.InputError):
                    TOOL.attribute_validation_evidence(TOOL.canonical_json(payload).encode("utf-8"))
        duplicate_keys = b'{"schema_version":"toolbox-actions-validation-attribution-input-r0","schema_version":"x"}'
        with self.assertRaises(TOOL.InputError):
            TOOL.attribute_validation_evidence(duplicate_keys)

    def test_cli_rejects_oversized_input_without_partial_stdout(self) -> None:
        result = self.invoke(b" " * (TOOL.MAX_INPUT_BYTES + 1))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"ACTIONS_VALIDATION_ATTRIBUTION_INVALID", result.stderr)

    def test_stdin_cli_creates_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            result = self.invoke(self.raw_fixture, cwd=cwd)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual(list(cwd.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
