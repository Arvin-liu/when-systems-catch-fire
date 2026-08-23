import hashlib
import unittest

from agent_federation.live_bridge import (
    LIVE_DISPATCH_SCHEMA,
    LIVE_LEASE_SCHEMA,
    LIVE_RECEIPT_SCHEMA,
    LiveCapabilityLease,
    LiveDispatchEnvelope,
    LiveDispatchStateMachine,
    LiveExecutorReceipt,
    LiveTransitionError,
)
from agent_federation.contracts import FederationContractError


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def envelope() -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA,
        task_id="IGNITION-20260823-136",
        dispatch_id="dispatch-contract-001",
        attempt_id="attempt-contract-001",
        executor_id="external.codex",
        adapter_id="codex-live-r2",
        capability_id="live.readonly.synthetic",
        capability_lease_ref="lease-contract-001",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT",
        workspace_mode="DISPOSABLE_READ_ONLY",
        permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC",
        network_class="INFERENCE_TRANSPORT_ONLY",
        intent_capsule_ref=None,
        synthetic_input_ref="fixture://live-136",
        synthetic_input_digest="a" * 64,
        success_criteria=("return the exact fixture nonce",),
        output_contract={"format": "json", "required_fields": ["nonce"]},
        deadline="2026-08-24T00:00:00Z",
        timeout_seconds=15,
        retry_policy="NO_BLIND_RETRY",
        reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY",
        provenance={"controller": "pointfire-os", "current_agent_is_external_executor": False},
    )


