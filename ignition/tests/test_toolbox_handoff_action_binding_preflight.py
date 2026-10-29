from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))
sys.path.insert(0, str(IGNITION_ROOT / "tools"))

from agent_federation import ArtifactRef, ExternalSessionRef, HandoffEligibility, build_handoff_bundle  # noqa: E402
from agent_federation.contracts import ExecutorDescriptor, ExecutorHealth, FederatedResultReceipt  # noqa: E402
from agent_runtime.actions import ActionKind, ApprovalClass, ExecutionPacket, RollbackClass  # noqa: E402
from agent_runtime.control import ApprovalDecisionR1, ApprovalRequestR1, ExecutionLease  # noqa: E402
from toolbox_handoff_action_binding_preflight import evaluate  # noqa: E402


TOOL_PATH = IGNITION_ROOT / "tools/toolbox_handoff_action_binding_preflight.py"
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-handoff-action-binding-input-r0.schema.json"
OUTPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-handoff-action-binding-output-r0.schema.json"
FIXTURE_PATH = IGNITION_ROOT / "tests/fixtures/toolbox-handoff-action-binding/valid-input-r0.json"

ACTION_ID = "action-read-manifest"
ARTIFACT_REF = "fixture/manifest.json"
ARTIFACT_SHA = "a" * 64
SOURCE_REVISION = "fixture-source-revision-20261027"
TASK_STATE_REVISION = "fixture-task-state-r7"
RECEIVER_ID = "fixture.receiver"
ADAPTER_VERSION = "adapter-v1"
AUTHORIZATION_REF = "decision-fixture"


def make_receiver(*, native_resume_support: bool = False, session_kinds: tuple[str, ...] = ()) -> ExecutorDescriptor:
    return ExecutorDescriptor(
        executor_id=RECEIVER_ID,
        family="synthetic-fixture",
        version="1.0",
        transport_kind=("LOCAL_FIXTURE",),
        availability="AVAILABLE",
        health=ExecutorHealth("HEALTHY", "2026-10-27T00:00:00Z", "synthetic fixture only"),
        capability_tokens=("repo.read",),
        supported_task_granularities=("ACTION",),
        workspace_semantics="caller-declared disposable fixture",
        permission_control_semantics="not independently observed",
        structured_output_support=True,
        progress_support=False,
        cancel_support=False,
        native_resume_support=native_resume_support,
        external_session_refs=session_kinds,
        network_semantics="disabled",
        max_task_duration_seconds=30,
        adapter_version=ADAPTER_VERSION,
        limitations=("synthetic contract fixture",),
    )


