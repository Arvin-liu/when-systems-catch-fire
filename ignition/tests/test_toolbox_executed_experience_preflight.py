from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


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
        observation["failure_record_ref"] = "stderr:sha256/" + "a" * 64
        observation["failure_record_sha256"] = "a" * 64
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


if __name__ == "__main__":
    unittest.main()
