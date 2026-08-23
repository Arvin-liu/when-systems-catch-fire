import unittest

from agent_federation.live_bridge import LiveExecutorReceipt
from agent_federation.live_failover import decide_bounded_failover


def receipt(*, state: str, no_effect: str = "UNKNOWN", session_pointer: str | None = "opaque:private") -> LiveExecutorReceipt:
    return LiveExecutorReceipt.build(
        task_id="IGNITION-20260823-136", dispatch_id="failover-dispatch", attempt_id="failover-attempt",
        executor_id="external.hermes", adapter_id="hermes-live-r2", state=state,
        started_at="2026-08-24T00:00:00+00:00", ended_at="2026-08-24T00:00:01+00:00", exit_code=0,
        timed_out=False, cancel_state="NOT_REQUESTED", event_count=1, sanitized_event_summary="bounded result",
        response_digest="a" * 64, structured_result=None, session_pointer=session_pointer,
        side_effect_class="READ_ONLY_SYNTHETIC", side_effect_observation=no_effect,
        workspace_before_digest="b" * 64, workspace_after_digest="b" * 64, os_validation_status="NOT_RUN",
        reconciliation_status="NOT_REQUIRED", claim_ceiling="bounded receipt only",
    )


class LiveFailoverTests(unittest.TestCase):
    def test_unknown_effect_stops_without_retry_or_session_transfer(self):
        decision = decide_bounded_failover(receipt(state="TIMED_OUT_EFFECT_UNKNOWN"), target_executor_id="external.codex", target_admission_status="ADMITTED", target_capabilities=("repo.read",), no_effect_proven=False)
        self.assertEqual(decision.status, "REQUIRES_RECONCILIATION")
        self.assertIsNone(decision.new_attempt_id)
        self.assertFalse(decision.private_session_propagated)
        self.assertNotIn("session_pointer", decision.handoff_capsule)

    def test_no_effect_requires_fresh_admission_and_new_lineage(self):
        decision = decide_bounded_failover(receipt(state="TIMED_OUT_KNOWN_NO_EFFECT", no_effect="NO_EFFECT_OBSERVED"), target_executor_id="external.codex", target_admission_status="ADMITTED", target_capabilities=("repo.read",), no_effect_proven=True)
        self.assertEqual(decision.status, "FAILOVER_ELIGIBLE_NEW_LINEAGE")
        self.assertEqual(decision.new_attempt_id, "failover-attempt:failover:external.codex")
        self.assertEqual(decision.handoff_capsule["permission_ceiling"], ["repo.read"])

    def test_failover_cannot_bypass_target_capability_or_completion(self):
        denied = decide_bounded_failover(receipt(state="TIMED_OUT_KNOWN_NO_EFFECT", no_effect="NO_EFFECT_OBSERVED"), target_executor_id="external.codex", target_admission_status="REJECTED_CAPABILITY", target_capabilities=("repo.read",), no_effect_proven=True)
        completed = decide_bounded_failover(receipt(state="COMPLETED_VALIDATED", no_effect="READ_ONLY_UNCHANGED"), target_executor_id="external.codex", target_admission_status="ADMITTED", target_capabilities=("repo.read",), no_effect_proven=True)
        self.assertEqual(denied.status, "REJECTED_CAPABILITY")
        self.assertEqual(completed.status, "REQUIRES_RECONCILIATION")


if __name__ == "__main__":
    unittest.main()
