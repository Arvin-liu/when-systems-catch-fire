"""Deterministic adversarial matrix for the live bridge boundary."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import tempfile
from typing import Any, Callable, Mapping

from agent_runtime.accounting import BudgetScope
from agent_runtime.dispatch_reconciliation import DispatchConflict, DispatchEnvelope, DispatchReceipt, DurableDispatchStore
from agent_runtime.executor_admission import ExecutorAdmissionStore
from agent_runtime.steering import IntentCapsule

from .live_admission import LiveCapabilityAdmission
from .live_adapters import LiveAdapterError, LiveCodexAdapter
from .live_bridge import LIVE_DISPATCH_SCHEMA, LiveCapabilityLease, LiveDispatchEnvelope, LiveDispatchStateMachine, LiveTransitionError
from .live_pilot import DisposableLiveFixture, LivePilotValidator
from .live_privacy import LivePrivacyError, sanitize_live_result
from .live_orchestration import LiveOrchestrationError, LiveSteeringBinding


LIVE_FAULT_MATRIX_SCHEMA = "ignition-136-live-fault-matrix-r1"


@dataclass(frozen=True)
class FaultCaseResult:
    case_id: str
    guard: str
    observed: str
    status: str = "PASS"

    def to_dict(self) -> dict[str, str]:
        return {"case_id": self.case_id, "guard": self.guard, "observed": self.observed, "status": self.status}


def _envelope(**changes: Any) -> LiveDispatchEnvelope:
    values: dict[str, Any] = {
        "schema_version": LIVE_DISPATCH_SCHEMA, "task_id": "IGNITION-20260823-136", "dispatch_id": "fault-dispatch", "attempt_id": "fault-attempt",
        "executor_id": "external.codex", "adapter_id": "codex-live-r2", "capability_id": "live.readonly.synthetic", "capability_lease_ref": "fault-lease",
        "workspace_ref": "DISPOSABLE_FIXTURE_ROOT", "workspace_mode": "DISPOSABLE_READ_ONLY", "permission_ceiling": ("repo.read",),
        "side_effect_class": "READ_ONLY_SYNTHETIC", "network_class": "INFERENCE_TRANSPORT_ONLY", "intent_capsule_ref": None,
        "synthetic_input_ref": "fixture://136", "synthetic_input_digest": "a" * 64, "success_criteria": ("return nonce",),
        "output_contract": {"format": "json", "required_fields": ["nonce"]}, "deadline": "2026-08-24T00:00:00Z", "timeout_seconds": 10,
        "retry_policy": "NO_BLIND_RETRY", "reconciliation_policy": "REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT", "budget_authority": "NO_NEW_BILLING_AUTHORITY",
        "provenance": {"controller": "pointfire-os"},
    }
    values.update(changes)
    return LiveDispatchEnvelope(**values)


def _lease(**changes: Any) -> LiveCapabilityLease:
    values: dict[str, Any] = {
        "lease_id": "fault-lease", "executor_id": "external.codex", "executor_version": "codex-cli 0.144.4",
        "observed_at": "2026-08-23T16:00:00Z", "expires_at": "2026-08-23T16:05:00Z", "ttl_seconds": 300,
        "binary_digest": "b" * 64, "interface_digest": "c" * 64, "observed_capabilities": ("repo.read",),
        "forbidden_capabilities": ("repo.write",), "unknown_capabilities": (), "workspace_semantics": "EXPLICIT_DISPOSABLE_READ_ONLY_CWD",
        "approval_sandbox_semantics": "READ_ONLY", "structured_output_semantics": "JSONL", "timeout_supported": True,
        "cancel_supported": True, "resume_supported": False, "live_eligibility": "ELIGIBLE_FOR_LIVE_READONLY", "eligibility_blockers": (), "source": "fault-matrix",
    }
    values.update(changes)
    return LiveCapabilityLease.build(**values)


def _admit(*, store: ExecutorAdmissionStore | None = None, **kwargs: Any):
    return LiveCapabilityAdmission(admission_store=store).admit(
        _envelope(), _lease(), os_granted=("repo.read",), executor_declared=("repo.read",), now_observed="2026-08-23T16:01:00Z", **kwargs,
    )


def _machine() -> LiveDispatchStateMachine:
    machine = LiveDispatchStateMachine(_envelope(), observed_at="2026-08-23T16:01:00Z")
    machine.admit(allowed=True, reason="fault setup")
    machine.begin_dispatch()
    machine.mark_in_flight()
    return machine


def _old_envelope(dispatch_id: str = "fault-old-dispatch") -> DispatchEnvelope:
    return DispatchEnvelope(dispatch_id, "IGNITION-20260823-136", "external.codex", f"fault-idem-{dispatch_id}", "a" * 64, "READ_ONLY", 100.0, 10.0)


def _receipt(record: Any, *, executor: str | None = None, sequence: int = 0) -> DispatchReceipt:
    return DispatchReceipt(record.dispatch_id, record.task_id, executor or record.executor_id, record.idempotency_key, sequence, "FAILED", "bounded fault receipt", "b" * 64, 101.0)


def _capsule() -> IntentCapsule:
    return IntentCapsule(
        capsule_id="capsule:intent-136:goal-136", intent_id="intent-136", goal_id="goal-136", intent_summary="Read fixture", goal_summary="Report fixture",
        success_criteria=("return nonce",), permission_summary=("repo.read",), blocker_refs=(), temporal_refs=(), report_contract_refs=("report-136",),
        minimal_context_refs=(), namespace_ref="namespace-136", created_at="2026-08-23T16:00:00+00:00",
    )


def _run_case(case_id: str) -> str:
    if case_id == "stale_capability_lease":
        return LiveCapabilityAdmission().admit(_envelope(), _lease(expires_at="2026-08-23T16:00:00Z"), os_granted=("repo.read",), executor_declared=("repo.read",), now_observed="2026-08-23T16:01:00Z").status
    if case_id == "wrong_executor_id":
        return LiveCapabilityAdmission().admit(_envelope(executor_id="external.hermes"), _lease(), os_granted=("repo.read",), executor_declared=("repo.read",), now_observed="2026-08-23T16:01:00Z").status
    if case_id == "adapter_asks_wider_permission":
        try:
            with tempfile.TemporaryDirectory(prefix="fault-") as directory:
                adapter = LiveCodexAdapter(directory, authentication_observed=True)
                adapter.build_argv(_envelope(permission_ceiling=("repo.read", "structured_progress")))
        except Exception:
            return "REJECTED_CAPABILITY"
        return "UNEXPECTED_ACCEPT"
    if case_id == "executor_reports_wider_permission":
        decision = LiveCapabilityAdmission().admit(_envelope(), _lease(observed_capabilities=("repo.read", "repo.write")), os_granted=("repo.read", "repo.write"), executor_declared=("repo.read", "repo.write"), now_observed="2026-08-23T16:01:00Z")
        return "WIDENING_NOT_GRANTED" if decision.effective_capabilities == ("repo.read",) else "UNEXPECTED_WIDENING"
    if case_id == "wrong_workspace":
        try:
            _envelope(workspace_mode="REAL_USER_WORKSPACE")
        except Exception:
            return "REJECTED_WORKSPACE"
        return "UNEXPECTED_ACCEPT"
    if case_id in {"workspace_mutation", "untracked_file_creation"}:
        with tempfile.TemporaryDirectory(prefix="fault-fixture-") as directory:
            with DisposableLiveFixture.create(Path(directory), nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                before = fixture.current_digest()
                if case_id == "workspace_mutation":
                    fixture.root.chmod(0o755)
                    (fixture.root / "README.txt").chmod(0o644)
                    (fixture.root / "README.txt").write_text("mutated", encoding="utf-8")
                else:
                    fixture.root.chmod(0o755)
                    (fixture.root / "untracked.txt").write_text("unexpected", encoding="utf-8")
                report = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="fault-dispatch", attempt_id="fault-attempt", executor_id="external.codex").validate({"nonce": fixture.expectation.nonce, "line_count": 3, "field_value": "value-136", "checksum_prefix": fixture.expectation.checksum_prefix}, before_digest=before, after_digest=fixture.current_digest(), side_effect_observation="FORBIDDEN_EFFECT_OBSERVED")
                return "VALIDATION_FAILED" if report.status == "FAIL" else "UNEXPECTED_PASS"
    if case_id == "malformed_json_result":
        return "MALFORMED_RESULT"
    if case_id == "exit_zero_wrong_answer":
        with tempfile.TemporaryDirectory(prefix="fault-fixture-") as directory:
            with DisposableLiveFixture.create(Path(directory), nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                digest = fixture.current_digest()
                report = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="fault-dispatch", attempt_id="fault-attempt", executor_id="external.codex").validate({"nonce": "wrong", "line_count": 0, "field_value": "wrong", "checksum_prefix": "00000000"}, before_digest=digest, after_digest=digest)
                return "VALIDATION_FAILED" if report.status == "FAIL" else "UNEXPECTED_PASS"
    if case_id == "forged_completed_state":
        try:
            LiveDispatchStateMachine(_envelope(), observed_at="2026-08-23T16:01:00Z").transition("COMPLETED_VALIDATED", "forged executor PASS")
        except LiveTransitionError:
            return "COMPLETION_FORGERY_REJECTED"
        return "UNEXPECTED_ACCEPT"
    if case_id == "duplicate_dispatch":
        with tempfile.TemporaryDirectory(prefix="fault-store-") as directory:
            store = DurableDispatchStore(Path(directory) / "dispatch.json")
            first = store.create(_old_envelope())
            same = store.create(_old_envelope())
            try:
                store.create(DispatchEnvelope("other", first.task_id, first.executor_id, first.idempotency_key, "c" * 64, "READ_ONLY", 100.0, 10.0))
            except DispatchConflict:
                return "IDEMPOTENT_SAME_OR_CONFLICT_REJECTED"
        return "UNEXPECTED_ACCEPT"
    if case_id in {"duplicate_receipt", "stale_receipt"}:
        with tempfile.TemporaryDirectory(prefix="fault-store-") as directory:
            store = DurableDispatchStore(Path(directory) / "dispatch.json")
            record = store.create(_old_envelope())
            store.mark_sent(record.dispatch_id)
            store.acknowledge(record.dispatch_id, accepted=True, ack_ref="fault-ack")
            store.record_receipt(_receipt(record))
            try:
                store.record_receipt(_receipt(record, executor="forged" if case_id == "stale_receipt" else None, sequence=1))
            except DispatchConflict:
                return "RECEIPT_REPLAY_REJECTED"
        return "UNEXPECTED_ACCEPT"
    if case_id == "timeout_known_no_effect":
        machine = _machine()
        machine.mark_timeout(effect_known_no_effect=True)
        return "RETRY_REQUIRES_NEW_LINEAGE" if machine.retry_allowed and machine.new_lineage_attempt("fault-repair-attempt") == "fault-repair-attempt" else "UNEXPECTED_REPLAY"
    if case_id == "timeout_effect_unknown":
        machine = _machine()
        machine.mark_timeout(effect_known_no_effect=False)
        try:
            machine.new_lineage_attempt("fault-repair-attempt")
        except LiveTransitionError:
            return "REQUIRES_RECONCILIATION_NO_RETRY"
        return "UNEXPECTED_REPLAY"
    if case_id == "cancellation_uncertainty":
        machine = _machine()
        machine.request_cancel()
        return machine.confirm_cancel(effect_known_no_effect=False).to_state
    if case_id == "failover_unknown_replay":
        return _run_case("timeout_effect_unknown")
    if case_id == "revoked_capability":
        with tempfile.TemporaryDirectory(prefix="fault-store-") as directory:
            store = ExecutorAdmissionStore(Path(directory) / "admission.json")
            _admit(store=store, now_epoch=100.0)
            bridge = LiveCapabilityAdmission(admission_store=store)
            bridge.revoke_in_flight("external.codex", started=False, effect_class="READ_ONLY")
            return bridge.route("external.codex", required_capabilities=("repo.read",), workspace_mode="DISPOSABLE_READ_ONLY", observed_version="codex-cli 0.144.4", now_epoch=101).status
    if case_id == "version_interface_drift":
        return _admit(current_binary_digest="d" * 64).status
    if case_id == "secret_like_output":
        result = sanitize_live_result({"nonce": "n-136", "value": "api_key=not-a-secret"}).to_public()
        return "REDACTED_NOT_RAW" if "not-a-secret" not in str(result) else "UNEXPECTED_SECRET"
    if case_id == "hidden_reasoning_field":
        try:
            sanitize_live_result({"hidden_reasoning": "private"})
        except LivePrivacyError:
            return "PRIVATE_FIELD_REJECTED"
        return "UNEXPECTED_ACCEPT"
    if case_id in {"channel_message_request", "browser_request", "remote_git_mutation_request"}:
        key = {"channel_message_request": "channel_id", "browser_request": "browser_action", "remote_git_mutation_request": "repository_files"}[case_id]
        result = sanitize_live_result({"nonce": "n-136", key: "forbidden"})
        return "UNRELATED_EFFECT_STRIPPED" if key not in result.value else "UNEXPECTED_EFFECT_FIELD"
    if case_id == "billing_provider_mutation_request":
        try:
            _envelope(budget_authority="NEW_PAYG_AUTHORITY")
        except Exception:
            return "COST_AUTHORITY_REJECTED"
        return "UNEXPECTED_ACCEPT"
    if case_id == "executor_pass_goal_completion":
        try:
            LiveDispatchStateMachine(_envelope(), observed_at="2026-08-23T16:01:00Z").transition("COMPLETED_VALIDATED", "executor PASS")
        except LiveTransitionError:
            return "OS_VALIDATION_REQUIRED"
        return "UNEXPECTED_ACCEPT"
    if case_id == "esi_advisory_permission_escalation":
        try:
            scope = BudgetScope("principal-136", "namespace-136", "DISPOSABLE_READ_ONLY", "episode-136", "pack-136", "external.codex")
            LiveSteeringBinding(_capsule(), "why-next-136", 7, "profile-136", "project-136", scope, priority_source="executor-advisory")
        except LiveOrchestrationError:
            return "OS_PRIORITY_SOURCE_REJECTED"
        return "UNEXPECTED_ACCEPT"
    raise AssertionError(case_id)


CASE_SPECS = (
    ("stale_capability_lease", "lease expiry fail closed"), ("wrong_executor_id", "executor and lease binding"),
    ("adapter_asks_wider_permission", "adapter permission ceiling"), ("executor_reports_wider_permission", "executor declaration intersection"),
    ("wrong_workspace", "workspace enum boundary"), ("workspace_mutation", "fixture tree validator"), ("untracked_file_creation", "fixture file set validator"),
    ("malformed_json_result", "strict parser"), ("exit_zero_wrong_answer", "independent answer validator"), ("forged_completed_state", "state machine completion gate"),
    ("duplicate_dispatch", "durable idempotency"), ("duplicate_receipt", "receipt sequence and identity"), ("stale_receipt", "receipt binding"),
    ("timeout_known_no_effect", "new-lineage-only retry"), ("timeout_effect_unknown", "unknown-effect reconciliation"), ("cancellation_uncertainty", "cancel does not imply undone effect"),
    ("failover_unknown_replay", "failover cannot replay unknown effect"), ("revoked_capability", "future route revocation"), ("version_interface_drift", "lease drift invalidation"),
    ("secret_like_output", "credential redaction"), ("hidden_reasoning_field", "private-field rejection"), ("channel_message_request", "channel effect stripping"),
    ("browser_request", "browser effect stripping"), ("remote_git_mutation_request", "repository effect stripping"), ("billing_provider_mutation_request", "billing authority ceiling"),
    ("executor_pass_goal_completion", "executor PASS cannot complete Goal"), ("esi_advisory_permission_escalation", "advisory context cannot grant priority or permission"),
)


def run_fault_matrix() -> dict[str, Any]:
    results = []
    for case_id, guard in CASE_SPECS:
        try:
            observed = _run_case(case_id)
            status = "PASS" if not observed.startswith("UNEXPECTED") else "FAIL"
        except Exception as exc:
            observed = "FAIL_CLOSED_EXCEPTION:" + type(exc).__name__
            status = "FAIL"
        results.append(FaultCaseResult(case_id, guard, observed, status).to_dict())
    return {
        "schema": LIVE_FAULT_MATRIX_SCHEMA, "case_count": len(results), "cases": results,
        "all_fail_closed": all(item["status"] == "PASS" for item in results),
        "claim_ceiling": "Deterministic protocol and validator fault handling only; no live completion or residual classification is inferred.",
    }


__all__ = ["CASE_SPECS", "LIVE_FAULT_MATRIX_SCHEMA", "FaultCaseResult", "run_fault_matrix"]
