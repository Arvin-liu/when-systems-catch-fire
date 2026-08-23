from pathlib import Path
import tempfile
import unittest

from agent_federation.live_admission import LiveCapabilityAdmission
from agent_federation.live_bridge import LiveCapabilityLease, LiveDispatchEnvelope, LIVE_DISPATCH_SCHEMA


def envelope() -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA, task_id="IGNITION-20260823-136", dispatch_id="d-admit", attempt_id="a-admit",
        executor_id="external.codex", adapter_id="codex-live-r2", capability_id="live.readonly.synthetic", capability_lease_ref="lease-admit",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT", workspace_mode="DISPOSABLE_READ_ONLY", permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC", network_class="INFERENCE_TRANSPORT_ONLY", intent_capsule_ref=None,
        synthetic_input_ref="fixture://136", synthetic_input_digest="a" * 64, success_criteria=("return nonce",),
        output_contract={"format":"json", "required_fields":["nonce"]}, deadline="2026-08-24T00:00:00Z", timeout_seconds=10,
        retry_policy="NO_BLIND_RETRY", reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY", provenance={"controller":"pointfire-os"},
    )


def lease(**changes) -> LiveCapabilityLease:
    values = {
        "lease_id":"lease-admit", "executor_id":"external.codex", "executor_version":"codex-cli 0.144.4",
        "observed_at":"2026-08-23T16:00:00Z", "expires_at":"2026-08-23T16:05:00Z", "ttl_seconds":300,
        "binary_digest":"b" * 64, "interface_digest":"c" * 64, "observed_capabilities":("repo.read",),
        "forbidden_capabilities":("repo.write",), "unknown_capabilities":(),
        "workspace_semantics":"EXPLICIT_DISPOSABLE_READ_ONLY_CWD", "approval_sandbox_semantics":"READ_ONLY",
        "structured_output_semantics":"JSONL", "timeout_supported":True, "cancel_supported":True, "resume_supported":False,
        "live_eligibility":"ELIGIBLE_FOR_LIVE_READONLY", "eligibility_blockers":(), "source":"test",
    }
    values.update(changes)
    return LiveCapabilityLease.build(**values)


class LiveAdmissionTests(unittest.TestCase):
    def test_strict_intersection_is_admitted_through_existing_store(self):
        with tempfile.TemporaryDirectory() as directory:
            from agent_runtime.executor_admission import ExecutorAdmissionStore
            store = ExecutorAdmissionStore(Path(directory) / "admission.json")
            decision = LiveCapabilityAdmission(admission_store=store).admit(
                envelope(), lease(), os_granted=("repo.read", "repo.write"), executor_declared=("repo.read", "repo.write"),
                now_observed="2026-08-23T16:01:00Z", now_epoch=100,
            )
            routed = LiveCapabilityAdmission(admission_store=store).route(
                "external.codex", required_capabilities=("repo.read",), workspace_mode="DISPOSABLE_READ_ONLY",
                observed_version="codex-cli 0.144.4", now_epoch=101,
            )
        self.assertEqual(decision.status, "ADMITTED")
        self.assertEqual(decision.effective_capabilities, ("repo.read",))
        self.assertEqual(routed.status, "ADMITTED")

    def test_stale_lease_and_version_drift_fail_closed(self):
        admission = LiveCapabilityAdmission()
        stale = admission.admit(envelope(), lease(expires_at="2026-08-23T16:00:00Z"), os_granted=("repo.read",), executor_declared=("repo.read",), now_observed="2026-08-23T16:01:00Z")
        drift = admission.admit(envelope(), lease(), os_granted=("repo.read",), executor_declared=("repo.read",), now_observed="2026-08-23T16:01:00Z", current_binary_digest="d" * 64)
        self.assertEqual(stale.status, "REJECTED_CAPABILITY")
        self.assertEqual(drift.status, "REJECTED_CAPABILITY")

    def test_executor_or_os_widening_never_widens_effective_capability(self):
        admission = LiveCapabilityAdmission()
        decision = admission.admit(envelope(), lease(), os_granted=("repo.write",), executor_declared=("repo.write",), now_observed="2026-08-23T16:01:00Z")
        self.assertEqual(decision.status, "REJECTED_CAPABILITY")
        self.assertEqual(decision.effective_capabilities, ())

    def test_revocation_denies_future_route_and_reconciles_in_flight_unknown_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            from agent_runtime.executor_admission import ExecutorAdmissionStore
            store = ExecutorAdmissionStore(Path(directory) / "admission.json")
            bridge = LiveCapabilityAdmission(admission_store=store)
            bridge.admit(envelope(), lease(), os_granted=("repo.read",), executor_declared=("repo.read",), now_observed="2026-08-23T16:01:00Z", now_epoch=100)
            revoked = bridge.revoke_in_flight("external.codex", started=True, effect_class="UNKNOWN_SIDE_EFFECT")
            routed = bridge.route("external.codex", required_capabilities=("repo.read",), workspace_mode="DISPOSABLE_READ_ONLY", observed_version="codex-cli 0.144.4", now_epoch=101)
        self.assertEqual(revoked.status, "REQUIRES_RECONCILIATION")
        self.assertEqual(routed.status, "REJECTED_CAPABILITY")


if __name__ == "__main__":
    unittest.main()
