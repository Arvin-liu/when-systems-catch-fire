from __future__ import annotations

from pathlib import Path
import unittest

from agent_federation import (
    ApprovalBridge,
    ApprovalPolicy,
    ArtifactRef,
    ExternalApprovalObservation,
    ExternalSessionRef,
    FailoverContext,
    FederatedResultReceipt,
    HandoffEligibility,
    accept_handoff,
    build_handoff_bundle,
    decide_failover,
)
from agent_federation.approval_handoff import ApprovalHandoffError


def validated_receipt() -> FederatedResultReceipt:
    return FederatedResultReceipt.build(
        federation_task_id="handoff-task-001",
        executor_id="external.codex",
        terminal_state="COMPLETED_VALIDATED",
        claimed_actions=("read manifest",),
        artifact_refs=(ArtifactRef("fixture/manifest.json", "a" * 64, "manifest"),),
        validation_refs=("validator/manifest-v1",),
        external_session_ref=ExternalSessionRef("external.codex", "thread-001", "codex-thread-id", "2026-08-16T00:00:00Z"),
        executor_telemetry={"transport": "fixture", "event_count": 4},
        unresolveds=(),
        handoff_eligibility=HandoffEligibility(True, "validated read-only work may be handed off"),
    )


class ApprovalHandoffTests(unittest.TestCase):
    def test_os_deny_cannot_be_overridden_by_external_approval(self) -> None:
        decision = ApprovalBridge().evaluate(
            ApprovalPolicy("DENY", False, ("repo.write",)),
            ("repo.write",),
            external_observation=ExternalApprovalObservation("APPROVED", "external-approval-1"),
        )
        self.assertEqual(decision.status, "BLOCKED_WITH_EVIDENCE")
        self.assertIn("OS approval policy", decision.reason)

    def test_owner_and_external_gates_are_separate(self) -> None:
        policy = ApprovalPolicy("REQUIRE_OWNER", True, ("repo.write",))
        bridge = ApprovalBridge()
        waiting_owner = bridge.evaluate(policy, ("repo.write",), external_observation=ExternalApprovalObservation("APPROVED"))
        self.assertEqual(waiting_owner.status, "WAITING_FOR_APPROVAL")
        waiting_external = bridge.evaluate(policy, ("repo.write",), owner_decision="ALLOW", external_observation=ExternalApprovalObservation("WAITING"))
        self.assertEqual(waiting_external.status, "WAITING_EXTERNAL_APPROVAL")
        approved = bridge.evaluate(policy, ("repo.write",), owner_decision="ALLOW", external_observation=ExternalApprovalObservation("APPROVED"))
        self.assertEqual(approved.status, "APPROVED")

    def test_capability_intersection_fails_closed(self) -> None:
        decision = ApprovalBridge().evaluate(
            ApprovalPolicy("AUTO", True, ("repo.read",)),
            ("repo.write",),
            external_capability_ceiling=("repo.read", "repo.write"),
        )
        self.assertEqual(decision.status, "CAPABILITY_MISMATCH")

    def test_handoff_contains_public_receipt_state_and_pointer_only_session(self) -> None:
        bundle = build_handoff_bundle(
            handoff_id="handoff-001", source_receipt=validated_receipt(), goal="Continue the fixture audit",
            pending_work=("re-observe fixture",), allowed_capabilities=("repo.read",),
            workspace_refs=("fixture/",), acceptance_criteria=("manifest hash is verified",),
            operational_memory_capsule_refs=("memory-capsule-001",),
        )
        roundtrip = type(bundle).from_dict(bundle.to_dict())
        self.assertEqual(roundtrip, bundle)
        self.assertEqual(bundle.validated_completed_work, ("read manifest",))
        self.assertEqual(bundle.external_session_refs[0].pointer_only, True)
        self.assertNotIn("prompt", str(bundle.to_dict()).casefold())

    def test_unvalidated_receipt_cannot_be_called_validated_work(self) -> None:
        receipt = FederatedResultReceipt.build(
            federation_task_id="handoff-task-002", executor_id="external.hermes", terminal_state="REQUIRES_RECONCILIATION",
            claimed_actions=("claimed read",), artifact_refs=(), validation_refs=(), external_session_ref=None,
            executor_telemetry={"transport": "fixture"}, unresolveds=("OS_VALIDATION_NOT_PERFORMED",),
            handoff_eligibility=HandoffEligibility(False, "not validated"),
        )
        with self.assertRaises(ApprovalHandoffError):
            build_handoff_bundle(
                handoff_id="handoff-002", source_receipt=receipt, goal="Continue", pending_work=("verify",),
                allowed_capabilities=("repo.read",), workspace_refs=("fixture/",), acceptance_criteria=("verified",),
            )

    def test_takeover_requires_target_capability_and_fresh_observation(self) -> None:
        bundle = build_handoff_bundle(
            handoff_id="handoff-003", source_receipt=validated_receipt(), goal="Continue", pending_work=("verify",),
            allowed_capabilities=("repo.read",), workspace_refs=("fixture/",), acceptance_criteria=("verified",),
        )
        pending = accept_handoff(bundle, "external.hermes", ("repo.read",), workspace_reobserved=False, source_receipt_verified=False)
        self.assertEqual(pending.status, "REQUIRES_RECONCILIATION")
        accepted = accept_handoff(bundle, "external.hermes", ("repo.read",), workspace_reobserved=True, source_receipt_verified=True, observed_artifact_refs=("fixture/manifest.json",))
        self.assertEqual(accepted.status, "ACCEPTED")
        mismatch = accept_handoff(bundle, "external.openclaw", ("long_task",), workspace_reobserved=True, source_receipt_verified=True, observed_artifact_refs=("fixture/manifest.json",))
        self.assertEqual(mismatch.status, "CAPABILITY_MISMATCH")

    def test_failover_is_automatic_only_when_safe(self) -> None:
        safe = decide_failover(FailoverContext("external.codex", "external.hermes", "EXECUTOR_TIMEOUT", ("repo.read",), True, False, False, True), target_capabilities=("repo.read",))
        self.assertEqual(safe.status, "AUTO_FAILOVER_ELIGIBLE")
        unsafe = decide_failover(FailoverContext("external.codex", "external.hermes", "EXECUTOR_CRASH", ("repo.write",), False, False, False, False), target_capabilities=("repo.write",))
        self.assertEqual(unsafe.status, "REQUIRES_RECONCILIATION")
        replayable = decide_failover(FailoverContext("external.codex", "reference.executor", "EXECUTOR_OUTPUT_INVALID", ("repo.write",), False, False, True, True), target_capabilities=("repo.write",))
        self.assertEqual(replayable.status, "AUTO_FAILOVER_ELIGIBLE")

    def test_external_approval_block_does_not_silently_switch(self) -> None:
        decision = decide_failover(FailoverContext("external.hermes", "external.codex", "EXTERNAL_APPROVAL_BLOCKED", ("repo.read",), True, False, False, True, external_approval_allowed=False), target_capabilities=("repo.read",))
        self.assertEqual(decision.status, "BLOCKED_WITH_EVIDENCE")
        self.assertFalse(decision.automatic)


if __name__ == "__main__":
    unittest.main()