class LiveBridgeContractTests(unittest.TestCase):
    def test_dispatch_round_trip_is_strict_and_deterministic(self):
        record = envelope()
        self.assertEqual(LiveDispatchEnvelope.from_dict(record.to_dict()), record)
        self.assertEqual(record.to_dict(), LiveDispatchEnvelope.from_dict(record.to_dict()).to_dict())

    def test_dispatch_rejects_permission_widening_and_unknown_schema(self):
        data = envelope().to_dict()
        data["permission_ceiling"] = ["repo.write"]
        with self.assertRaises(FederationContractError):
            LiveDispatchEnvelope.from_dict(data)
        data = envelope().to_dict()
        data["unexpected"] = True
        with self.assertRaises(FederationContractError):
            LiveDispatchEnvelope.from_dict(data)

    def test_lease_and_receipt_have_integrity_digests(self):
        lease = LiveCapabilityLease.build(
            lease_id="lease-contract-001", executor_id="external.codex", executor_version="codex-cli 0.144.4",
            observed_at="2026-08-23T16:00:00Z", expires_at="2026-08-23T16:05:00Z", ttl_seconds=300,
            binary_digest="b" * 64, interface_digest="c" * 64, observed_capabilities=("repo.read", "structured_progress"),
            forbidden_capabilities=("repo.write", "messaging.send"), unknown_capabilities=(),
            workspace_semantics="EXPLICIT_DISPOSABLE_READ_ONLY_CWD", approval_sandbox_semantics="CODEX_READ_ONLY",
            structured_output_semantics="JSONL_AND_OUTPUT_SCHEMA", timeout_supported=True, cancel_supported=True,
            resume_supported=False, live_eligibility="ELIGIBLE_FOR_LIVE_READONLY", eligibility_blockers=(), source="step11-public-probe",
        )
        self.assertEqual(lease.schema_version, LIVE_LEASE_SCHEMA)
        self.assertEqual(LiveCapabilityLease.from_dict(lease.to_dict()), lease)
        receipt = LiveExecutorReceipt.build(
            task_id=envelope().task_id, dispatch_id=envelope().dispatch_id, attempt_id=envelope().attempt_id,
            executor_id="external.codex", adapter_id="codex-live-r2", state="RETURNED_UNVALIDATED",
            started_at="2026-08-23T16:01:00Z", ended_at="2026-08-23T16:01:02Z", exit_code=0,
            timed_out=False, cancel_state="NOT_REQUESTED", event_count=2, sanitized_event_summary="bounded result observed",
            response_digest=digest("result"), structured_result={"nonce": "n-001"}, session_pointer="opaque-session-pointer",
            side_effect_class="READ_ONLY_SYNTHETIC", side_effect_observation="READ_ONLY_UNCHANGED",
            workspace_before_digest="d" * 64, workspace_after_digest="d" * 64, os_validation_status="NOT_RUN",
            reconciliation_status="NOT_REQUIRED", claim_ceiling="bounded live observation only",
        )
        self.assertEqual(receipt.schema_version, LIVE_RECEIPT_SCHEMA)
        self.assertEqual(LiveExecutorReceipt.from_dict(receipt.to_dict()), receipt)

    def test_receipt_rejects_private_result_fields_and_forged_digest(self):
        with self.assertRaises(FederationContractError):
            LiveExecutorReceipt.build(
                task_id="t", dispatch_id="d", attempt_id="a", executor_id="external.codex", adapter_id="adapter",
                state="COMPLETED_VALIDATED", started_at="s", ended_at="e", exit_code=0, timed_out=False,
                cancel_state="NOT_REQUESTED", event_count=1, sanitized_event_summary="ok", response_digest=None,
                structured_result={"chain_of_thought": "private"}, session_pointer=None,
                side_effect_class="READ_ONLY_SYNTHETIC", side_effect_observation="READ_ONLY_UNCHANGED",
                workspace_before_digest="a" * 64, workspace_after_digest="a" * 64, os_validation_status="PASS",
                reconciliation_status="CLOSED", claim_ceiling="bounded",
            )
        data = LiveExecutorReceipt.build(
            task_id="t", dispatch_id="d", attempt_id="a", executor_id="external.codex", adapter_id="adapter",
            state="RETURNED_UNVALIDATED", started_at="s", ended_at="e", exit_code=0, timed_out=False,
            cancel_state="NOT_REQUESTED", event_count=1, sanitized_event_summary="ok", response_digest=None,
            structured_result=None, session_pointer=None, side_effect_class="READ_ONLY_SYNTHETIC",
            side_effect_observation="READ_ONLY_UNCHANGED", workspace_before_digest="a" * 64,
            workspace_after_digest="a" * 64, os_validation_status="NOT_RUN", reconciliation_status="NOT_REQUIRED",
            claim_ceiling="bounded",
        ).to_dict()
        data["receipt_digest"] = "f" * 64
        with self.assertRaises(FederationContractError):
            LiveExecutorReceipt.from_dict(data)

    def test_state_machine_requires_unvalidated_and_validation_hops(self):
        machine = LiveDispatchStateMachine(envelope(), observed_at="2026-08-23T16:00:00Z")
        machine.admit(allowed=True, reason="bounded read-only policy", cost_authorized=True)
        machine.begin_dispatch()
        machine.mark_in_flight()
        with self.assertRaises(LiveTransitionError):
            machine.transition("COMPLETED_VALIDATED", "executor said PASS")
        machine.record_executor_return(parsed=True, returncode=0)
        self.assertEqual(machine.state, "RETURNED_UNVALIDATED")
        machine.start_validation()
        machine.finish_validation(passed=True, workspace_unchanged=True, no_forbidden_effect=True)
        self.assertTrue(machine.terminal)

    def test_unknown_timeout_stops_replay_but_known_no_effect_allows_new_lineage(self):
        unknown = LiveDispatchStateMachine(envelope(), observed_at="now")
        unknown.admit(allowed=True, reason="policy")
        unknown.begin_dispatch()
        unknown.mark_in_flight()
        unknown.mark_timeout(effect_known_no_effect=False)
        self.assertEqual(unknown.state, "TIMED_OUT_EFFECT_UNKNOWN")
        self.assertFalse(unknown.retry_allowed)
        with self.assertRaises(LiveTransitionError):
            unknown.new_lineage_attempt("attempt-2")

        known = LiveDispatchStateMachine(envelope(), observed_at="now")
        known.admit(allowed=True, reason="policy")
        known.begin_dispatch()
        known.mark_in_flight()
        known.mark_timeout(effect_known_no_effect=True)
        self.assertTrue(known.retry_allowed)
        self.assertEqual(known.new_lineage_attempt("attempt-2"), "attempt-2")

    def test_executor_completion_receipt_cannot_bypass_validation(self):
        machine = LiveDispatchStateMachine(envelope(), observed_at="now")
        machine.admit(allowed=True, reason="policy")
        machine.begin_dispatch()
        machine.mark_in_flight()
        with self.assertRaises(LiveTransitionError):
            machine.record_executor_return(parsed=True, returncode=0)
            machine.transition("COMPLETED_VALIDATED", "forged executor completion")


if __name__ == "__main__":
    unittest.main()
