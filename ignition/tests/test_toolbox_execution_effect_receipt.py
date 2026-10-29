from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-execution-effect-receipt/valid-effect-r0.json"
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_execution_effect_receipt.py"
INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-execution-effect-receipt-input-r0.schema.json"
OUTPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-execution-effect-receipt-output-r0.schema.json"
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_execution_effect_receipt as tool  # noqa: E402
import toolbox_actions_validation_attribution as actions_attribution  # noqa: E402
import toolbox_failure_anchored_recovery as failure_recovery  # noqa: E402
import toolbox_portable_research_episode as portable_episode  # noqa: E402


class ExecutionEffectReceiptTests(unittest.TestCase):
    def valid_input(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def codes(self, result: dict) -> set[str]:
        return {row["code"] for row in result["findings"]}

    def test_binds_declared_observation_without_claiming_truth_or_authority(self) -> None:
        result = tool.evaluate(self.valid_input())
        self.assertEqual(result["outcome_status"], "OUTCOME_RECORDED_CALLER_DECLARATION")
        self.assertEqual(result["bound_observation_ids"], ["fixture-observation-001"])
        self.assertEqual(result["effect_states"], ["EFFECT_PRESENT"])
        self.assertEqual(result["observer_independence"], "ACTOR_REF_COMPARISON_ONLY")
        self.assertEqual(result["outcome_truth"], "NOT_ESTABLISHED")
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["referenced_bytes_read"])

    def test_unknown_observation_is_preserved_alongside_a_known_declaration(self) -> None:
        payload = self.valid_input()
        unknown = copy.deepcopy(payload["observations"][0])
        unknown["observation_id"] = "fixture-observation-unknown"
        unknown["effect_state"] = "UNKNOWN"
        payload["observations"].append(unknown)
        result = tool.evaluate(payload)
        self.assertEqual(result["outcome_status"], "OUTCOME_WITH_UNRESOLVED_OBSERVATION")
        self.assertEqual(result["effect_states"], ["EFFECT_PRESENT", "UNKNOWN"])

    def test_each_identity_and_digest_mismatch_is_reported(self) -> None:
        mutations = (
            ("run_id", "different-run", "OBSERVATION_RUN_ID_MISMATCH"),
            ("tool_id", "different.tool", "OBSERVATION_TOOL_ID_MISMATCH"),
            ("tool_version", "9.9.9", "OBSERVATION_TOOL_VERSION_MISMATCH"),
            ("source_sha256", "e" * 64, "OBSERVATION_SOURCE_DIGEST_MISMATCH"),
            ("input_sha256", "e" * 64, "OBSERVATION_INPUT_DIGEST_MISMATCH"),
            ("output_sha256", "e" * 64, "OBSERVATION_OUTPUT_DIGEST_MISMATCH"),
            ("environment_ref", "other-environment", "OBSERVATION_ENVIRONMENT_MISMATCH"),
        )
        for field, value, expected_code in mutations:
            with self.subTest(field=field):
                payload = self.valid_input()
                payload["observations"][0][field] = value
                result = tool.evaluate(payload)
                self.assertIn(expected_code, self.codes(result))
                self.assertEqual(result["outcome_status"], "BINDING_OR_COMPLETENESS_FINDINGS")

    def test_missing_run_is_not_success_and_cannot_carry_observations(self) -> None:
        payload = self.valid_input()
        payload["execution"] = {
            "status": "NOT_RUN", "run_id": None, "tool_id": None, "tool_version": None,
            "source_sha256": None, "input_sha256": None, "output_sha256": None, "environment_ref": None,
            "executor_actor_ref": None, "started_at_utc": None, "completed_at_utc": None, "exit_code": None,
        }
        payload["observations"] = []
        self.assertEqual(tool.evaluate(payload)["outcome_status"], "NO_RUN_RECORDED")
        payload["observations"] = self.valid_input()["observations"]
        self.assertIn("OBSERVATION_WITHOUT_RECORDED_RUN", self.codes(tool.evaluate(payload)))

    def test_local_path_recheck_reads_hash_only_and_compares_declared_baseline(self) -> None:
        payload = self.valid_input()
        relative = "ignition/tests/fixtures/toolbox-execution-effect-receipt/valid-effect-r0.json"
        actual_sha = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        payload["repository_paths"] = [{
            "path": relative,
            "baseline_state": "PRESENT",
            "baseline_sha256": actual_sha,
        }]
        unchanged = tool.evaluate(payload)
        self.assertEqual(unchanged["repository_effect_status"], "NO_DIFFERENCE_FROM_DECLARED_BASELINE_OBSERVED")
        self.assertEqual(unchanged["repository_state_observations"][0]["sha256"], actual_sha)
        self.assertEqual(unchanged["repository_state_observations"][0]["change"], "UNCHANGED")
        self.assertNotIn("contents", unchanged["repository_state_observations"][0])
        self.assertEqual(unchanged["repository_bytes_read"], FIXTURE.stat().st_size)

        payload["repository_paths"][0]["baseline_sha256"] = "f" * 64
        changed = tool.evaluate(payload)
        self.assertEqual(changed["repository_effect_status"], "DIFFERENCE_FROM_DECLARED_BASELINE_OBSERVED")
        self.assertEqual(changed["repository_state_observations"][0]["change"], "CHANGED")

    def test_local_path_recheck_distinguishes_absence_and_rejects_symlinks(self) -> None:
        payload = self.valid_input()
        missing_path = "ignition/tests/fixtures/toolbox-execution-effect-receipt/absent-r0.json"
        payload["repository_paths"] = [{
            "path": missing_path,
            "baseline_state": "MISSING",
            "baseline_sha256": None,
        }]
        absent = tool.evaluate(payload)
        self.assertEqual(absent["repository_state_observations"][0]["state"], "MISSING")
        self.assertEqual(absent["repository_state_observations"][0]["change"], "UNCHANGED")

        link = FIXTURE.parent / ".effect-receipt-test-link"
        self.assertFalse(link.exists())
        try:
            os.symlink(FIXTURE, link)
            payload["repository_paths"] = [{
                "path": "ignition/tests/fixtures/toolbox-execution-effect-receipt/.effect-receipt-test-link",
                "baseline_state": "MISSING",
                "baseline_sha256": None,
            }]
            result = tool.evaluate(payload)
            self.assertEqual(result["repository_state_observations"][0]["state"], "SYMLINK")
            self.assertIn("REPOSITORY_PATH_OBSERVATION_INCOMPLETE", self.codes(result))
        finally:
            if link.is_symlink():
                link.unlink()

    def test_repository_recheck_requires_a_completed_run_and_rejects_path_traversal(self) -> None:
        payload = self.valid_input()
        payload["repository_paths"] = [{
            "path": "ignition/tests/fixtures/toolbox-execution-effect-receipt/valid-effect-r0.json",
            "baseline_state": "MISSING",
            "baseline_sha256": None,
        }]
        payload["execution"]["status"] = "STARTED"
        result = tool.evaluate(payload)
        self.assertIn("REPOSITORY_OBSERVATION_WITHOUT_COMPLETED_RUN", self.codes(result))
        self.assertEqual(result["repository_state_observations"], [])
        self.assertEqual(result["repository_bytes_read"], 0)

        payload = self.valid_input()
        payload["repository_paths"] = [{
            "path": "ignition/../README.md",
            "baseline_state": "MISSING",
            "baseline_sha256": None,
        }]
        with self.assertRaises(tool.InputError):
            tool.evaluate(payload)

    def test_same_actor_is_labeled_as_self_report(self) -> None:
        payload = self.valid_input()
        payload["observations"][0]["observer_actor_ref"] = payload["execution"]["executor_actor_ref"]
        result = tool.evaluate(payload)
        self.assertIn("OBSERVER_IS_EXECUTOR_SELF_REPORT", {row["code"] for row in result["warnings"]})
        self.assertEqual(result["observer_independence"], "ACTOR_REF_COMPARISON_ONLY")

    def test_observation_before_completion_does_not_bind(self) -> None:
        payload = self.valid_input()
        payload["observations"][0]["observed_at_utc"] = "2026-10-27T01:00:00Z"
        result = tool.evaluate(payload)
        self.assertIn("OBSERVATION_PRECEDES_COMPLETION", self.codes(result))
        self.assertEqual(result["bound_observation_ids"], [])

    def test_contradictory_observations_are_not_resolved_by_order(self) -> None:
        payload = self.valid_input()
        second = copy.deepcopy(payload["observations"][0])
        second["observation_id"] = "fixture-observation-002"
        second["effect_state"] = "NO_EFFECT_OBSERVED"
        payload["observations"].append(second)
        self.assertIn("CONTRADICTORY_EFFECT_OBSERVATIONS", self.codes(tool.evaluate(payload)))

    def test_nonzero_run_without_preserved_first_failure_remains_incomplete(self) -> None:
        payload = self.valid_input()
        payload["execution"]["exit_code"] = 2
        result = tool.evaluate(payload)
        self.assertIn("FAILURE_EVIDENCE_NOT_PRESERVED", self.codes(result))
        self.assertFalse(result["failure_preservation_declared"])

    def test_matching_failure_record_preserves_failure_without_marking_success(self) -> None:
        payload = self.valid_input()
        payload["execution"]["exit_code"] = 2
        failure = copy.deepcopy(payload["observations"][0])
        failure.update({
            "observation_id": "failure-record-001",
            "kind": "FAILURE_RECORD",
            "effect_state": None,
            "failure_record_ref": "fixture://failure/001",
            "failure_record_sha256": "e" * 64,
            "first_failure_preserved": True,
        })
        payload["observations"] = [failure]
        result = tool.evaluate(payload)
        self.assertEqual(result["findings"], [])
        self.assertTrue(result["failure_preservation_declared"])
        self.assertEqual(result["outcome_status"], "OUTCOME_UNKNOWN")

    def test_input_and_output_schemas_validate_contracts(self) -> None:
        input_schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(input_schema)
        Draft202012Validator.check_schema(output_schema)
        Draft202012Validator(input_schema).validate(self.valid_input())
        output = tool.evaluate(self.valid_input())
        Draft202012Validator(output_schema).validate({
            **output,
            "input_sha256": "a" * 64,
            "tool_source_sha256": "b" * 64,
        })

    def test_same_task_receipt_is_distinct_from_adjacent_incumbent_contracts(self) -> None:
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-execution-effect-receipt-real-task-r0.json")
            .read_text(encoding="utf-8")
        )
        payload = evidence["receipt_input"]

        candidate_result = tool.evaluate(payload)
        episode_result = portable_episode.validate_episode(payload)
        self.assertEqual(candidate_result["outcome_status"], "OUTCOME_RECORDED_CALLER_DECLARATION")
        self.assertEqual(episode_result["status"], "EPISODE_MANIFEST_INVALID")
        with self.assertRaises(actions_attribution.InputError) as action_error:
            actions_attribution.attribute_validation_evidence(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            )
        self.assertIn("unsupported fields", str(action_error.exception))
        with self.assertRaises(failure_recovery.InputError) as recovery_error:
            failure_recovery.evaluate(payload)
        self.assertEqual(str(recovery_error.exception), "INPUT_SCHEMA_INVALID")

    def test_duplicate_json_keys_and_oversized_input_fail_closed(self) -> None:
        duplicate = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=b'{"schema_version":"a","schema_version":"b"}',
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        self.assertEqual(duplicate.returncode, 2)
        self.assertEqual(json.loads(duplicate.stderr)["error"], "DUPLICATE_JSON_KEY")
        oversized = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=b" " * (tool.MAX_INPUT_BYTES + 1),
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        self.assertEqual(oversized.returncode, 2)
        self.assertEqual(json.loads(oversized.stderr)["error"], "INPUT_TOO_LARGE")

    def test_cli_emits_bound_hashes_and_never_authorizes_execution(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=FIXTURE.read_bytes(),
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        result = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(result["outcome_status"], "OUTCOME_RECORDED_CALLER_DECLARATION")
        self.assertEqual(len(result["input_sha256"]), 64)
        self.assertEqual(len(result["tool_source_sha256"]), 64)
        self.assertFalse(result["execution_authorized"])
        Draft202012Validator(json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))).validate(result)


if __name__ == "__main__":
    unittest.main()
