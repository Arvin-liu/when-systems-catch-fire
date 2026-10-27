from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_execution_state_lineage as tool  # noqa: E402
from agent_kernel.contracts import Checkpoint, Handoff, ResumeCapsule, validate_resume_lineage  # noqa: E402


FIXTURES = IGNITION_ROOT / "tests/fixtures/toolbox-execution-state-lineage"
OUTPUT_SCHEMA = json.loads(
    (IGNITION_ROOT / "schemas/operations/toolbox-execution-state-lineage-output-r0.schema.json").read_text(encoding="utf-8")
)


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def raw(document: dict) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def make_checkpoint(checkpoint_id: str, parent_id: str | None, digest: str) -> Checkpoint:
    return Checkpoint(
        checkpoint_id=checkpoint_id,
        run_id="run-1",
        phase="CONTINUE",
        state_ref=f"state://{checkpoint_id}",
        state_sha256=digest,
        event_count=3,
        created_by="executor-a",
        parent_checkpoint_id=parent_id,
        reason_summary="synthetic matched comparison",
    )


def make_capsule(checkpoint: Checkpoint, capsule_id: str, to_executor: str) -> ResumeCapsule:
    return ResumeCapsule(
        capsule_id=capsule_id,
        run_id=checkpoint.run_id,
        checkpoint_id=checkpoint.checkpoint_id,
        state_ref=checkpoint.state_ref,
        state_sha256=checkpoint.state_sha256,
        pending_action_ids=(),
        required_capabilities=(),
        created_by="executor-a",
        handoff=Handoff("executor-a", to_executor, "synthetic resume", checkpoint.state_ref),
    )


