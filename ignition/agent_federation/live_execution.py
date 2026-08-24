"""One bounded live-attempt runner shared by dry-run and real pilot evidence."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json
from agent_runtime.accounting import CostVector
from agent_runtime.dispatch_reconciliation import DispatchReceipt

from .live_adapters import LiveAdapterObservation
from .live_bridge import LiveDispatchEnvelope, LiveDispatchStateMachine, LiveExecutorReceipt
from .live_orchestration import LiveDispatchCoordinator
from .live_pilot import LivePilotValidator, LiveValidationReport
from .live_privacy import LivePrivacyError, sanitize_live_result, sanitize_public_summary


LIVE_EXECUTION_SCHEMA = "ignition-136-live-execution-r1"
_RESULT_KEYS = ("nonce", "line_count", "field_value", "checksum_prefix")


class LiveExecutionError(RuntimeError):
    """Raised when bounded live execution cannot produce a safe attempt record."""


@dataclass(frozen=True)
class LiveAttemptResult:
    observation: LiveAdapterObservation
    receipt: LiveExecutorReceipt
    validation: LiveValidationReport | None
    state_history: tuple[Mapping[str, Any], ...]
    durable_record: Mapping[str, Any]
    claim_ceiling: str = "Bounded executor observation plus independent synthetic validation only; no Goal completion or external truth is inferred."

    @property
    def success(self) -> bool:
        return self.receipt.state == "COMPLETED_VALIDATED" and self.validation is not None and self.validation.status == "PASS"

    def to_dict(self) -> dict[str, Any]:
        durable_state = self.durable_record.get("state")
        if durable_state is None and isinstance(self.durable_record.get("record"), Mapping):
            durable_state = self.durable_record["record"].get("state")
        return {
            "schema": LIVE_EXECUTION_SCHEMA,
            "executor_id": self.receipt.executor_id,
            "adapter_id": self.receipt.adapter_id,
            "state": self.receipt.state,
            "success": self.success,
            "receipt": self.receipt.to_dict(),
            "validation": self.validation.to_dict() if self.validation else None,
            "state_history": [dict(item) for item in self.state_history],
            "durable_record_state": durable_state,
            "claim_ceiling": self.claim_ceiling,
        }


def _candidate_objects(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for item in value.values():
            yield from _candidate_objects(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _candidate_objects(item)


def _extract_structured_result(events: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    for event in _candidate_objects(events):
        if set(_RESULT_KEYS).issubset(event):
            return {key: event[key] for key in _RESULT_KEYS}
        for key in ("text", "content", "message"):
            text = event.get(key)
            if not isinstance(text, str) or not text.strip():
                continue
            try:
                parsed = json.loads(text.strip())
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, Mapping) and set(_RESULT_KEYS).issubset(parsed):
                return {key: parsed[key] for key in _RESULT_KEYS}
    raise LiveExecutionError("public events did not contain the exact synthetic result object")


def _cost(observation: LiveAdapterObservation, timeout_seconds: float) -> CostVector:
    duration = max(0.0, min(float(timeout_seconds), float(observation.process.duration_ms) / 1000.0))
    return CostVector(action_count=1, wall_clock_seconds=duration, output_bytes=1, event_volume=1)


def _safe_summary(observation: LiveAdapterObservation) -> str:
    try:
        return sanitize_public_summary(observation.summary)
    except LivePrivacyError:
        return "PUBLIC_SUMMARY_REDACTED"


def _transport_evidence(process: Any, *, observed_at: str, timeout_seconds: float) -> dict[str, Any]:
    elapsed_ms = process.monotonic_elapsed_ms if process.monotonic_elapsed_ms is not None else process.duration_ms
    process_timeout = process.timeout_seconds if process.timeout_seconds > 0 else timeout_seconds
    group_status = process.process_group_status
    if group_status == "UNKNOWN" and process.process_group_cleaned:
        group_status = "CONFIRMED_GONE"
    stdout_bytes = process.stdout_bytes if process.stdout_bytes is not None else len(process.stdout.encode("utf-8"))
    stderr_bytes = process.stderr_bytes if process.stderr_bytes is not None else len(process.stderr.encode("utf-8"))
    first_event_ms = process.first_public_event_latency_ms
    return {
        "started_at": process.started_at or observed_at,
        "ended_at": process.ended_at or observed_at,
        "elapsed_seconds": max(0.0, float(elapsed_ms) / 1000.0),
        "timeout_seconds": float(process_timeout),
        "timeout_requested": bool(process.timeout_requested or process.timed_out),
        "termination_requested": bool(process.termination_requested or process.timed_out or process.output_truncated),
        "signals_sent": tuple(process.signals_sent),
        "process_group_status": group_status,
        "first_public_event_latency_seconds": None if first_event_ms is None else max(0.0, float(first_event_ms) / 1000.0),
        "stdout_byte_count": max(0, int(stdout_bytes)),
        "stderr_byte_count": max(0, int(stderr_bytes)),
        "stdout_digest": process.stdout_digest,
        "stderr_digest": process.stderr_digest,
    }


def execute_bounded_attempt(
    *,
    adapter: Any,
    envelope: LiveDispatchEnvelope,
    coordinator: LiveDispatchCoordinator,
    fixture: Any,
    validator: LivePilotValidator,
    observed_at: str,
    capability_lease_digest: str | None = None,
    child_depth: int | None = None,
) -> LiveAttemptResult:
    """Execute at most one adapter process and close its OS-owned evidence."""

    machine = LiveDispatchStateMachine(envelope, observed_at=observed_at)
    machine.admit(allowed=True, reason="Step 11 live preflight admitted bounded read-only capability")
    machine.begin_dispatch()
    coordinator.start()
    machine.mark_in_flight()
    before_digest = fixture.current_digest()
    observation = adapter.dispatch(envelope)
    after_digest = fixture.current_digest()
    side_effect_observation = "READ_ONLY_UNCHANGED" if before_digest == after_digest and fixture.read_only_guard_observed() else "FORBIDDEN_EFFECT_OBSERVED"
    transport_evidence = _transport_evidence(observation.process, observed_at=observed_at, timeout_seconds=envelope.timeout_seconds)
    validation: LiveValidationReport | None = None

    if observation.process.timed_out:
        machine.mark_timeout(effect_known_no_effect=False)
        durable = coordinator.timeout_ambiguous(reason="live process timeout has unknown external outcome", actual_cost=_cost(observation, envelope.timeout_seconds))
        final_state = machine.state
        structured = None
        os_validation = "NOT_RUN"
        reconciliation = "OPEN"
    else:
        try:
            if not observation.parsed or observation.process.returncode != 0:
                machine.record_executor_return(parsed=False, returncode=observation.process.returncode)
                final_state = machine.state
                structured = None
                os_validation = "FAIL"
                reconciliation = "NOT_REQUIRED"
            else:
                machine.record_executor_return(parsed=True, returncode=observation.process.returncode)
                try:
                    raw_result = _extract_structured_result(observation.parsed_events)
                    structured = sanitize_live_result(raw_result, allowed_keys=_RESULT_KEYS).value
                except (LiveExecutionError, LivePrivacyError):
                    machine.transition("MALFORMED_RESULT", "structured result failed exact extraction or privacy gate")
                    final_state = machine.state
                    structured = None
                    os_validation = "FAIL"
                    reconciliation = "NOT_REQUIRED"
                else:
                    machine.start_validation()
                    validation = validator.validate(structured, before_digest=before_digest, after_digest=after_digest, side_effect_observation=side_effect_observation)
                    machine.finish_validation(
                        passed=validation.status == "PASS",
                        workspace_unchanged=validation.checks.get("tree_unchanged", False),
                        no_forbidden_effect=validation.checks.get("side_effect_free", False),
                    )
                    final_state = machine.state
                    os_validation = "PASS" if validation.status == "PASS" else "FAIL"
                    reconciliation = "NOT_REQUIRED"
        except Exception:
            # The process result remains bounded; preserve a safe machine state
            # and let the durable failed receipt carry only public evidence.
            if machine.state in {"RETURNED_UNVALIDATED", "VALIDATING"}:
                machine.transition("MALFORMED_RESULT", "bounded result handling failed closed")
            final_state = machine.state
            structured = None
            os_validation = "FAIL"
            reconciliation = "NOT_REQUIRED"

        receipt = LiveExecutorReceipt.build(
            task_id=envelope.task_id, dispatch_id=envelope.dispatch_id, attempt_id=envelope.attempt_id,
            executor_id=observation.executor_id, adapter_id=observation.adapter_id, state=final_state,
            exit_code=observation.process.returncode,
            timed_out=observation.process.timed_out, cancel_state="NOT_REQUESTED", event_count=len(observation.parsed_events),
            sanitized_event_summary=_safe_summary(observation), response_digest=observation.response_digest,
            structured_result=structured, session_pointer=observation.session_pointer,
            side_effect_class=envelope.side_effect_class, side_effect_observation=side_effect_observation,
            workspace_before_digest=before_digest, workspace_after_digest=after_digest,
            os_validation_status=os_validation, reconciliation_status=reconciliation,
            claim_ceiling="Executor result is unvalidated until the independent fixture validator passes.",
            **transport_evidence,
            workspace_ref=envelope.workspace_ref,
            capability_lease_digest=capability_lease_digest,
            result_digest=sha256_json(structured) if structured is not None else None,
            child_depth=child_depth,
        )
        old_receipt = DispatchReceipt(
            envelope.dispatch_id, envelope.task_id, envelope.executor_id, f"live-idempotency-{envelope.dispatch_id}",
            0, "COMPLETED" if receipt.state == "COMPLETED_VALIDATED" else "FAILED",
            "bounded live receipt recorded for independent validation", (validation.result_digest if validation else receipt.receipt_digest),
            0.0,
        )
        durable = coordinator.finalize_receipt(old_receipt, passed=receipt.state == "COMPLETED_VALIDATED", validation_ref="live-pilot-validator-136", actual_cost=_cost(observation, envelope.timeout_seconds))

    if observation.process.timed_out:
        receipt = LiveExecutorReceipt.build(
            task_id=envelope.task_id, dispatch_id=envelope.dispatch_id, attempt_id=envelope.attempt_id,
            executor_id=observation.executor_id, adapter_id=observation.adapter_id, state=final_state,
            exit_code=observation.process.returncode,
            timed_out=True, cancel_state="UNKNOWN", event_count=len(observation.parsed_events),
            sanitized_event_summary=_safe_summary(observation), response_digest=observation.response_digest,
            structured_result=None, session_pointer=observation.session_pointer,
            side_effect_class=envelope.side_effect_class, side_effect_observation=side_effect_observation,
            workspace_before_digest=before_digest, workspace_after_digest=after_digest,
            os_validation_status="NOT_RUN", reconciliation_status="OPEN",
            claim_ceiling="Timeout outcome is unresolved; no retry or completion is inferred.",
            **transport_evidence,
            workspace_ref=envelope.workspace_ref,
            capability_lease_digest=capability_lease_digest,
            result_digest=None,
            child_depth=child_depth,
        )

    return LiveAttemptResult(receipt and observation, receipt, validation, tuple(item.to_dict() for item in machine.history), durable,)


__all__ = ["LIVE_EXECUTION_SCHEMA", "LiveAttemptResult", "LiveExecutionError", "execute_bounded_attempt"]
