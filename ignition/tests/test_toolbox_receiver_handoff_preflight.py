from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))
sys.path.insert(0, str(IGNITION_ROOT / "tools"))

from agent_federation import ArtifactRef, HandoffEligibility, build_handoff_bundle  # noqa: E402
from agent_federation.contracts import FederatedResultReceipt  # noqa: E402
from toolbox_receiver_handoff_preflight import evaluate  # noqa: E402


TOOL_PATH = IGNITION_ROOT / "tools/toolbox_receiver_handoff_preflight.py"


def make_receipt(*, eligible: bool = True) -> FederatedResultReceipt:
    return FederatedResultReceipt.build(
        federation_task_id="handoff-task-001",
        executor_id="external.codex",
        terminal_state="COMPLETED_VALIDATED",
        claimed_actions=("read manifest",),
        artifact_refs=(ArtifactRef("fixture/manifest.json", "a" * 64, "manifest"),),
        validation_refs=("validator/manifest-v1",),
        external_session_ref=None,
        executor_telemetry={"transport": "test", "event_count": 1},
        unresolveds=(),
        handoff_eligibility=HandoffEligibility(eligible, "controlled handoff test"),
    )


def make_document(*, receipt: FederatedResultReceipt | None = None) -> dict:
    receipt = receipt or make_receipt()
    bundle = build_handoff_bundle(
        handoff_id="handoff-001",
        source_receipt=receipt,
        goal="Continue the bounded manifest task",
        pending_work=("re-observe the manifest",),
        allowed_capabilities=("repo.read",),
        workspace_refs=("fixture/",),
        acceptance_criteria=("source binding is checked",),
    )
    return {
        "schema_version": "receiver-handoff-preflight-r0",
        "source_receipt": receipt.to_dict(),
        "handoff_bundle": bundle.to_dict(),
        "target_executor_id": "external.hermes",
        "target_capabilities": ["repo.read"],
        "workspace_reobserved": True,
        "observed_artifact_refs": ["fixture/manifest.json"],
    }


class ReceiverHandoffPreflightTests(unittest.TestCase):
    def test_matching_receipt_bundle_and_receiver_return_no_authority_preflight(self) -> None:
        result, code = evaluate(make_document())
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "PREFLIGHT_READY_NO_AUTHORITY")
        self.assertEqual(result["checks"]["handoff_bundle_binding"], "PASS")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["receipt_authenticity"], "NOT_ESTABLISHED_UNKEYED_DIGEST")

    def test_source_artifact_substitution_is_rejected_before_takeover(self) -> None:
        document = make_document()
        document["handoff_bundle"]["artifact_refs"] = [{
            "ref": "fixture/other.json",
            "sha256": "b" * 64,
            "kind": "manifest",
        }]
        document["observed_artifact_refs"] = ["fixture/other.json"]
        result, code = evaluate(document)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "SOURCE_RECEIPT_BUNDLE_MISMATCH")
        self.assertIn("HANDOFF_NOT_SOURCE_RECEIPT_PROJECTION", {row["code"] for row in result["findings"]})
        self.assertEqual(result["checks"]["receiver_capability_and_reobservation"], "NOT_RUN")

    def test_valid_bundle_with_insufficient_receiver_capability_is_blocked(self) -> None:
        document = make_document()
        document["target_capabilities"] = ["long_task"]
        result, code = evaluate(document)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "CAPABILITY_MISMATCH")
        self.assertFalse(result["execution_authorized"])

    def test_valid_bundle_without_reobservation_requires_reconciliation(self) -> None:
        document = make_document()
        document["workspace_reobserved"] = False
        result, code = evaluate(document)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "REQUIRES_RECONCILIATION")
        self.assertEqual(result["workspace_reobservation"], "NOT_ASSERTED")

    def test_handoff_ineligible_receipt_is_not_accepted_as_receiver_ready(self) -> None:
        result, code = evaluate(make_document(receipt=make_receipt(eligible=False)))
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "HANDOFF_NOT_ELIGIBLE")

    def test_bad_source_receipt_digest_fails_closed(self) -> None:
        document = make_document()
        document["source_receipt"]["receipt_digest"] = "0" * 64
        result, code = evaluate(document)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "INPUT_INVALID")
        self.assertEqual(result["findings"][0]["code"], "SOURCE_RECEIPT_INVALID")

    def test_duplicate_json_keys_and_oversize_stdin_fail_closed(self) -> None:
        fixture = IGNITION_ROOT / "tests/fixtures/toolbox-receiver-handoff-preflight/valid-input-r0.json"
        smoke = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=fixture.read_text(encoding="utf-8"),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(smoke.returncode, 0, smoke.stderr)
        self.assertEqual(json.loads(smoke.stdout)["status"], "PREFLIGHT_READY_NO_AUTHORITY")

        duplicate = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input='{"schema_version":"x","schema_version":"y"}',
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(duplicate.returncode, 2)
        self.assertEqual(json.loads(duplicate.stdout)["findings"][0]["code"], "DUPLICATE_JSON_KEY")

        oversized = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=" " * 262_145,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(oversized.returncode, 2)
        self.assertEqual(json.loads(oversized.stdout)["status"], "INPUT_INVALID")


if __name__ == "__main__":
    unittest.main()
