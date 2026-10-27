from __future__ import annotations

import copy
import unittest

from agent_federation import (
    ApprovalPolicy,
    ArtifactRef,
    BudgetContract,
    ExecutorDescriptor,
    ExecutorHealth,
    ExternalSessionRef,
    FederatedHandoffBundle,
    FederatedProgressEvent,
    FederatedResultReceipt,
    FederatedTaskEnvelope,
    FederationContractError,
    HandoffEligibility,
    HandoffPolicy,
    OutputContract,
    ValidationContract,
)


def descriptor() -> ExecutorDescriptor:
    return ExecutorDescriptor(
        executor_id="fixture.executor.a",
        family="fixture-family",
        version="1.0",
        transport_kind=("FIXTURE",),
        availability="AVAILABLE",
        health=ExecutorHealth("HEALTHY", "2026-08-16T00:00:00Z", "fixture healthy", capability_digest="a" * 64),
        capability_tokens=("repo.read", "repo.test"),
        supported_task_granularities=("ACTION", "SUBTASK"),
        workspace_semantics="disposable local workspace",
        permission_control_semantics="OS and executor intersection",
        structured_output_support=True,
        progress_support=True,
        cancel_support=True,
        native_resume_support=False,
        external_session_refs=("fixture-session",),
        network_semantics="disabled",
        max_task_duration_seconds=30,
        adapter_version="adapter-r1",
        limitations=("fixture only",),
    )


def envelope() -> FederatedTaskEnvelope:
    return FederatedTaskEnvelope(
        federation_task_id="fed-task-001",
        owner_ref="owner-ref",
        profile_ref="profile-ref",
        goal="Inspect a disposable fixture",
        success_criteria=("manifest is deterministic",),
        required_capabilities=("repo.read", "repo.test"),
        allowed_effects=("read fixture",),
        forbidden_effects=("write outside fixture", "send message"),
        workspace_scope=("fixture/",),
        approval_policy=ApprovalPolicy("DENY", False, ("repo.read", "repo.test")),
        context_capsule_refs=("capsule-1",),
        pack_refs=("maintenance.repository",),
        validation_contract=ValidationContract("manifest-v1", ("hash",), ("validator-1",)),
        output_contract=OutputContract("json", ("manifest",)),
        budget=BudgetContract(30, 10000, 2),
        idempotency_key="idem-001",
        privacy_class="LOCAL_FIXTURE",
        handoff_policy=HandoffPolicy(True, ("fixture.executor.b",), True),
        reason_summary="bounded conformance fixture",
    )


class FederationCoreTests(unittest.TestCase):
    def test_descriptor_and_envelope_roundtrip(self) -> None:
        self.assertEqual(ExecutorDescriptor.from_dict(descriptor().to_dict()), descriptor())
        original = envelope()
        self.assertEqual(FederatedTaskEnvelope.from_dict(original.to_dict()), original)

    def test_progress_is_public_and_fraction_bounded(self) -> None:
        event = FederatedProgressEvent("fed-task-001", "fixture.executor.a", 0, "RUNNING", "Reading fixture", ("ref-1",), 0.25)
        self.assertEqual(FederatedProgressEvent.from_dict(event.to_dict()), event)
        with self.assertRaises(FederationContractError):
            FederatedProgressEvent("fed-task-001", "fixture.executor.a", 0, "RUNNING", "bad", (), 2)

    def test_receipt_digest_and_session_pointer_are_verified(self) -> None:
        session = ExternalSessionRef("fixture.executor.a", "session-1", "cli", "2026-08-16T00:00:00Z")
        receipt = FederatedResultReceipt.build(
            federation_task_id="fed-task-001",
            executor_id="fixture.executor.a",
            terminal_state="COMPLETED_VALIDATED",
            claimed_actions=("read fixture",),
            artifact_refs=(ArtifactRef("manifest.json", "b" * 64, "manifest"),),
            validation_refs=("validation-1",),
            external_session_ref=session,
            executor_telemetry={"duration_ms": 12, "transport": "fixture"},
            unresolveds=(),
            handoff_eligibility=HandoffEligibility(True, "read-only fixture complete"),
        )
        self.assertEqual(FederatedResultReceipt.from_dict(receipt.to_dict()), receipt)
        tampered = copy.deepcopy(receipt.to_dict())
        tampered["claimed_actions"] = ["write fixture"]
        with self.assertRaises(FederationContractError):
            FederatedResultReceipt.from_dict(tampered)
        with self.assertRaises(FederationContractError):
            ExternalSessionRef("fixture.executor.a", "secret:token", "cli", "2026-08-16T00:00:00Z")

    def test_handoff_contains_refs_not_hidden_state(self) -> None:
        bundle = FederatedHandoffBundle(
            "handoff-1", "fed-task-001", "fixture.executor.a", envelope().goal,
            ("manifest read validated",), ("run validator",), ("repo.test",), ("fixture/",),
            (ArtifactRef("manifest.json", "c" * 64, "manifest"),), ("manifest is deterministic",),
            ("capsule-1",), (ExternalSessionRef("fixture.executor.a", "session-1", "cli", "2026-08-16T00:00:00Z"),), (),
        )
        self.assertEqual(FederatedHandoffBundle.from_dict(bundle.to_dict()), bundle)

    def test_hidden_fields_are_rejected(self) -> None:
        health = ExecutorHealth("HEALTHY", "2026-08-16T00:00:00Z", "ok")
        with self.assertRaises(FederationContractError):
            ExecutorDescriptor.from_dict({**descriptor().to_dict(), "health": {**health.to_dict(), "prompt": "hidden"}})


if __name__ == "__main__":
    unittest.main()