class ExecutionStateLineageTests(unittest.TestCase):
    def assert_output_schema(self, output: dict) -> None:
        self.assertEqual(list(Draft202012Validator(OUTPUT_SCHEMA).iter_errors(output)), [])

    def test_valid_branch_projection_returns_one_active_path_and_preserves_alternative(self) -> None:
        output = tool.analyze(raw(load_fixture("valid-two-branch-r0.json")))

        self.assertEqual(output["status"], "PASS")
        self.assertEqual(output["active_path_checkpoint_ids"], ["cp-root", "cp-active"])
        self.assertEqual(output["leaf_checkpoint_ids"], ["cp-active", "cp-alternative"])
        self.assertEqual(output["expected_inactive_tip_checkpoint_ids"], ["cp-alternative"])
        self.assertEqual(output["branch_points"], [{
            "parent_checkpoint_id": "cp-root",
            "child_checkpoint_ids": ["cp-active", "cp-alternative"],
        }])
        self.assertFalse(output["caller_declarations_authenticated"])
        self.assertFalse(output["checkpoint_state_bytes_read"])
        self.assertFalse(output["execution_authorized"])
        self.assertEqual(output["network_calls"], 0)
        self.assertFalse(output["write_effects"])
        self.assert_output_schema(output)

    def test_unaccounted_inactive_branch_fails_closed(self) -> None:
        output = tool.analyze((FIXTURES / "unaccounted-inactive-tip-r0.json").read_bytes())
        self.assertEqual(output["status"], "FAIL")
        self.assertIn("INACTIVE_TIP_ACCOUNTING_MISMATCH", [row["code"] for row in output["findings"]])
        self.assert_output_schema(output)

    def test_non_leaf_active_checkpoint_and_declared_path_mismatch_are_findings(self) -> None:
        document = load_fixture("valid-two-branch-r0.json")
        document["active_checkpoint_id"] = "cp-root"
        document["declared_active_path_checkpoint_ids"] = ["cp-root"]
        output = tool.analyze(raw(document))
        codes = {row["code"] for row in output["findings"]}
        self.assertIn("ACTIVE_CHECKPOINT_NOT_LEAF", codes)
        self.assertIn("INACTIVE_TIP_ACCOUNTING_MISMATCH", codes)
        self.assert_output_schema(output)

    def test_resume_capsule_must_match_checkpoint_binding_and_change_executor(self) -> None:
        document = load_fixture("valid-two-branch-r0.json")
        capsule = document["resume_capsules"][0]
        capsule["state_sha256"] = "f" * 64
        capsule["from_executor_id"] = "executor-b"
        capsule["to_executor_id"] = "executor-b"
        output = tool.analyze(raw(document))
        codes = {row["code"] for row in output["findings"]}
        self.assertIn("RESUME_STATE_DIGEST_MISMATCH", codes)
        self.assertIn("RESUME_EXECUTOR_NOT_CHANGED", codes)

    def test_rollback_target_must_be_a_strict_ancestor(self) -> None:
        document = load_fixture("valid-two-branch-r0.json")
        document["rollback_records"][0]["to_checkpoint_id"] = "cp-alternative"
        output = tool.analyze(raw(document))
        self.assertIn("ROLLBACK_TARGET_NOT_ANCESTOR", [row["code"] for row in output["findings"]])

    def test_unknown_parent_and_cycle_are_reported(self) -> None:
        document = load_fixture("valid-two-branch-r0.json")
        document["checkpoints"][0]["parent_checkpoint_id"] = "missing"
        output = tool.analyze(raw(document))
        self.assertIn("PARENT_CHECKPOINT_UNKNOWN", [row["code"] for row in output["findings"]])

        document = load_fixture("valid-two-branch-r0.json")
        document["checkpoints"][0]["parent_checkpoint_id"] = "cp-active"
        output = tool.analyze(raw(document))
        self.assertIn("CHECKPOINT_PARENT_CYCLE", [row["code"] for row in output["findings"]])

    def test_parent_and_child_must_belong_to_the_same_run(self) -> None:
        document = load_fixture("valid-two-branch-r0.json")
        document["checkpoints"][1]["run_id"] = "run-2"
        output = tool.analyze(raw(document))
        self.assertIn("PARENT_RUN_ID_MISMATCH", [row["code"] for row in output["findings"]])

    def test_kernel_pairwise_resume_passes_both_siblings_but_lineage_audit_requires_tip_accounting(self) -> None:
        active = make_checkpoint("cp-active", "cp-root", "1" * 64)
        alternative = make_checkpoint("cp-alternative", "cp-root", "2" * 64)
        validate_resume_lineage(active, make_capsule(active, "cap-active", "executor-b"), active.state_sha256, executor_id="executor-b")
        validate_resume_lineage(
            alternative,
            make_capsule(alternative, "cap-alternative", "executor-c"),
            alternative.state_sha256,
            executor_id="executor-c",
        )

        document = load_fixture("valid-two-branch-r0.json")
        document["declared_inactive_tip_checkpoint_ids"] = []
        output = tool.analyze(raw(document))
        self.assertIn("INACTIVE_TIP_ACCOUNTING_MISMATCH", [row["code"] for row in output["findings"]])
        self.assertEqual(active.parent_checkpoint_id, alternative.parent_checkpoint_id)

    def test_duplicate_json_keys_invalid_json_and_input_limit_return_machine_reports(self) -> None:
        for payload, expected in [
            (b'{"schema_version":"x","schema_version":"y"}', "INPUT_DUPLICATE_JSON_KEY"),
            (b'{"broken":', "INPUT_INVALID_JSON"),
            (b" " * (tool.MAX_INPUT_BYTES + 1), "INPUT_TOO_LARGE"),
        ]:
            output = tool.analyze(payload)
            self.assertIn(expected, [row["code"] for row in output["findings"]])
            self.assert_output_schema(output)

    def test_schema_rejects_unknown_fields_without_accessing_any_path(self) -> None:
        document = load_fixture("valid-two-branch-r0.json")
        document["write_path"] = "../../outside"
        output = tool.analyze(raw(document))
        self.assertIn("INPUT_SCHEMA_INVALID", [row["code"] for row in output["findings"]])
        self.assert_output_schema(output)

    def test_cli_matches_preserved_local_pilot_stdout_without_side_effects(self) -> None:
        input_path = IGNITION_ROOT / "data/operations/toolbox-execution-state-lineage-real-task-input-r0.json"
        expected_stdout_path = IGNITION_ROOT / "data/operations/toolbox-execution-state-lineage-real-task-cli-stdout-r1.json"
        prior_projection_path = IGNITION_ROOT / "data/operations/toolbox-execution-state-lineage-real-task-output-r0.json"
        completed = subprocess.run(
            [sys.executable, "-B", str(IGNITION_ROOT / "tools/toolbox_execution_state_lineage.py"), "--stdin"],
            input=input_path.read_bytes(),
            capture_output=True,
            cwd=IGNITION_ROOT.parent,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        self.assertEqual(completed.stdout, expected_stdout_path.read_bytes())
        output = json.loads(completed.stdout)
        self.assertEqual(output, json.loads(prior_projection_path.read_text(encoding="utf-8")))
        self.assertEqual(output["status"], "PASS")
        self.assertFalse(output["caller_declarations_authenticated"])
        self.assertFalse(output["checkpoint_state_bytes_read"])
        self.assertEqual(output["network_calls"], 0)
        self.assertFalse(output["write_effects"])
        self.assertFalse(output["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
