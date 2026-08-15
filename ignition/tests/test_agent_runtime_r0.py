from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_kernel import (
    AuthorizationRequest,
    AuthorizationStatus,
    AgentProfile,
    assert_no_authority_upgrade,
    CapabilityScope,
    Checkpoint,
    DomainPackManifest,
    Handoff,
    KernelValidationError,
    Phase,
    ResumeCapsule,
    StopState,
    authorize_action,
    validate_resume_lineage,
)
from agent_runtime import GoalContract, RunTerminalState
from agent_runtime.pilots.non_knowledge_manifest import run_pilot, validate_artifact


class AgentRuntimeR0Tests(unittest.TestCase):
    def test_non_knowledge_pilot_completes_after_independent_resume(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-runtime-test-") as temp:
            receipt = run_pilot(Path(temp))
            self.assertEqual(receipt["checkpoint_state"], StopState.CHECKPOINTED_RESUMABLE.value)
            self.assertEqual(receipt["final_state"], StopState.COMPLETED_VALIDATED.value)
            self.assertNotEqual(receipt["first_executor"], receipt["resume_executor"])
            self.assertFalse(receipt["network_allowed"])
            self.assertEqual(receipt["source_hashes_before"], receipt["source_hashes_after"])
            self.assertEqual(receipt["allowed_write_set"], receipt["actual_write_set"])
            self.assertEqual(validate_artifact(Path(temp))["state_sha256"], receipt["state_sha256"])
            self.assertNotIn("foundation", json.dumps(receipt).casefold())

    def test_unknown_capability_and_unauthorized_write_fail_closed(self) -> None:
        scope = CapabilityScope(scope_id="read-only", allowed_reads=("input/*.txt",), allowed_tools=("read.files",))
        request = AuthorizationRequest(
            action_id="write-1",
            run_id="run-1",
            required_capabilities=("write.manifest",),
            requested_reads=("input/a.txt",),
            requested_writes=("output/result.json",),
            reason_summary="attempt an undeclared write",
        )
        decision = authorize_action(scope, request)
        self.assertEqual(decision.status, AuthorizationStatus.DENY.value)
        self.assertIn("capability", decision.reason_summary)

    def test_strict_records_reject_malformed_and_generic_success(self) -> None:
        goal = {
            "goal_id": "goal-1",
            "statement": "bounded test goal",
            "success_conditions": ["validated"],
            "prohibited_actions": [],
            "capability_scope_ref": "scope-1",
            "version": "r0",
            "unexpected": "reject",
        }
        with self.assertRaises(KernelValidationError):
            GoalContract.from_dict(goal)
        with self.assertRaises(KernelValidationError):
            RunTerminalState(state="SUCCESS", summary="not allowed", executor_id="executor-1", event_count=0)

    def test_profile_cannot_self_escalate_and_pack_cannot_grant_kernel_authority(self) -> None:
        with self.assertRaises(KernelValidationError):
            AgentProfile(
                stable_agent_id="agent-1",
                owner_ref="owner:human",
                authority_refs=("authority:1",),
                charter_refs=("charter:1",),
                role="bounded",
                allowed_capability_classes=("read_declared",),
                mutable_preference_refs=(),
                update_policy="owner-only",
                memory_policy="structured-only",
                prohibited_self_escalation=False,
            )
        with self.assertRaises(KernelValidationError):
            DomainPackManifest(
                pack_id="bad-pack",
                display_name="Bad",
                domain="test",
                capabilities_provided=("test.read",),
                object_types=("test_object",),
                validators=("validator",),
                human_entries=("README.md",),
                machine_entries=("data/",),
                required_kernel_capabilities=("read_declared",),
                prohibited_authority_upgrades=("owner_acceptance",),
            )

        with self.assertRaises(KernelValidationError):
            assert_no_authority_upgrade(("kernel_definition",))
        assert_no_authority_upgrade(("read_declared",))

    def test_resume_lineage_rejects_detached_digest_and_executor(self) -> None:
        digest = "a" * 64
        checkpoint = Checkpoint(
            checkpoint_id="checkpoint-1",
            run_id="run-1",
            phase=Phase.STOP.value,
            state_ref="run-state.json",
            state_sha256=digest,
            event_count=2,
            created_by="executor-alpha",
            reason_summary="bounded checkpoint",
        )
        capsule = ResumeCapsule(
            capsule_id="capsule-1",
            run_id="run-1",
            checkpoint_id="checkpoint-1",
            state_ref="run-state.json",
            state_sha256=digest,
            pending_action_ids=("action-2",),
            required_capabilities=("read.files",),
            created_by="executor-alpha",
            handoff=Handoff(
                from_executor_id="executor-alpha",
                to_executor_id="executor-beta",
                reason_summary="resume only after digest verification",
                resume_ref="run-state.json",
            ),
        )
        with self.assertRaises(KernelValidationError):
            validate_resume_lineage(checkpoint, capsule, "b" * 64, executor_id="executor-beta")
        with self.assertRaises(KernelValidationError):
            validate_resume_lineage(checkpoint, capsule, digest, executor_id="executor-gamma")


if __name__ == "__main__":
    unittest.main()
