from pathlib import Path
import tempfile
import unittest

from agent_kernel.contracts import sha256_json
from agent_federation.live_bridge import LIVE_DISPATCH_SCHEMA, LiveCapabilityLease, LiveDispatchEnvelope, LiveExecutorReceipt
from agent_federation.live_pilot import DisposableLiveCompletionFixture
from agent_federation.live_validation import LiveIndependentValidator


NOW = "2026-08-24T00:01:00+00:00"


def envelope() -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA, task_id="IGNITION-20260824-137", dispatch_id="dispatch-137", attempt_id="attempt-137",
        executor_id="external.codex", adapter_id="codex-live-r2", capability_id="live.readonly.synthetic", capability_lease_ref="lease-137",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT", workspace_mode="DISPOSABLE_SYNTHETIC_READ_ONLY", permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC", network_class="INFERENCE_TRANSPORT_ONLY", intent_capsule_ref=None,
        synthetic_input_ref="fixture://IGNITION-20260824-137", synthetic_input_digest="a" * 64,
        success_criteria=("return exact synthetic result",),
        output_contract={"format": "json", "required_fields": ["nonce", "selected_ids", "count", "workspace_digest_claim"]},
        deadline="2026-08-24T00:10:00+00:00", timeout_seconds=900, retry_policy="NO_BLIND_RETRY",
        reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT", budget_authority="NO_NEW_BILLING_AUTHORITY",
        provenance={"controller": "pointfire-os", "child_depth": 1},
    )


def lease(*, expires_at: str = "2026-08-24T00:05:00+00:00") -> LiveCapabilityLease:
    return LiveCapabilityLease.build(
        lease_id="lease-137", executor_id="external.codex", executor_version="codex-cli 0.144.4",
        observed_at="2026-08-24T00:00:00+00:00", expires_at=expires_at, ttl_seconds=300,
        binary_digest="b" * 64, interface_digest="c" * 64, observed_capabilities=("repo.read", "structured_progress"),
        forbidden_capabilities=("repo.write", "messaging.send"), unknown_capabilities=(),
        workspace_semantics="EXPLICIT_DISPOSABLE_READ_ONLY_CWD", approval_sandbox_semantics="CODEX_READ_ONLY",
        structured_output_semantics="JSONL_PUBLIC_EVENTS_AND_OUTPUT_SCHEMA", timeout_supported=True, cancel_supported=True,
        resume_supported=False, live_eligibility="ELIGIBLE_FOR_LIVE_READONLY", eligibility_blockers=(), source="test",
    )


def result(fixture: DisposableLiveCompletionFixture, *, nonce: str | None = None) -> dict:
    return {
        "nonce": nonce or fixture.expectation.nonce,
        "selected_ids": ["row-a", "row-d", "row-c"],
        "count": 3,
        "workspace_digest_claim": fixture.before_digest,
    }


def receipt(value: dict, fixture: DisposableLiveCompletionFixture, current_lease: LiveCapabilityLease, *, executor_id: str = "external.codex", workspace_ref: str = "DISPOSABLE_FIXTURE_ROOT") -> LiveExecutorReceipt:
    return LiveExecutorReceipt.build(
        task_id="IGNITION-20260824-137", dispatch_id="dispatch-137", attempt_id="attempt-137",
        executor_id=executor_id, adapter_id="codex-live-r2", state="RETURNED_UNVALIDATED",
        started_at="2026-08-24T00:00:10+00:00", ended_at="2026-08-24T00:00:11+00:00", exit_code=0,
        timed_out=False, cancel_state="NOT_REQUESTED", event_count=2, sanitized_event_summary="bounded result",
        response_digest=sha256_json(value), structured_result=value, session_pointer=None,
        side_effect_class="READ_ONLY_SYNTHETIC", side_effect_observation="READ_ONLY_UNCHANGED",
        workspace_before_digest=fixture.before_digest, workspace_after_digest=fixture.before_digest,
        os_validation_status="NOT_RUN", reconciliation_status="NOT_REQUIRED", claim_ceiling="unvalidated",
        workspace_ref=workspace_ref, capability_lease_digest=current_lease.lease_digest,
        result_digest=sha256_json(value), child_depth=1,
        elapsed_seconds=1.0, timeout_seconds=900, process_group_status="CONFIRMED_GONE",
        stdout_byte_count=10, stderr_byte_count=0, stdout_digest="d" * 64, stderr_digest="e" * 64,
    )


class LiveValidationTests(unittest.TestCase):
    def validate(self, *, current_lease=None, value=None, executor_id="external.codex", workspace_ref="DISPOSABLE_FIXTURE_ROOT"):
        with tempfile.TemporaryDirectory() as directory:
            with DisposableLiveCompletionFixture.create(Path(directory), nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                current_lease = current_lease or lease()
                value = value or result(fixture)
                receipt_value = receipt(value, fixture, current_lease, executor_id=executor_id, workspace_ref=workspace_ref)
                validation, report = LiveIndependentValidator(fixture).validate(
                    envelope=envelope(), lease=current_lease, executor_receipt=receipt_value, result=value,
                    before_digest=fixture.before_digest, after_digest=fixture.current_digest(), observed_at=NOW,
                    child_depth=1, external_surface_evidence={
                        "channel": False, "browser": False, "remote_git": False, "user_data": False,
                        "formal_repo_mutation": False, "billing_authority": False,
                    },
                )
                return validation, report

    def test_pass_requires_exact_binding_and_independent_answer(self):
        validation, report = self.validate()
        self.assertEqual(validation.status, "PASS")
        self.assertEqual(report.status, "PASS")
        self.assertEqual(validation.child_depth, 1)
        self.assertEqual(validation.effective_capabilities, ("repo.read",))
        self.assertEqual(validation.validator_receipt_digest, validation.to_dict()["validator_receipt_digest"])

    def test_stale_lease_wrong_nonce_copied_result_workspace_and_executor_fail_closed(self):
        stale, _ = self.validate(current_lease=lease(expires_at="2026-08-23T23:59:00+00:00"))
        self.assertEqual(stale.status, "FAIL")
        self.assertIn("LEASE_FRESH", stale.failure_codes)

        with tempfile.TemporaryDirectory() as directory:
            with DisposableLiveCompletionFixture.create(Path(directory), nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                current_lease = lease()
                bad = result(fixture, nonce="fedcba987654321001234567")
                bad_receipt = receipt(bad, fixture, current_lease)
                validation, _ = LiveIndependentValidator(fixture).validate(
                    envelope=envelope(), lease=current_lease, executor_receipt=bad_receipt, result=bad,
                    before_digest=fixture.before_digest, after_digest=fixture.current_digest(), observed_at=NOW,
                    child_depth=1, external_surface_evidence={key: False for key in ("channel", "browser", "remote_git", "user_data", "formal_repo_mutation", "billing_authority")},
                )
                self.assertEqual(validation.status, "FAIL")
                self.assertIn("FIXTURE_VALIDATOR", validation.failure_codes)

                wrong_workspace, _ = self.validate(workspace_ref="OTHER_DISPOSABLE_FIXTURE")
                self.assertIn("WORKSPACE_BINDING", wrong_workspace.failure_codes)
                substituted, _ = self.validate(executor_id="external.hermes")
                self.assertIn("EXECUTOR_BINDING", substituted.failure_codes)


if __name__ == "__main__":
    unittest.main()
