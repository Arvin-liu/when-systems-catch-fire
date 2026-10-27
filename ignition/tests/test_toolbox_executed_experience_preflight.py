from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_executed_experience_preflight as tool  # noqa: E402


REAL_ARTIFACT = json.loads(
    (IGNITION_ROOT / "data/operations/toolbox-execution-effect-receipt-real-task-r0.json").read_text(encoding="utf-8")
)
RUN = REAL_ARTIFACT["receipt_input"]["execution"]
NOW = "2026-10-27T15:00:00Z"


def artifact_bytes(effect_state: str = "EFFECT_PRESENT", *, preserve_failure: bool = False) -> bytes:
    artifact = copy.deepcopy(REAL_ARTIFACT)
    artifact["receipt_input"]["observations"][0]["effect_state"] = effect_state
    if preserve_failure:
        observation = artifact["receipt_input"]["observations"][0]
        failure_sha256 = hashlib.sha256(b"preserved test failure evidence\n").hexdigest()
        observation["failure_record_ref"] = "stderr:sha256/" + failure_sha256
        observation["failure_record_sha256"] = failure_sha256
        observation["first_failure_preserved"] = "declared local failure excerpt"
    artifact["receipt_output"]["effect_states"] = [effect_state]
    artifact["receipt_output"]["failure_preservation_declared"] = preserve_failure
    encoded_input = json.dumps(artifact["receipt_input"], ensure_ascii=False, separators=(",", ":")).encode()
    artifact["receipt_input_sha256"] = hashlib.sha256(encoded_input).hexdigest()
    artifact["receipt_output"]["input_sha256"] = artifact["receipt_input_sha256"]
    return json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def request(root: Path, *, outcome: str = "EFFECT_PRESENT", path: str = "ignition/receipt.json", expires: str = "2026-10-28T00:00:00Z") -> dict:
    artifact_path = root / path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    if not artifact_path.exists():
        artifact_path.write_bytes(artifact_bytes(outcome, preserve_failure=outcome == "EFFECT_ABSENT"))
    raw = artifact_path.read_bytes()
    return {
        "schema_version": "toolbox-executed-experience-preflight-r0",
        "evaluated_at_utc": NOW,
        "task": {
            "task_id": "same-task-replay",
            "task_family": "validation-target-coverage",
            "environment_ref": RUN["environment_ref"],
            "source_scope_id": "repo:formal-ignition",
        },
        "experiences": [
            {
                "experience_id": "exp-one",
                "task_family": "validation-target-coverage",
                "environment_ref": RUN["environment_ref"],
                "source_scope_id": "repo:formal-ignition",
                "task_ref": REAL_ARTIFACT["task_ref"],
                "tool_id": RUN["tool_id"],
                "tool_version": RUN["tool_version"],
                "source_sha256": RUN["source_sha256"],
                "outcome_claim": outcome,
                "expires_at_utc": expires,
                "evidence_artifact": {"path": path, "sha256": hashlib.sha256(raw).hexdigest()},
            }
        ],
    }


def request_r1(root: Path, *, outcome: str = "EFFECT_PRESENT", path: str = "ignition/receipt-r1.json") -> dict:
    payload = request(root, outcome=outcome, path=path)
    payload["schema_version"] = "toolbox-executed-experience-preflight-r1"
    receipt_path = root / path
    raw_receipt = artifact_bytes(outcome, preserve_failure=outcome == "EFFECT_ABSENT")
    receipt_path.write_bytes(raw_receipt)
    experience = payload["experiences"][0]
    experience["evidence_artifact"]["sha256"] = hashlib.sha256(raw_receipt).hexdigest()

    source = IGNITION_ROOT / "tools/toolbox_actions_validation_target_coverage.py"
    input_artifact = IGNITION_ROOT / "tests/fixtures/toolbox-actions-validation-target-coverage/pr264-four-runs-r0.json"
    output_artifact = IGNITION_ROOT / "data/operations/toolbox-actions-validation-target-coverage-replay-output-20261027-r0.json"
    raw_bindings = {
        "source": ("ignition/tools/toolbox_actions_validation_target_coverage.py", source.read_bytes()),
        "input": ("ignition/tests/fixtures/toolbox-actions-validation-target-coverage/pr264-four-runs-r0.json", input_artifact.read_bytes()),
        "output": ("ignition/data/operations/toolbox-actions-validation-target-coverage-replay-output-20261027-r0.json", output_artifact.read_bytes()),
    }
    bindings = {}
    for role, (relative_path, raw) in raw_bindings.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        bindings[role] = {"path": relative_path, "sha256": hashlib.sha256(raw).hexdigest()}
    if outcome == "EFFECT_ABSENT":
        failure_path = "ignition/r1-artifacts/failure.log"
        failure_raw = b"preserved test failure evidence\n"
        target = root / failure_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(failure_raw)
        bindings["failure"] = {"path": failure_path, "sha256": hashlib.sha256(failure_raw).hexdigest()}
    experience["artifact_bindings"] = bindings
    return payload


class ExecutedExperiencePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(__file__).resolve().parents[1] / "tests" / ".tmp-experience-preflight"
        if self.temp_root.exists():
            import shutil
            shutil.rmtree(self.temp_root)
        (self.temp_root / "ignition").mkdir(parents=True)
        self.request = request(self.temp_root)

    def tearDown(self) -> None:
        import shutil
        if self.temp_root.exists():
            shutil.rmtree(self.temp_root)

    def run_request(self, payload: dict | None = None) -> dict:
        with patch.object(tool, "REPO_ROOT", self.temp_root):
            return tool.evaluate(payload or self.request)

    def test_exact_scope_effect_receipt_is_only_an_optional_reference(self):
        result = self.run_request()
        decision = result["experience_decisions"][0]
        self.assertEqual(decision["decision"], "OPTIONAL_REFERENCE_ONLY")
        self.assertEqual(decision["evidence_status"], "LOCAL_BYTES_MATCH")
        self.assertFalse(decision["can_execute"])
        self.assertFalse(result["reuse_authorized"])
        self.assertFalse(result["execution_authorized"])

    def test_preserved_negative_effect_remains_a_counterexample(self):
        payload = request(self.temp_root, outcome="EFFECT_ABSENT", path="ignition/negative.json")
        result = self.run_request(payload)
        self.assertEqual(result["experience_decisions"][0]["decision"], "COUNTEREXAMPLE_ONLY")

    def test_unpreserved_negative_effect_requires_review(self):
        payload = request(self.temp_root, outcome="EFFECT_ABSENT", path="ignition/unpreserved.json")
        raw = artifact_bytes("EFFECT_ABSENT", preserve_failure=False)
        (self.temp_root / "ignition/unpreserved.json").write_bytes(raw)
        payload["experiences"][0]["evidence_artifact"]["sha256"] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(self.run_request(payload)["experience_decisions"][0]["reason"], "NEGATIVE_EFFECT_WITHOUT_PRESERVED_FAILURE")

    def test_different_environment_is_review_only(self):
        payload = copy.deepcopy(self.request)
        payload["task"]["environment_ref"] = "different-runtime"
        result = self.run_request(payload)
        self.assertEqual(result["experience_decisions"][0]["decision"], "REVIEW_REQUIRED")
        self.assertEqual(result["experience_decisions"][0]["reason"], "TRANSFER_SCOPE_DIFFERS")

    def test_expired_experience_is_withheld_before_read(self):
        payload = request(self.temp_root, path="ignition/missing.json", expires="2026-10-27T15:00:00Z")
        (self.temp_root / "ignition/missing.json").unlink()
        result = self.run_request(payload)
        self.assertEqual(result["experience_decisions"][0]["reason"], "EXPIRED_BEFORE_EVIDENCE_READ")
        self.assertEqual(result["experience_decisions"][0]["evidence_status"], "NOT_READ_EXPIRED")

    def test_wrong_artifact_digest_is_withheld(self):
        payload = copy.deepcopy(self.request)
        payload["experiences"][0]["evidence_artifact"]["sha256"] = "0" * 64
        result = self.run_request(payload)
        self.assertEqual(result["experience_decisions"][0]["reason"], "EVIDENCE_DIGEST_MISMATCH")

    def test_path_traversal_is_withheld(self):
        payload = copy.deepcopy(self.request)
        payload["experiences"][0]["evidence_artifact"]["path"] = "ignition/../outside.json"
        with self.assertRaises(tool.ExperienceError):
            self.run_request(payload)

    def test_r1_exact_artifact_bytes_match_and_still_do_not_authorize(self):
        payload = request_r1(self.temp_root)
        result = self.run_request(payload)
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-executed-experience-result-r1.schema.json").read_text())
        Draft202012Validator(schema).validate(result)
        decision = result["experience_decisions"][0]
        self.assertEqual(result["tool_version"], "0.2.0")
        self.assertEqual(decision["decision"], "OPTIONAL_REFERENCE_ONLY")
        self.assertEqual(decision["artifact_binding_status"], {
            "source": "MATCHED", "input": "MATCHED", "output": "MATCHED", "failure": "NOT_REQUIRED",
        })
        self.assertGreater(result["artifact_bytes_read"], 0)
        self.assertEqual(result["artifact_read_budget_bytes"], tool.MAX_R1_READ_BYTES)
        self.assertFalse(result["reuse_authorized"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(decision["can_execute"])
        self.assertFalse(decision["can_authorize"])

    def test_r1_mismatched_source_input_or_output_bytes_are_withheld(self):
        for role in ("source", "input", "output"):
            with self.subTest(role=role):
                payload = request_r1(self.temp_root, path=f"ignition/receipt-{role}.json")
                binding = payload["experiences"][0]["artifact_bindings"][role]
                artifact_path = self.temp_root / binding["path"]
                artifact_path.write_bytes(artifact_path.read_bytes() + b"tampered")
                decision = self.run_request(payload)["experience_decisions"][0]
                self.assertEqual(decision["decision"], "WITHHOLD")
                self.assertEqual(decision["artifact_binding_status"][role], "DIGEST_MISMATCH")
                self.assertEqual(decision["reason"], f"ARTIFACT_{role.upper()}_DIGEST_MISMATCH")

    def test_r1_missing_output_bytes_are_withheld(self):
        payload = request_r1(self.temp_root)
        output_path = self.temp_root / payload["experiences"][0]["artifact_bindings"]["output"]["path"]
        output_path.unlink()
        decision = self.run_request(payload)["experience_decisions"][0]
        self.assertEqual(decision["decision"], "WITHHOLD")
        self.assertEqual(decision["artifact_binding_status"]["output"], "MISSING")
        self.assertEqual(decision["reason"], "ARTIFACT_OUTPUT_MISSING")

    def test_r1_source_path_must_be_the_receipt_observed_path(self):
        payload = request_r1(self.temp_root)
        original = payload["experiences"][0]["artifact_bindings"]["source"]
        alternate = "ignition/data/operations/alternate-source-copy.py"
        alternate_path = self.temp_root / alternate
        alternate_path.parent.mkdir(parents=True, exist_ok=True)
        alternate_path.write_bytes((self.temp_root / original["path"]).read_bytes())
        original["path"] = alternate
        decision = self.run_request(payload)["experience_decisions"][0]
        self.assertEqual(decision["decision"], "WITHHOLD")
        self.assertEqual(decision["reason"], "SOURCE_PATH_NOT_BOUND_TO_RECEIPT")
        self.assertEqual(decision["artifact_binding_status"]["source"], "RECEIPT_BINDING_MISMATCH")

    def test_r1_observation_hashes_must_match_the_execution_record(self):
        payload = request_r1(self.temp_root)
        experience = payload["experiences"][0]
        receipt_path = self.temp_root / experience["evidence_artifact"]["path"]
        receipt = copy.deepcopy(REAL_ARTIFACT)
        receipt["receipt_input"]["observations"][0]["source_sha256"] = "0" * 64
        encoded_input = json.dumps(receipt["receipt_input"], ensure_ascii=False, separators=(",", ":")).encode()
        receipt["receipt_input_sha256"] = hashlib.sha256(encoded_input).hexdigest()
        receipt["receipt_output"]["input_sha256"] = receipt["receipt_input_sha256"]
        raw = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        receipt_path.write_bytes(raw)
        experience["evidence_artifact"]["sha256"] = hashlib.sha256(raw).hexdigest()
        decision = self.run_request(payload)["experience_decisions"][0]
        self.assertEqual(decision["decision"], "WITHHOLD")
        self.assertEqual(decision["reason"], "RECEIPT_OBSERVATION_BINDING_INVALID")

    def test_r1_declared_artifact_digest_mismatch_stops_before_artifact_reads(self):
        payload = request_r1(self.temp_root)
        payload["experiences"][0]["artifact_bindings"]["input"]["sha256"] = "0" * 64
        with patch.object(tool, "_read_repo_artifact", wraps=tool._read_repo_artifact) as read_artifact:
            decision = self.run_request(payload)["experience_decisions"][0]
        self.assertEqual(read_artifact.call_count, 1)
        self.assertEqual(decision["decision"], "WITHHOLD")
        self.assertEqual(decision["reason"], "ARTIFACT_DECLARATION_MISMATCH")

    def test_r1_scope_and_expiry_mismatches_happen_before_any_artifact_read(self):
        scoped = request_r1(self.temp_root, path="ignition/receipt-scope.json")
        scoped["task"]["source_scope_id"] = "another-scope"
        with patch.object(tool, "_read_repo_artifact") as read_artifact:
            decision = self.run_request(scoped)["experience_decisions"][0]
        read_artifact.assert_not_called()
        self.assertEqual(decision["reason"], "TRANSFER_SCOPE_DIFFERS")

        expired = request_r1(self.temp_root, path="ignition/receipt-expired-r1.json")
        expired["experiences"][0]["expires_at_utc"] = NOW
        with patch.object(tool, "_read_repo_artifact") as read_artifact:
            decision = self.run_request(expired)["experience_decisions"][0]
        read_artifact.assert_not_called()
        self.assertEqual(decision["reason"], "EXPIRED_BEFORE_EVIDENCE_READ")

    def test_r1_traversal_and_symlink_bindings_fail_closed(self):
        traversal = request_r1(self.temp_root, path="ignition/receipt-traversal.json")
        traversal["experiences"][0]["artifact_bindings"]["output"]["path"] = "ignition/../outside.json"
        with self.assertRaises(tool.ExperienceError):
            self.run_request(traversal)

        symlinked = request_r1(self.temp_root, path="ignition/receipt-symlink.json")
        card = symlinked["experiences"][0]
        link_path = self.temp_root / "ignition/r1-artifacts/output-link.json"
        target_path = self.temp_root / card["artifact_bindings"]["output"]["path"]
        link_path.parent.mkdir(parents=True, exist_ok=True)
        link_path.symlink_to(target_path)
        card["artifact_bindings"]["output"]["path"] = "ignition/r1-artifacts/output-link.json"
        decision = self.run_request(symlinked)["experience_decisions"][0]
        self.assertEqual(decision["decision"], "WITHHOLD")
        self.assertEqual(decision["artifact_binding_status"]["output"], "PATH_REJECTED")

    def test_r1_preserved_failure_requires_and_verifies_failure_bytes(self):
        payload = request_r1(self.temp_root, outcome="EFFECT_ABSENT", path="ignition/receipt-negative-r1.json")
        decision = self.run_request(payload)["experience_decisions"][0]
        self.assertEqual(decision["decision"], "COUNTEREXAMPLE_ONLY")
        self.assertEqual(decision["artifact_binding_status"]["failure"], "MATCHED")

        binding = payload["experiences"][0]["artifact_bindings"]["failure"]
        (self.temp_root / binding["path"]).write_bytes(b"different failure bytes\n")
        decision = self.run_request(payload)["experience_decisions"][0]
        self.assertEqual(decision["decision"], "WITHHOLD")
        self.assertEqual(decision["artifact_binding_status"]["failure"], "DIGEST_MISMATCH")

    def test_r1_enforces_aggregate_read_budget(self):
        payload = request_r1(self.temp_root, path="ignition/receipt-budget.json")
        base = payload["experiences"][0]
        payload["experiences"] = []
        for index in range(10):
            duplicate = copy.deepcopy(base)
            duplicate["experience_id"] = f"budget-{index}"
            payload["experiences"].append(duplicate)
        result = self.run_request(payload)
        self.assertLessEqual(result["artifact_bytes_read"], tool.MAX_R1_READ_BYTES)
        self.assertEqual(result["experience_decisions"][-1]["decision"], "WITHHOLD")
        self.assertEqual(result["experience_decisions"][-1]["reason"], "ARTIFACT_INPUT_BUDGET_EXHAUSTED")


if __name__ == "__main__":
    unittest.main()