def make_document(*, session_kind: str | None = None) -> dict:
    external_session = (
        ExternalSessionRef("fixture.source", "session-fixture", session_kind, "2026-10-27T00:00:00Z")
        if session_kind
        else None
    )
    receipt = FederatedResultReceipt.build(
        federation_task_id="handoff-task-fixture",
        executor_id="fixture.source",
        terminal_state="COMPLETED_VALIDATED",
        claimed_actions=("read manifest",),
        artifact_refs=(ArtifactRef(ARTIFACT_REF, ARTIFACT_SHA, "manifest"),),
        validation_refs=("fixture-validator-r0",),
        external_session_ref=external_session,
        executor_telemetry={"transport": "synthetic"},
        unresolveds=(),
        handoff_eligibility=HandoffEligibility(True, "synthetic action-binding fixture"),
    )
    bundle = build_handoff_bundle(
        handoff_id="handoff-fixture",
        source_receipt=receipt,
        goal="Read a bounded synthetic manifest",
        pending_work=(ACTION_ID,),
        allowed_capabilities=("repo.read",),
        workspace_refs=("fixture/",),
        acceptance_criteria=("preserve exact action and artifact bindings",),
    )
    payload = {
        "handoff_action_id": ACTION_ID,
        "handoff_source_revision": SOURCE_REVISION,
        "handoff_task_state_revision": TASK_STATE_REVISION,
        "handoff_authorization_ref": AUTHORIZATION_REF,
        "handoff_target_artifact_ref": ARTIFACT_REF,
        "handoff_target_artifact_sha256": ARTIFACT_SHA,
        "handoff_receiver_executor_id": RECEIVER_ID,
        "handoff_receiver_adapter_version": ADAPTER_VERSION,
    }
    packet = ExecutionPacket(
        run_id="run-handoff-fixture",
        step_id="step-read-manifest",
        action_id=ACTION_ID,
        kind=ActionKind.READ_FILE.value,
        required_capabilities=("repo.read",),
        requested_reads=(ARTIFACT_REF,),
        requested_writes=(),
        argv=(),
        approval_class=ApprovalClass.AUTO_ALLOWED_SAFE.value,
        expected_side_effects=(),
        validator_refs=("fixture-validator-r0",),
        timeout_seconds=30,
        max_output_bytes=1024,
        idempotency_key="idem-handoff-fixture",
        rollback_class=RollbackClass.NONE.value,
        reason_summary="Read one bounded synthetic manifest",
        source_plan_hash="b" * 64,
        payload=payload,
        network_requested=False,
    )
    packet_digest = packet.action_digest
    approval_request = ApprovalRequestR1(
        request_id="request-fixture",
        run_id=packet.run_id,
        action_id=packet.action_id,
        action_digest=packet_digest,
        impact_summary="Read one synthetic fixture file",
        risk_class="LOW",
        requested_capabilities=packet.required_capabilities,
        requested_reads=packet.requested_reads,
        requested_writes=packet.requested_writes,
        expires_at=4_102_444_800,
        lease_id="lease-fixture",
        status="ALLOWED",
        created_at="2026-10-27T00:00:00Z",
    )
    approval_decision = ApprovalDecisionR1(
        decision_id=AUTHORIZATION_REF,
        request_id=approval_request.request_id,
        run_id=packet.run_id,
        action_digest=packet_digest,
        decision="ALLOW",
        authority_id="synthetic-fixture-authority",
        authority_type="synthetic_pilot",
        decided_at="2026-10-27T00:00:01Z",
        reason_summary="Synthetic record for contract testing",
    )
    lease = ExecutionLease(
        lease_id="lease-fixture",
        run_id=packet.run_id,
        action_id=packet.action_id,
        idempotency_key=packet.idempotency_key,
        packet_digest=packet_digest,
        executor_class_id=RECEIVER_ID,
        executor_instance_id="fixture.receiver.instance",
        issued_at=1_700_000_000,
        expires_at=4_102_444_800,
        status="ACTIVE",
    )
    receiver = make_receiver(session_kinds=())
    return {
        "schema_version": "handoff-action-binding-preflight-r0",
        "source_receipt": receipt.to_dict(),
        "handoff_bundle": bundle.to_dict(),
        "receiver_descriptor": receiver.to_dict(),
        "execution_packet": packet.to_dict(),
        "approval_request": approval_request.to_dict(),
        "approval_decision": approval_decision.to_dict(),
        "execution_lease": lease.to_dict(),
        "expected": {
            "receiver_executor_id": RECEIVER_ID,
            "receiver_adapter_version": ADAPTER_VERSION,
            "authorization_ref": AUTHORIZATION_REF,
            "source_revision": SOURCE_REVISION,
            "target_artifact_ref": ARTIFACT_REF,
            "target_artifact_sha256": ARTIFACT_SHA,
            "task_state_revision": TASK_STATE_REVISION,
            "receiver_observed_task_state_revision": TASK_STATE_REVISION,
            "native_resume_required": False,
        },
        "workspace_reobserved": True,
        "observed_artifact_refs": [ARTIFACT_REF],
    }


