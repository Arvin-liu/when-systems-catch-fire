#!/usr/bin/env python3
"""Run and durably record Task139's one authorized live synthetic attempt.

The external process boundary is crossed at most once.  Public probes, OS
coordination, host capture and the append-only ledger are all kept in the same
bounded episode; any observation failure is recorded as incomplete and never
retried.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import argparse
import json
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json
from agent_runtime.accounting import AccountingPolicy, AccountingStore, BudgetScope, CostVector
from agent_runtime.dispatch_reconciliation import DurableDispatchStore
from agent_runtime.event_ledger import EventLedger
from agent_runtime.queue_control import WorkQueue
from agent_runtime.resource_arbitration import ResourceArbiter
from agent_runtime.steering import IntentCapsule

from agent_federation.live_admission import LiveCapabilityAdmission, LiveAdmissionDecision
from agent_federation.live_attempt_ledger import LiveAttemptLedger, LiveAttemptLedgerError
from agent_federation.live_bridge import LiveDispatchEnvelope, LiveExecutorReceipt
from agent_federation.live_child_guard import CHILD_ENV_ALLOWLIST, LiveChildContext
from agent_federation.live_execution import LiveAttemptResult, execute_bounded_attempt
from agent_federation.live_orchestration import LiveDispatchCoordinator, LiveSteeringBinding
from agent_federation.live_pilot import DisposableLiveFixture, LivePilotValidator
from agent_federation.live_transport import LiveProcessResult, LiveProcessTransport
from agent_federation.live_current_projection import validate_projection
from agent_federation.local_executor_census import validate_path

try:
    from tools.run_task139_live_admission import (
        AUTH_SOURCE,
        CODEX,
        CONTROL_REPO,
        DOCUMENT_ROOT,
        REPO_ROOT,
        ROOT,
        TASK_ID,
        _envelope,
        _schema_path,
    )
except ImportError:  # direct execution with ignition/tools on sys.path
    from run_task139_live_admission import (  # type: ignore
        AUTH_SOURCE,
        CODEX,
        CONTROL_REPO,
        DOCUMENT_ROOT,
        REPO_ROOT,
        ROOT,
        TASK_ID,
        _envelope,
        _schema_path,
    )


LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
PROJECTION_PATH = ROOT / "data/operations/iterations/139/live-current-projection-r1.json"
DISPATCH_ID = "dispatch-139-live-02"
ATTEMPT_ID = "attempt-139-live-02"
LEASE_ID = "lease-ignition-139-codex-live-02"
ADAPTER_ID = "codex-live-r3"


class SingleLiveAttemptError(RuntimeError):
    """Raised when the single-live-attempt boundary cannot be proven."""


class RecordingTransport:
    """Record only public argv shape and retain the last bounded process result."""

    supports_runtime_scratch = True
    supports_durable_capture = True

    def __init__(self, delegate: LiveProcessTransport) -> None:
        self.delegate = delegate
        self.calls: list[tuple[str, ...]] = []
        self.last_result: LiveProcessResult | None = None

    def run(self, argv: Sequence[str], **kwargs: Any) -> LiveProcessResult:
        self.calls.append(tuple(argv))
        self.last_result = self.delegate.run(argv, **kwargs)
        return self.last_result

    @property
    def live_dispatch_calls(self) -> int:
        return sum(
            1 for call in self.calls
            if len(call) > 2 and call[1] == "exec" and call[-1] != "--help"
        )


def _now() -> tuple[str, str]:
    current = datetime.now(timezone.utc).replace(microsecond=0)
    return current.isoformat().replace("+00:00", "Z"), (current + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")


def _accounting_policy() -> AccountingPolicy:
    identifiers = {
        "principal": "principal-139",
        "namespace": "namespace-139",
        "workspace": "DISPOSABLE_SYNTHETIC_READ_ONLY",
        "episode": "episode-139-live",
        "pack": "pack-live-139",
        "executor": "external.codex",
    }
    limit = CostVector(action_count=2, wall_clock_seconds=120, output_bytes=2, event_volume=20)
    return AccountingPolicy(
        limits={f"{dimension}:{identifier}": limit for dimension, identifier in identifiers.items()},
        workspace_namespace={"DISPOSABLE_SYNTHETIC_READ_ONLY": "namespace-139"},
    )


def _steering(observed_at: str) -> LiveSteeringBinding:
    capsule = IntentCapsule(
        capsule_id="capsule-intent-139-live",
        intent_id="intent-139-live",
        goal_id="goal-139-live",
        intent_summary="Observe one disposable synthetic executor attempt",
        goal_summary="Persist a bounded public result or an explicit incomplete observation",
        success_criteria=("return the exact public result described by the disposable synthetic fixture",),
        permission_summary=("repo.read",),
        blocker_refs=(),
        temporal_refs=(),
        report_contract_refs=("report-contract-139-live",),
        minimal_context_refs=("fixture-ref-139-live",),
        namespace_ref="namespace-139",
        created_at=observed_at,
    )
    scope = BudgetScope(
        principal_id="principal-139",
        namespace_id="namespace-139",
        workspace_id="DISPOSABLE_SYNTHETIC_READ_ONLY",
        episode_id="episode-139-live",
        pack_id="pack-live-139",
        executor_id="external.codex",
    )
    return LiveSteeringBinding(
        capsule=capsule,
        why_next_ref="why-next-139-live-attempt",
        priority=7,
        profile_ref="profile-live-139",
        project_ref=TASK_ID,
        budget_scope=scope,
    )


def _coordinator(
    root: Path,
    envelope: LiveDispatchEnvelope,
    admission: LiveAdmissionDecision,
    observed_at: str,
) -> LiveDispatchCoordinator:
    state = root / "os-state"
    state.mkdir()
    return LiveDispatchCoordinator(
        envelope=envelope,
        steering=_steering(observed_at),
        admission=admission,
        queue=WorkQueue(state / "queue.json", max_depth=2, profile_limits={"profile-live-139": 2}),
        resources=ResourceArbiter(state / "resources.json"),
        accounting=AccountingStore(state / "accounting.json", _accounting_policy()),
        dispatch_store=DurableDispatchStore(state / "dispatch.json"),
        ledger=EventLedger(state / "events.jsonl"),
    )


def _process_group_cleanup(status: str) -> str:
    if status == "CONFIRMED_GONE":
        return "CLEANED"
    if status in {"CHILD_LEFT_BEHIND", "UNKNOWN"}:
        return "REQUIRES_RECONCILIATION"
    return "NOT_OBSERVED"


def _fallback_receipt(
    *,
    envelope: LiveDispatchEnvelope,
    lease_digest: str,
    fixture: DisposableLiveFixture,
    process: LiveProcessResult | None,
    started_at: str,
    ended_at: str,
) -> LiveExecutorReceipt:
    before = fixture.before_digest
    after = fixture.current_digest()
    state = "TIMED_OUT_EFFECT_UNKNOWN" if process is not None and process.timed_out else "REQUIRES_RECONCILIATION"
    process_group_status = process.process_group_status if process is not None else "UNKNOWN"
    if process_group_status not in {"NOT_REQUIRED", "CONFIRMED_GONE", "CHILD_LEFT_BEHIND", "UNKNOWN"}:
        process_group_status = "UNKNOWN"
    return LiveExecutorReceipt.build(
        task_id=envelope.task_id,
        dispatch_id=envelope.dispatch_id,
        attempt_id=envelope.attempt_id,
        executor_id=envelope.executor_id,
        adapter_id=envelope.adapter_id,
        state=state,
        started_at=process.started_at if process is not None and process.started_at else started_at,
        ended_at=process.ended_at if process is not None and process.ended_at else ended_at,
        exit_code=process.returncode if process is not None else None,
        timed_out=bool(process.timed_out) if process is not None else False,
        cancel_state="UNKNOWN",
        event_count=len(process.captured_events) if process is not None else 0,
        sanitized_event_summary="PUBLIC_OBSERVATION_INCOMPLETE",
        response_digest=process.stdout_digest if process is not None else None,
        structured_result=None,
        session_pointer=None,
        side_effect_class=envelope.side_effect_class,
        side_effect_observation="READ_ONLY_UNCHANGED" if before == after and fixture.read_only_guard_observed() else "UNKNOWN",
        workspace_before_digest=before,
        workspace_after_digest=after,
        os_validation_status="NOT_RUN",
        reconciliation_status="OPEN",
        claim_ceiling="One bounded external process boundary was crossed but host observation is incomplete; no result or completion is inferred.",
        elapsed_seconds=(process.duration_ms / 1000.0) if process is not None else 0.0,
        timeout_seconds=envelope.timeout_seconds,
        timeout_requested=bool(process.timed_out) if process is not None else False,
        termination_requested=bool(process.termination_requested) if process is not None else False,
        signals_sent=process.signals_sent if process is not None else (),
        process_group_status=process_group_status,
        first_public_event_latency_seconds=(process.first_public_event_latency_ms / 1000.0) if process is not None and process.first_public_event_latency_ms is not None else None,
        stdout_byte_count=process.stdout_bytes or 0 if process is not None else 0,
        stderr_byte_count=process.stderr_bytes or 0 if process is not None else 0,
        stdout_digest=process.stdout_digest if process is not None else None,
        stderr_digest=process.stderr_digest if process is not None else None,
        workspace_ref=envelope.workspace_ref,
        capability_lease_digest=lease_digest,
        result_digest=None,
        child_depth=1,
    )


def _ledger_record(
    *,
    envelope: LiveDispatchEnvelope,
    lease: Any,
    receipt: LiveExecutorReceipt,
    validation: Any,
    capture_capsule: Mapping[str, Any] | None,
    process: LiveProcessResult | None,
    ledger_state_override: str | None = None,
) -> dict[str, Any]:
    ledger_state = ledger_state_override or receipt.state
    capture_complete = bool(capture_capsule and capture_capsule.get("capture_completeness") == "COMPLETE")
    evidence = "COMPLETE" if capture_complete and not receipt.timed_out and ledger_state not in {"OBSERVATION_INCOMPLETE", "REQUIRES_RECONCILIATION"} else "INCOMPLETE"
    capture_ref = str(capture_capsule.get("spool_ref")) if capture_capsule and capture_capsule.get("spool_ref") else "UNRECOVERED"
    capture_digest = sha256_json(capture_capsule) if capture_capsule else "UNRECOVERED"
    if capture_capsule:
        event_count = int(capture_capsule.get("public_events", {}).get("count", receipt.event_count))
        stdout_bytes = int(capture_capsule.get("stdout", {}).get("byte_count", receipt.stdout_byte_count))
        stderr_bytes = int(capture_capsule.get("stderr", {}).get("byte_count", receipt.stderr_byte_count))
        stdout_digest = capture_capsule.get("stdout", {}).get("digest", receipt.stdout_digest or "UNRECOVERED")
        stderr_digest = capture_capsule.get("stderr", {}).get("digest", receipt.stderr_digest or "UNRECOVERED")
    else:
        event_count = receipt.event_count
        stdout_bytes = receipt.stdout_byte_count
        stderr_bytes = receipt.stderr_byte_count
        stdout_digest = receipt.stdout_digest or "UNRECOVERED"
        stderr_digest = receipt.stderr_digest or "UNRECOVERED"
    structured_present = receipt.structured_result is not None
    structured_ref = None
    if structured_present and capture_capsule:
        structured_ref = capture_capsule.get("structured_result", {}).get("ref")
    if structured_present and not structured_ref:
        structured_ref = f"result://{envelope.attempt_id}"
    if structured_present:
        structured_digest = receipt.result_digest or sha256_json(receipt.structured_result)
    else:
        structured_digest = "UNRECOVERED" if evidence == "INCOMPLETE" else "NOT_APPLICABLE"
    if validation is not None:
        validator_status = validation.status
        validator_ref = f"validator://live-pilot-{envelope.attempt_id}"
        validator_digest = validation.result_digest if validation.status == "PASS" else "UNRECOVERED"
    else:
        validator_status = "UNKNOWN" if evidence == "INCOMPLETE" else "NOT_RUN"
        validator_ref = None
        validator_digest = "UNRECOVERED" if evidence == "INCOMPLETE" else "NOT_APPLICABLE"
    runtime_receipt = process.runtime_scratch_receipt if process is not None else None
    runtime_digest = sha256_json(runtime_receipt) if isinstance(runtime_receipt, Mapping) else "UNRECOVERED"
    reconciliation = receipt.reconciliation_status
    if reconciliation == "OPEN":
        reconciliation = "REQUIRES_RECONCILIATION"
    return {
        "task_id": envelope.task_id,
        "dispatch_id": envelope.dispatch_id,
        "attempt_id": envelope.attempt_id,
        "executor_id": receipt.executor_id,
        "adapter_id": receipt.adapter_id,
        "executor_version": lease.executor_version,
        "capability_lease_digest": lease.lease_digest,
        "lease_binding_status": "BOUND",
        "workspace_ref": envelope.workspace_ref,
        "workspace_digest_before": receipt.workspace_before_digest,
        "workspace_digest_after": receipt.workspace_after_digest,
        "runtime_scratch_lifecycle_digest": runtime_digest,
        "started_at": receipt.started_at,
        "ended_at": receipt.ended_at,
        "process": {
            "state": ledger_state,
            "return_code": receipt.exit_code,
            "timed_out": receipt.timed_out,
            "signal": receipt.signals_sent[-1] if receipt.signals_sent else None,
            "cleanup_status": _process_group_cleanup(receipt.process_group_status),
            "process_group_status": receipt.process_group_status,
        },
        "public_events": {
            "capture_ref": capture_ref,
            "capture_digest": capture_digest,
            "event_count": event_count,
            "capture_completeness": evidence,
            "stdout_digest": stdout_digest,
            "stderr_digest": stderr_digest,
            "stdout_byte_count": stdout_bytes,
            "stderr_byte_count": stderr_bytes,
        },
        "structured_result": {"present": structured_present, "ref": structured_ref, "digest": structured_digest},
        "validator": {"status": validator_status, "ref": validator_ref, "digest": validator_digest},
        "reconciliation_status": reconciliation,
        "evidence_completeness": evidence,
        "claim_ceiling": "Task139 canonical host observation and independent synthetic validation only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
        "source_refs": [f"live://{envelope.task_id}/{envelope.dispatch_id}"],
        "history_classification": "CURRENT_ATTEMPT",
    }


def run_once() -> dict[str, Any]:
    ledger = LiveAttemptLedger(LEDGER_PATH)
    existing = ledger.records()
    if any(record["task_id"] == TASK_ID for record in existing):
        raise SingleLiveAttemptError("Task139 already has a ledger attempt; refusing any second live dispatch")
    projection = json.loads(PROJECTION_PATH.read_text(encoding="utf-8"))
    projection_summary = validate_projection(projection)
    if projection["obligation"]["state"] != "OPEN" or projection["counts"]["validated_completion_count"] != 0:
        raise SingleLiveAttemptError("Current projection no longer admits the single bounded attempt")
    census = validate_path(ROOT / "data/operations/iterations/139/local-executor-census-r1.json", expected_task_id=TASK_ID, expected_step="09")
    if census["selected_executor_id"] != "external.codex" or census["selection_status"] != "SELECTED":
        raise SingleLiveAttemptError("fresh census no longer selects external.codex")

    capture_parent = Path(tempfile.mkdtemp(prefix="pointfire-task139-capture-"))
    retain_capture = False
    try:
        with tempfile.TemporaryDirectory(prefix="ignition-139-live-episode-") as directory:
            root = Path(directory)
            workspace_parent = root / "fixture-parent"
            runtime_parent = root / "runtime-parent"
            for path in (workspace_parent, runtime_parent):
                path.mkdir()
            fixture = DisposableLiveFixture.create(workspace_parent, nonce="abcdef0123456789abcdef01")
            schema_path = _schema_path(fixture)
            try:
                fixture.make_read_only()
                transport = RecordingTransport(LiveProcessTransport(
                    executable_allowlist=(str(CODEX),),
                    env_allowlist=CHILD_ENV_ALLOWLIST,
                    output_cap_bytes=128 * 1024,
                    capture_output_cap_bytes=16 * 1024 * 1024,
                ))
                adapter = __import__("agent_federation.live_adapters", fromlist=["LiveCodexAdapter"]).LiveCodexAdapter(
                    fixture.root,
                    executable=str(CODEX),
                    transport=transport,
                    authentication_observed=True,
                    adapter_id=ADAPTER_ID,
                    child_context=LiveChildContext(depth=0),
                    runtime_scratch_required=True,
                    runtime_scratch_parent=runtime_parent,
                    capture_parent=capture_parent,
                    formal_repo=REPO_ROOT,
                    control_repo=CONTROL_REPO,
                    persistent_user_document_roots=(DOCUMENT_ROOT,),
                    auth_source_path=AUTH_SOURCE,
                    auth_source_ref="auth://codex-login-status",
                )
                observed_at, expires_at = _now()
                lease = adapter.observe_lease(
                    lease_id=LEASE_ID,
                    observed_at=observed_at,
                    expires_at=expires_at,
                    ttl_seconds=900,
                )
                if lease.live_eligibility != "ELIGIBLE_FOR_LIVE_READONLY":
                    raise SingleLiveAttemptError("fresh Codex lease is not eligible: " + ",".join(lease.eligibility_blockers))
                envelope = _envelope(
                    lease,
                    fixture,
                    schema_path,
                    observed_at,
                    expires_at,
                    dispatch_id=DISPATCH_ID,
                    attempt_id=ATTEMPT_ID,
                    phase="step11-single-live-attempt",
                )
                admission = LiveCapabilityAdmission().admit(
                    envelope,
                    lease,
                    os_granted=("repo.read",),
                    executor_declared=("repo.read", "structured_progress"),
                    now_observed=observed_at,
                    current_binary_digest=lease.binary_digest,
                    current_interface_digest=lease.interface_digest,
                )
                if admission.status != "ADMITTED" or admission.effective_capabilities != ("repo.read",):
                    raise SingleLiveAttemptError("fresh strict capability admission was rejected")
                coordinator = _coordinator(root, envelope, admission, observed_at)
                validator = LivePilotValidator(
                    fixture,
                    task_id=TASK_ID,
                    dispatch_id=DISPATCH_ID,
                    attempt_id=ATTEMPT_ID,
                    executor_id="external.codex",
                )
                invocation_started_at, _ = _now()
                observation_error: str | None = None
                result: LiveAttemptResult | None = None
                receipt: LiveExecutorReceipt
                validation: Any = None
                capture_capsule: Mapping[str, Any] | None = None
                try:
                    result = execute_bounded_attempt(
                        adapter=adapter,
                        envelope=envelope,
                        coordinator=coordinator,
                        fixture=fixture,
                        validator=validator,
                        observed_at=observed_at,
                        capability_lease_digest=lease.lease_digest,
                        child_depth=1,
                    )
                    receipt = result.receipt
                    validation = result.validation
                    capture_capsule = result.capture_capsule
                except Exception as exc:  # one crossing only; convert observation loss into a ledger fact
                    observation_error = type(exc).__name__
                    live_process = transport.last_result if transport.live_dispatch_calls == 1 else None
                    if coordinator.plan is not None:
                        duration = live_process.duration_ms / 1000.0 if live_process is not None else 0.0
                        try:
                            coordinator.timeout_ambiguous(
                                reason="adapter observation failed closed after the single live boundary",
                                actual_cost=CostVector(action_count=1, wall_clock_seconds=min(90.0, max(0.0, duration)), output_bytes=1, event_volume=1),
                            )
                        except Exception:
                            observation_error = observation_error + "+COORDINATOR_RECONCILIATION_UNPROVEN"
                    receipt = _fallback_receipt(
                        envelope=envelope,
                        lease_digest=lease.lease_digest,
                        fixture=fixture,
                        process=live_process,
                        started_at=invocation_started_at,
                        ended_at=_now()[0],
                    )
                    capture_capsule = live_process.capture_capsule if live_process is not None else None
                record_input = _ledger_record(
                    envelope=envelope,
                    lease=lease,
                    receipt=receipt,
                    validation=validation,
                    capture_capsule=capture_capsule,
                    process=live_process,
                    ledger_state_override="OBSERVATION_INCOMPLETE" if observation_error and not receipt.timed_out else None,
                )
                try:
                    record = ledger.append(
                        record_input,
                        expected_task_id=TASK_ID,
                        expected_executor_id="external.codex",
                        expected_lease_digest=lease.lease_digest,
                    )
                except LiveAttemptLedgerError as exc:
                    raise SingleLiveAttemptError("single live receipt could not be durably appended: " + type(exc).__name__) from exc
                retain_capture = record["evidence_completeness"] == "INCOMPLETE" and capture_capsule is not None
                if retain_capture:
                    capture_parent.chmod(stat.S_IRWXU)
                return {
                    "status": "ATTEMPT_RECORDED",
                    "task_id": TASK_ID,
                    "dispatch_id": DISPATCH_ID,
                    "attempt_id": ATTEMPT_ID,
                    "executor_id": receipt.executor_id,
                    "adapter_id": receipt.adapter_id,
                    "lease_id": lease.lease_id,
                    "lease_digest": lease.lease_digest,
                    "executor_version": lease.executor_version,
                    "binary_digest": lease.binary_digest,
                    "interface_digest": lease.interface_digest,
                    "receipt_digest": receipt.receipt_digest,
                    "state": receipt.state,
                    "success": bool(result and result.success),
                    "validator_status": validation.status if validation is not None else "UNKNOWN",
                    "evidence_completeness": record["evidence_completeness"],
                    "capture_completeness": record["public_events"]["capture_completeness"],
                    "capture_ref": record["public_events"]["capture_ref"],
                    "capture_retention": "RETAINED_FOR_RECONCILIATION" if retain_capture else "RAW_SPOOL_CLEANED_AFTER_DURABLE_RECEIPT",
                    "capture_parent_separate_from_runtime": True,
                    "public_probe_calls": 2,
                    "live_dispatch_calls": transport.live_dispatch_calls,
                    "live_inference_started": transport.live_dispatch_calls == 1,
                    "structured_result": dict(receipt.structured_result) if receipt.structured_result is not None else None,
                    "process": {
                        "return_code": receipt.exit_code,
                        "timed_out": receipt.timed_out,
                        "output_truncated": bool(live_process and live_process.output_truncated),
                        "process_group_status": receipt.process_group_status,
                        "elapsed_seconds": receipt.elapsed_seconds,
                    },
                    "ledger": {
                        "sequence": record["sequence"],
                        "record_hash": record["record_hash"],
                        "previous_record_hash": record["previous_record_hash"],
                    },
                    "current_before_attempt": {
                        "projection_digest": projection_summary["projection_digest"],
                        "total_attempts": projection_summary["counts"]["total_attempts"],
                        "validated_completion_count": projection_summary["counts"]["validated_completion_count"],
                        "unreconciled_count": projection_summary["counts"]["unreconciled_count"],
                    },
                    "observation_error_class": observation_error,
                    "claim_ceiling": "One canonical Task139 host observation was durably appended; independent Current projection and validator interpretation remain Step12 evidence, with no external truth or completion upgrade inferred.",
                }
            finally:
                if schema_path.exists():
                    schema_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
                    schema_path.unlink()
                fixture.cleanup()
    finally:
        if not retain_capture and capture_parent.exists():
            shutil.rmtree(capture_parent)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="cross the one authorized external process boundary")
    args = parser.parse_args()
    if not args.live:
        parser.error("--live is required; no external process is started without the explicit live mode")
    try:
        result = run_once()
    except (SingleLiveAttemptError, LiveAttemptLedgerError, OSError, ValueError) as exc:
        print(f"LIVE_ATTEMPT_NOT_RECORDED\n- {type(exc).__name__}")
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
