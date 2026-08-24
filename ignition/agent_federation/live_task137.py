"""Task137 envelope, OS coordinator and one-attempt live pilot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json
from agent_runtime.accounting import AccountingPolicy, AccountingStore, BudgetScope, CostVector
from agent_runtime.dispatch_reconciliation import DispatchReceipt, DurableDispatchStore
from agent_runtime.event_ledger import EventLedger
from agent_runtime.queue_control import WorkQueue
from agent_runtime.resource_arbitration import ResourceArbiter
from agent_runtime.steering import IntentCapsule

from .live_admission import LiveAdmissionDecision
from .live_bridge import LiveCapabilityLease, LiveDispatchEnvelope, LiveDispatchStateMachine, LiveExecutorReceipt, LIVE_DISPATCH_SCHEMA
from .live_execution import LiveExecutionError, _cost, _safe_summary, _transport_evidence
from .live_orchestration import LiveDispatchCoordinator, LiveSteeringBinding
from .live_pilot import DisposableLiveCompletionFixture, LiveValidationReport
from .live_privacy import LivePrivacyError, sanitize_live_result
from .live_validation import IndependentValidationReceipt, LiveIndependentValidator


TASK137_ID = "IGNITION-20260824-137"
TASK137_FIXTURE_SCHEMA = "ignition-137-live-pilot-r1"
TASK137_RESULT_KEYS = ("nonce", "selected_ids", "count", "workspace_digest_claim")
TASK137_SURFACE_KEYS = ("channel", "browser", "remote_git", "user_data", "formal_repo_mutation", "billing_authority")
TASK137_EXECUTION_SCHEMA = "ignition-137-live-execution-r1"


def task137_input_digest() -> str:
    return sha256_json({
        "task_id": TASK137_ID,
        "fixture_schema": TASK137_FIXTURE_SCHEMA,
        "read_only": True,
        "rule": {"eligible": True, "minimum_score": 50, "sort": ["score", "id"]},
        "output_keys": list(TASK137_RESULT_KEYS),
    })


def build_task137_envelope(
    *,
    schema_path: str | Path,
    observed_at: str,
    dispatch_id: str = "live-dispatch-137",
    attempt_id: str = "live-attempt-137",
    timeout_seconds: float = 900.0,
) -> LiveDispatchEnvelope:
    observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    deadline = (observed + timedelta(seconds=timeout_seconds)).isoformat()
    schema_ref = str(Path(schema_path).resolve())
    criteria = (
        "Read README.txt, nonce.txt and table.json from the disposable fixture only.",
        "Select rows with eligible=true and score>=50, then sort by score ascending and id ascending.",
        "Return exactly the four public JSON fields required by the output schema and no commentary.",
    )
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA,
        task_id=TASK137_ID,
        dispatch_id=dispatch_id,
        attempt_id=attempt_id,
        executor_id="external.codex",
        adapter_id="codex-live-r2",
        capability_id="live.readonly.synthetic",
        capability_lease_ref="live-codex-137-attempt-lease",
        workspace_ref="DISPOSABLE_LIVE_FIXTURE_137",
        workspace_mode="DISPOSABLE_READ_ONLY",
        permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC",
        network_class="INFERENCE_TRANSPORT_ONLY",
        intent_capsule_ref="capsule:intent-137:goal-137",
        synthetic_input_ref="fixture://IGNITION-20260824-137",
        synthetic_input_digest=task137_input_digest(),
        success_criteria=criteria,
        output_contract={
            "format": "json",
            "required_fields": list(TASK137_RESULT_KEYS),
            "strict_output_schema": True,
            "schema_path": schema_ref,
            "additionalProperties": False,
        },
        deadline=deadline,
        timeout_seconds=timeout_seconds,
        retry_policy="NO_BLIND_RETRY",
        reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY",
        provenance={
            "controller": "pointfire-os",
            "current_agent_is_external_executor": False,
            "child_depth": 1,
            "parent_prompt_forwarded": False,
            "formal_task_context_forwarded": False,
            "real_user_data": False,
            "channel": False,
            "browser": False,
            "remote_git": False,
            "billing_authority": "NO_NEW_BILLING_AUTHORITY",
        },
    )


def build_task137_steering(observed_at: str) -> LiveSteeringBinding:
    criteria = (
        "Read only the disposable Task137 fixture.",
        "Return the exact independently verifiable synthetic result.",
    )
    capsule = IntentCapsule(
        capsule_id="capsule:intent-137:goal-137",
        intent_id="intent-137",
        goal_id="goal-137",
        intent_summary="Bounded validation of one synthetic read-only executor result",
        goal_summary="Produce one independently verifiable Task137 fixture result",
        success_criteria=criteria,
        permission_summary=("repo.read",),
        blocker_refs=(),
        temporal_refs=(),
        report_contract_refs=("live-validation-receipt-137",),
        minimal_context_refs=("fixture://IGNITION-20260824-137",),
        namespace_ref="namespace-live-137",
        created_at=observed_at,
    )
    scope = BudgetScope(
        principal_id="principal-live-137",
        namespace_id="namespace-live-137",
        workspace_id="DISPOSABLE_READ_ONLY",
        episode_id="episode-live-137",
        pack_id="pack-live-137",
        executor_id="external.codex",
    )
    return LiveSteeringBinding(
        capsule=capsule,
        why_next_ref="why-next-137",
        priority=7,
        profile_ref="profile-live-137",
        project_ref=TASK137_ID,
        budget_scope=scope,
    )


def _task137_accounting_policy() -> AccountingPolicy:
    identifiers = {
        "principal": "principal-live-137",
        "namespace": "namespace-live-137",
        "workspace": "DISPOSABLE_READ_ONLY",
        "episode": "episode-live-137",
        "pack": "pack-live-137",
        "executor": "external.codex",
    }
    limit = CostVector(action_count=4, wall_clock_seconds=1800, output_bytes=200_000, event_volume=50)
    return AccountingPolicy(
        limits={f"{dimension}:{identifier}": limit for dimension, identifier in identifiers.items()},
        workspace_namespace={"DISPOSABLE_READ_ONLY": "namespace-live-137"},
    )


def build_task137_coordinator(
    root: str | Path,
    *,
    envelope: LiveDispatchEnvelope,
    steering: LiveSteeringBinding,
    admission: LiveAdmissionDecision,
    now_epoch: float,
) -> LiveDispatchCoordinator:
    state = Path(root)
    state.mkdir(parents=True, exist_ok=True)
    return LiveDispatchCoordinator(
        envelope=envelope,
        steering=steering,
        admission=admission,
        queue=WorkQueue(state / "queue.json", max_depth=2, profile_limits={"profile-live-137": 1}),
        resources=ResourceArbiter(state / "resources.json"),
        accounting=AccountingStore(state / "accounting.json", _task137_accounting_policy()),
        dispatch_store=DurableDispatchStore(state / "dispatch.json"),
        ledger=EventLedger(state / "events.jsonl"),
        clock=lambda: now_epoch,
    )


def _candidate_objects(value: Any):
    if isinstance(value, Mapping):
        yield value
        for item in value.values():
            yield from _candidate_objects(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _candidate_objects(item)


def _extract_task137_result(events: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    expected = set(TASK137_RESULT_KEYS)
    for event in _candidate_objects(events):
        if set(event) == expected:
            return {key: event[key] for key in TASK137_RESULT_KEYS}
        for key in ("text", "content", "message"):
            text = event.get(key)
            if not isinstance(text, str) or not text.strip():
                continue
            try:
                parsed = json.loads(text.strip())
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, Mapping) and set(parsed) == expected:
                return {key: parsed[key] for key in TASK137_RESULT_KEYS}
    raise LiveExecutionError("public events did not contain the exact Task137 result object")


def task137_external_surface_evidence(envelope: LiveDispatchEnvelope, observation: Any, fixture: DisposableLiveCompletionFixture) -> dict[str, bool]:
    process = observation.process
    argv = tuple(process.argv)
    flags = set(argv[:-1]) if argv else set()
    safe_argv = (
        argv
        and argv[0] == "/Users/zhiyuan/.local/bin/codex"
        and "--json" in flags
        and "--ephemeral" in flags
        and "--ignore-user-config" in flags
        and "--ignore-rules" in flags
        and "--skip-git-repo-check" in flags
        and "--sandbox" in flags
        and "read-only" in argv
        and "--output-schema" in flags
        and "--add-dir" not in flags
        and "--dangerously-bypass-approvals-and-sandbox" not in flags
        and "workspace-write" not in flags
    )
    safe_workspace = Path(process.cwd).resolve() == fixture.root.resolve()
    safe = bool(safe_argv and safe_workspace)
    return {
        "channel": not safe,
        "browser": not safe,
        "remote_git": not safe,
        "user_data": not safe_workspace,
        "formal_repo_mutation": not safe_workspace,
        "billing_authority": envelope.budget_authority != "NO_NEW_BILLING_AUTHORITY",
    }


@dataclass(frozen=True)
class Task137AttemptResult:
    observation: Any
    executor_receipt: LiveExecutorReceipt
    unvalidated_receipt: LiveExecutorReceipt | None
    validation_receipt: IndependentValidationReceipt | None
    fixture_report: LiveValidationReport | None
    state_history: tuple[Mapping[str, Any], ...]
    durable_record: Mapping[str, Any]
    claim_ceiling: str = "One bounded Task137 synthetic executor attempt plus independent OS validation only; no Goal completion, production readiness or external truth is inferred."

    @property
    def success(self) -> bool:
        return bool(
            self.executor_receipt.state == "COMPLETED_VALIDATED"
            and self.validation_receipt is not None
            and self.validation_receipt.status == "PASS"
            and self.fixture_report is not None
            and self.fixture_report.status == "PASS"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": TASK137_EXECUTION_SCHEMA,
            "task_id": TASK137_ID,
            "success": self.success,
            "executor_receipt": self.executor_receipt.to_dict(),
            "unvalidated_receipt": self.unvalidated_receipt.to_dict() if self.unvalidated_receipt else None,
            "validation_receipt": self.validation_receipt.to_dict() if self.validation_receipt else None,
            "fixture_report": self.fixture_report.to_dict() if self.fixture_report else None,
            "state_history": [dict(item) for item in self.state_history],
            "durable_record": dict(self.durable_record),
            "claim_ceiling": self.claim_ceiling,
        }


def _receipt(
    *,
    envelope: LiveDispatchEnvelope,
    observation: Any,
    state: str,
    before_digest: str,
    after_digest: str,
    structured_result: Mapping[str, Any] | None,
    transport_evidence: Mapping[str, Any],
    lease_digest: str,
    os_validation_status: str,
    reconciliation_status: str,
    cancel_state: str,
    side_effect_observation: str,
    child_depth: int,
    validator_receipt_digest: str | None = None,
    claim_ceiling: str,
) -> LiveExecutorReceipt:
    return LiveExecutorReceipt.build(
        task_id=envelope.task_id,
        dispatch_id=envelope.dispatch_id,
        attempt_id=envelope.attempt_id,
        executor_id=observation.executor_id,
        adapter_id=observation.adapter_id,
        state=state,
        exit_code=observation.process.returncode,
        timed_out=observation.process.timed_out,
        cancel_state=cancel_state,
        event_count=len(observation.parsed_events),
        sanitized_event_summary=_safe_summary(observation),
        response_digest=observation.response_digest,
        structured_result=structured_result,
        session_pointer=observation.session_pointer,
        side_effect_class=envelope.side_effect_class,
        side_effect_observation=side_effect_observation,
        workspace_before_digest=before_digest,
        workspace_after_digest=after_digest,
        os_validation_status=os_validation_status,
        reconciliation_status=reconciliation_status,
        claim_ceiling=claim_ceiling,
        workspace_ref=envelope.workspace_ref,
        capability_lease_digest=lease_digest,
        result_digest=sha256_json(structured_result) if structured_result is not None else None,
        validator_receipt_digest=validator_receipt_digest,
        child_depth=child_depth,
        **dict(transport_evidence),
    )


def _finalize_failure(
    *,
    machine: LiveDispatchStateMachine,
    coordinator: LiveDispatchCoordinator,
    envelope: LiveDispatchEnvelope,
    observation: Any,
    receipt: LiveExecutorReceipt,
    validation_ref: str,
) -> Mapping[str, Any]:
    old_receipt = DispatchReceipt(
        envelope.dispatch_id,
        envelope.task_id,
        envelope.executor_id,
        f"live-idempotency-{envelope.dispatch_id}",
        0,
        "FAILED",
        "bounded Task137 result did not establish validated completion",
        receipt.receipt_digest,
        time.time(),
    )
    return coordinator.finalize_receipt(
        old_receipt,
        passed=False,
        validation_ref=validation_ref,
        actual_cost=_cost(observation, envelope.timeout_seconds),
    )


def execute_task137_attempt(
    *,
    adapter: Any,
    envelope: LiveDispatchEnvelope,
    coordinator: LiveDispatchCoordinator,
    fixture: DisposableLiveCompletionFixture,
    lease: LiveCapabilityLease,
    observed_at: str,
) -> Task137AttemptResult:
    """Start exactly one bounded process and never replay an unknown outcome."""

    machine = LiveDispatchStateMachine(envelope, observed_at=observed_at)
    machine.admit(allowed=True, reason="Task137 dry-run gate admitted the bounded read-only capability")
    machine.begin_dispatch()
    coordinator.start()
    machine.mark_in_flight()
    before_digest = fixture.current_digest()
    observation = adapter.dispatch(envelope)
    after_digest = fixture.current_digest()
    transport_evidence = _transport_evidence(observation.process, observed_at=observed_at, timeout_seconds=envelope.timeout_seconds)
    side_effect_free = before_digest == after_digest and fixture.read_only_guard_observed()
    child_depth = 1

    if observation.process.timed_out:
        machine.mark_timeout(effect_known_no_effect=False)
        durable = coordinator.timeout_ambiguous(
            reason="Task137 Codex bounded process timed out; cancellation/effect remains unknown",
            actual_cost=_cost(observation, envelope.timeout_seconds),
        )
        receipt = _receipt(
            envelope=envelope,
            observation=observation,
            state=machine.state,
            before_digest=before_digest,
            after_digest=after_digest,
            structured_result=None,
            transport_evidence=transport_evidence,
            lease_digest=lease.lease_digest,
            os_validation_status="NOT_RUN",
            reconciliation_status="OPEN",
            cancel_state="UNKNOWN",
            side_effect_observation="UNKNOWN",
            child_depth=child_depth,
            claim_ceiling="Task137 process timed out with unknown effect; no retry or completion is inferred.",
        )
        return Task137AttemptResult(observation, receipt, None, None, None, tuple(item.to_dict() for item in machine.history), durable)

    structured: Mapping[str, Any] | None = None
    if not observation.parsed or observation.process.returncode != 0:
        machine.record_executor_return(parsed=False, returncode=observation.process.returncode)
    else:
        machine.record_executor_return(parsed=True, returncode=observation.process.returncode)
        try:
            structured = sanitize_live_result(
                _extract_task137_result(observation.parsed_events),
                allowed_keys=TASK137_RESULT_KEYS,
            ).value
        except (LiveExecutionError, LivePrivacyError):
            machine.transition("MALFORMED_RESULT", "Task137 public result failed exact extraction or privacy gate")

    if structured is None:
        receipt = _receipt(
            envelope=envelope,
            observation=observation,
            state=machine.state,
            before_digest=before_digest,
            after_digest=after_digest,
            structured_result=None,
            transport_evidence=transport_evidence,
            lease_digest=lease.lease_digest,
            os_validation_status="FAIL",
            reconciliation_status="NOT_REQUIRED",
            cancel_state="NOT_REQUESTED",
            side_effect_observation="READ_ONLY_UNCHANGED" if side_effect_free else "FORBIDDEN_EFFECT_OBSERVED",
            child_depth=child_depth,
            claim_ceiling="Task137 executor output was not an exact public result; no validated completion is inferred.",
        )
        durable = _finalize_failure(
            machine=machine,
            coordinator=coordinator,
            envelope=envelope,
            observation=observation,
            receipt=receipt,
            validation_ref="live-task137-validation-failed",
        )
        return Task137AttemptResult(observation, receipt, None, None, None, tuple(item.to_dict() for item in machine.history), durable)

    unvalidated = _receipt(
        envelope=envelope,
        observation=observation,
        state="RETURNED_UNVALIDATED",
        before_digest=before_digest,
        after_digest=after_digest,
        structured_result=structured,
        transport_evidence=transport_evidence,
        lease_digest=lease.lease_digest,
        os_validation_status="NOT_RUN",
        reconciliation_status="NOT_REQUIRED",
        cancel_state="NOT_REQUESTED",
        side_effect_observation="READ_ONLY_UNCHANGED" if side_effect_free else "FORBIDDEN_EFFECT_OBSERVED",
        child_depth=child_depth,
        claim_ceiling="Codex returned a public Task137 result; independent OS validation is still required.",
    )
    # Bind the lease after the unvalidated receipt is constructed, without
    # reusing any executor-supplied identity or result claim.
    unvalidated = LiveExecutorReceipt.from_dict(unvalidated.to_dict())
    machine.start_validation()
    validation_receipt, fixture_report = LiveIndependentValidator(fixture).validate(
        envelope=envelope,
        lease=lease,
        executor_receipt=unvalidated,
        result=structured,
        before_digest=before_digest,
        after_digest=after_digest,
        observed_at=observed_at,
        child_depth=child_depth,
        external_surface_evidence=task137_external_surface_evidence(envelope, observation, fixture),
        side_effect_observation="READ_ONLY_UNCHANGED" if side_effect_free else "FORBIDDEN_EFFECT_OBSERVED",
    )
    passed = validation_receipt.status == "PASS"
    machine.finish_validation(
        passed=passed,
        workspace_unchanged=validation_receipt.checks.get("workspace_unchanged", False),
        no_forbidden_effect=validation_receipt.checks.get("external_surface_clear", False) and validation_receipt.checks.get("side_effect_free", False),
    )
    final_receipt = _receipt(
        envelope=envelope,
        observation=observation,
        state=machine.state,
        before_digest=before_digest,
        after_digest=after_digest,
        structured_result=structured,
        transport_evidence=transport_evidence,
        lease_digest=lease.lease_digest,
        os_validation_status="PASS" if passed else "FAIL",
        reconciliation_status="CLOSED" if passed else "NOT_REQUIRED",
        cancel_state="NOT_REQUESTED",
        side_effect_observation="READ_ONLY_UNCHANGED" if side_effect_free else "FORBIDDEN_EFFECT_OBSERVED",
        child_depth=child_depth,
        validator_receipt_digest=validation_receipt.validator_receipt_digest,
        claim_ceiling="Pointfire independently validated one bounded synthetic read-only result; no Goal completion, production readiness or external truth is inferred.",
    )
    durable = coordinator.finalize_receipt(
        DispatchReceipt(
            envelope.dispatch_id,
            envelope.task_id,
            envelope.executor_id,
            f"live-idempotency-{envelope.dispatch_id}",
            0,
            "COMPLETED" if passed else "FAILED",
            "Task137 independent OS validation " + ("PASS" if passed else "FAIL"),
            final_receipt.receipt_digest,
            time.time(),
        ),
        passed=passed,
        validation_ref=f"live-task137-validator-{validation_receipt.validator_receipt_digest[:16]}",
        actual_cost=_cost(observation, envelope.timeout_seconds),
    )
    return Task137AttemptResult(
        observation,
        final_receipt,
        unvalidated,
        validation_receipt,
        fixture_report,
        tuple(item.to_dict() for item in machine.history),
        durable,
    )


__all__ = [
    "TASK137_EXECUTION_SCHEMA", "TASK137_FIXTURE_SCHEMA", "TASK137_ID", "TASK137_RESULT_KEYS", "TASK137_SURFACE_KEYS",
    "Task137AttemptResult", "build_task137_coordinator", "build_task137_envelope", "build_task137_steering",
    "execute_task137_attempt", "task137_external_surface_evidence", "task137_input_digest",
]