class HandoffActionBindingPreflightTests(unittest.TestCase):
    def assert_output_schema(self, result: dict) -> None:
        schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(result)

    def run_cli(self, raw: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="handoff-action-binding-cli-") as temp:
            result = subprocess.run(
                [sys.executable, str(TOOL_PATH), "--stdin"],
                input=raw,
                text=True,
                capture_output=True,
                cwd=temp,
                check=False,
            )
            self.assertEqual(list(Path(temp).iterdir()), [], "CLI must not write files")
            return result

    def test_matching_fixture_reports_exact_declared_bindings_without_authority(self) -> None:
        document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        result, code = evaluate(document)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "DECLARED_BINDINGS_MATCH_NO_AUTHORITY")
        self.assertTrue(all(value in {"MATCH", "PASS", "NOT_REQUIRED"} for value in result["checks"].values()))
        self.assertFalse(result["handoff_accepted"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["runtime_invoked"])
        self.assertEqual(result["authorization_record_authenticity"], "NOT_AUTHENTICATED_CALLER_SUPPLIED_RECORDS")
        self.assertEqual(result["receipt_authenticity"], "NOT_ESTABLISHED_UNKEYED_DIGEST")
        self.assert_output_schema(result)

    def test_action_target_source_revision_and_task_state_mismatches_fail_closed(self) -> None:
        cases = (
            ("pending_action", lambda doc: doc["handoff_bundle"].update(pending_work=["action-other"]), "pending_action_id"),
            ("artifact_digest", lambda doc: doc["expected"].update(target_artifact_sha256="c" * 64), "target_artifact_and_source_digest"),
            ("source_revision", lambda doc: doc["expected"].update(source_revision="different-source-revision"), "source_revision"),
            ("task_state_revision", lambda doc: doc["expected"].update(receiver_observed_task_state_revision="r8"), "task_state_revision"),
        )
        for name, mutate, check in cases:
            with self.subTest(name=name):
                document = make_document()
                mutate(document)
                result, code = evaluate(document)
                self.assertEqual(code, 2)
                self.assertEqual(result["status"], "BLOCKED_OR_INCOMPLETE")
                self.assertEqual(result["checks"][check], "MISMATCH")
                self.assertFalse(result["execution_authorized"])
                self.assert_output_schema(result)

    def test_approval_reference_lease_and_packet_context_conflicts_fail_closed(self) -> None:
        cases = (
            ("denied_decision", lambda doc: doc["approval_decision"].update(decision="DENY"), "approval_request_decision_packet"),
            ("wrong_authorization_ref", lambda doc: doc["expected"].update(authorization_ref="decision-other"), "authorization_reference"),
            ("lease_packet_digest", lambda doc: doc["execution_lease"].update(packet_digest="d" * 64), "execution_lease_packet"),
            ("expired_lease", lambda doc: doc["execution_lease"].update(issued_at=1_600_000_000, expires_at=1_600_000_100), "execution_lease_packet"),
            ("receiver_adapter_version", lambda doc: doc["expected"].update(receiver_adapter_version="adapter-v2"), "receiver_identity_and_interface_version"),
        )
        for name, mutate, check in cases:
            with self.subTest(name=name):
                document = make_document()
                mutate(document)
                result, code = evaluate(document)
                self.assertEqual(code, 2)
                self.assertEqual(result["checks"][check], "MISMATCH")
                self.assertFalse(result["execution_authorized"])
                self.assert_output_schema(result)

    def test_native_resume_and_external_session_kind_are_not_assumed(self) -> None:
        document = make_document()
        document["expected"]["native_resume_required"] = True
        result, code = evaluate(document)
        self.assertEqual(code, 2)
        self.assertEqual(result["checks"]["native_resume_compatibility"], "UNSUPPORTED")
        self.assertIn("RECEIVER_DOES_NOT_DECLARE_NATIVE_RESUME", {row["code"] for row in result["findings"]})

        document = make_document(session_kind="remote-cli")
        result, code = evaluate(document)
        self.assertEqual(code, 2)
        self.assertEqual(result["checks"]["external_session_reference_support"], "UNSUPPORTED")
        self.assertIn("RECEIVER_SESSION_REFERENCE_KIND_UNSUPPORTED", {row["code"] for row in result["findings"]})
        self.assertFalse(result["runtime_invoked"])

    def test_schema_and_cli_reject_missing_fields_duplicate_keys_and_oversize(self) -> None:
        document = make_document()
        del document["expected"]["source_revision"]
        result, code = evaluate(document)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "INPUT_INVALID")
        self.assertIn("INPUT_SCHEMA_INVALID", {row["code"] for row in result["findings"]})

        duplicate = self.run_cli('{"schema_version":"x","schema_version":"y"}')
        self.assertEqual(duplicate.returncode, 2)
        duplicate_result = json.loads(duplicate.stdout)
        self.assertIn("DUPLICATE_JSON_KEY", {row["code"] for row in duplicate_result["findings"]})
        self.assert_output_schema(duplicate_result)

        oversized = self.run_cli(" " * (262_145))
        self.assertEqual(oversized.returncode, 2)
        oversized_result = json.loads(oversized.stdout)
        self.assertIn("INPUT_INVALID_OR_OVERSIZED", {row["code"] for row in oversized_result["findings"]})
        self.assert_output_schema(oversized_result)

        nonfinite = self.run_cli('{"schema_version":"handoff-action-binding-preflight-r0","value":NaN}')
        self.assertEqual(nonfinite.returncode, 2)
        nonfinite_result = json.loads(nonfinite.stdout)
        self.assertIn("INPUT_INVALID_OR_OVERSIZED", {row["code"] for row in nonfinite_result["findings"]})
        self.assert_output_schema(nonfinite_result)

    def test_cli_positive_fixture_emits_schema_valid_stdout_only(self) -> None:
        raw = FIXTURE_PATH.read_text(encoding="utf-8")
        result = self.run_cli(raw)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "DECLARED_BINDINGS_MATCH_NO_AUTHORITY")
        self.assertFalse(output["execution_authorized"])
        self.assert_output_schema(output)


if __name__ == "__main__":
    unittest.main()
