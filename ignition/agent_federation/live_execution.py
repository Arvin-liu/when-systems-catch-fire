"""One bounded live-attempt runner shared by dry-run and real pilot evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json
from agent_runtime.accounting import CostVector
from agent_runtime.dispatch_reconciliation import DispatchReceipt

from .live_adapters import LiveAdapterObservation
from .live_bridge import LiveDispatchEnvelope, LiveDispatchStateMachine, LiveExecutorReceipt
from .failure_forensics import build_failure_forensics_capsule, classify_failure, update_spool_disposition
from .live_orchestration import LiveDispatchCoordinator
from .live_pilot import LivePilotValidator, LiveValidationReport
from .live_privacy import LivePrivacyError, sanitize_live_result, sanitize_public_summary
from .structured_result_contract import StructuredResultContractError, extract_synthetic_result


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
    capture_capsule: Mapping[str, Any] | None = None
    failure_forensics_capsule: Mapping[str, Any] | None = None

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
            "capture_capsule": dict(self.capture_capsule) if self.capture_capsule is not None else None,
            "failure_forensics_capsule": dict(self.failure_forensics_capsule) if self.failure_forensics_capsule is not None else None,
            "claim_ceiling": self.claim_ceiling,
        }


def _extract_structured_result(events: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    try:
        return extract_synthetic_result(events).value
    except StructuredResultContractError as exc:
        raise LiveExecutionError(f"{exc.code}: {exc}") from exc


def _cost(observation: LiveAdapterObservation, timeout_seconds: float) -> CostVector:
    duration = max(0.0, min(float(timeout_seconds), float(observation.process.duration_ms) / 1000.0))
    return CostVector(action_count=1, wall_clock_seconds=duration, output_bytes=1, event_volume=1)


def _safe_summary(observation: LiveAdapterObservation) -> str:
    try:
        return sanitize_public_summary(observation.summary)
    except LivePrivacyError:
        return "PUBLIC_SUMMARY_REDACTED"


def _public_error_class(value: str) -> str:
    if not value:
        return "NONE"
    upper = value.upper()
    if "JSONL" in upper or "JSON" in upper:
        return "PUBLIC_JSON_PARSE_ERROR"
    if "EXACT" in upper or "RESULT" in upper:
        return "STRUCTURED_RESULT_EXTRACTION_ERROR"
    return "PUBLIC_PARSER_ERROR"


def _auth_boundary_status(adapter: Any) -> str:
    observed = getattr(adapter, "last_auth_source_observation", None)
    if isinstance(observed, Mapping):
        return "MUTATED" if observed.get("mutated") else "UNCHANGED_REFERENCE"
    return "NOT_CONFIGURED" if getattr(adapter, "auth_source_path", None) is None else "UNKNOWN"


def _runtime_boundary_status(observation: LiveAdapterObservation) -> str:
    status = observation.runtime_scratch_cleanup_status
    if status == "CLEANED":
        return "UNCHANGED"
    if status == "NOT_USED":
        return "NOT_CONFIGURED"
    return "UNKNOWN"


def _failure_forensics(
    *,
    observation: LiveAdapterObservation,
    adapter: Any,
    envelope: LiveDispatchEnvelope,
    before_digest: str,
    after_digest: str,
    parser_status: str,
    parser_error_class: str,
    schema_status: str,
    schema_error_class: str,
    structured_output_status: str,
    structured_output_present: bool,
    diagnostic_class: str | None,
    raw_spool_retention_status: str,
    raw_spool_disposal_status: str,
) -> Mapping[str, Any]:
    process = observation.process
    cleanup_status = "CLEANED" if process.process_group_cleaned else "REQUIRES_RECONCILIATION" if process.process_group_status in {"CHILD_LEFT_BEHIND", "UNKNOWN"} else "NOT_OBSERVED"
    inference_status = "UNKNOWN" if process.returncode is None else "NOT_OBSERVED"
    return build_failure_forensics_capsule(
        task_id=envelope.task_id,
        dispatch_id=envelope.dispatch_id,
        attempt_id=envelope.attempt_id,
        executor_id=observation.executor_id,
        adapter_id=observation.adapter_id,
        executor_version=observation.version,
        interface_digest=observation.interface_digest,
        argv=process.argv,
        process_return_code=process.returncode,
        duration_ms=process.duration_ms,
        timed_out=process.timed_out,
        process_group_status=process.process_group_status,
        cleanup_status=cleanup_status,
        stdout_byte_count=process.stdout_bytes if process.stdout_bytes is not None else len(process.stdout.encode("utf-8")),
        stdout_digest=process.stdout_digest,
        stderr_byte_count=process.stderr_bytes if process.stderr_bytes is not None else len(process.stderr.encode("utf-8")),
        stderr_digest=process.stderr_digest,
        parser_status=parser_status,
        parser_error_class=parser_error_class,
        schema_status=schema_status,
        schema_error_class=schema_error_class,
        structured_output_status=structured_output_status,
        structured_output_present=structured_output_present,
        diagnostic_class=diagnostic_class,
        runtime_scratch_status=_runtime_boundary_status(observation),
        auth_source_status=_auth_boundary_status(adapter),
        workspace_status="UNCHANGED" if before_digest == after_digest else "MUTATED",
        inference_observation_status=inference_status,
        raw_spool_initialized=process.capture_writer is not None or process.capture_capsule is not None,
        raw_spool_retention_status=raw_spool_retention_status,
        raw_spool_disposal_status=raw_spool_disposal_status,
        known=("public process lifecycle was captured", "structured result presence was classified"),
        unknown=("provider-private diagnostic text", "executor-internal inference state"),
        not_inferable=("private inference execution", "external side effects beyond the bounded workspace"),
    )


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


def _close_capture(observation: LiveAdapterObservation, structured: Mapping[str, Any] | None, *, retain_for_reconciliation: bool) -> Mapping[str, Any] | None:
    """Attach the bounded result and clean raw spool only after a durable receipt exists."""

    writer = getattr(observation.process, "capture_writer", None)
    capsule = getattr(observation.process, "capture_capsule", None)
    if writer is None:
        return capsule
    if structured is not None:
        capsule = writer.attach_structured_result(structured)
    if not retain_for_reconciliation:
        capsule = writer.cleanup_spool()
    return capsule


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
    capture_capsule: Mapping[str, Any] | None = observation.process.capture_capsule
    failure_forensics_capsule: Mapping[str, Any] | None = None
    parser_status = "NOT_RUN"
    parser_error_class = "NONE"
    schema_status = "NOT_RUN"
    schema_error_class = "NONE"
    structured_output_status = "UNKNOWN"
    structured_output_present = False

    if observation.process.timed_out:
        machine.mark_timeout(effect_known_no_effect=False)
        durable = coordinator.timeout_ambiguous(reason="live process timeout has unknown external outcome", actual_cost=_cost(observation, envelope.timeout_seconds))
        final_state = machine.state
        structured = None
        os_validation = "NOT_RUN"
        reconciliation = "OPEN"
        structured_output_status = "UNKNOWN"
        failure_forensics_capsule = _failure_forensics(
            observation=observation, adapter=adapter, envelope=envelope,
            before_digest=before_digest, after_digest=after_digest,
            parser_status="UNKNOWN", parser_error_class="OBSERVATION_INCOMPLETE",
            schema_status="UNKNOWN", schema_error_class="OBSERVATION_INCOMPLETE",
            structured_output_status="UNKNOWN", structured_output_present=False,
            diagnostic_class="OBSERVATION_INCOMPLETE",
            raw_spool_retention_status="RETAINED_UNTIL_DURABLE_RECEIPT",
            raw_spool_disposal_status="PENDING",
        )
    else:
        try:
            if not observation.parsed or observation.process.returncode != 0:
                parser_status = "FAIL" if observation.parse_error else "PASS" if observation.parsed else "NOT_RUN"
                parser_error_class = _public_error_class(observation.parse_error)
                machine.record_executor_return(parsed=False, returncode=observation.process.returncode)
                final_state = machine.state
                structured = None
                structured_output_status = "ABSENT"
                os_validation = "FAIL"
                reconciliation = "NOT_REQUIRED"
            else:
                parser_status = "PASS"
                machine.record_executor_return(parsed=True, returncode=observation.process.returncode)
                try:
                    raw_result = _extract_structured_result(observation.parsed_events)
                    structured = sanitize_live_result(raw_result, allowed_keys=_RESULT_KEYS).value
                    structured_output_status = "PRESENT"
                    structured_output_present = True
                    schema_status = "PASS"
                except (LiveExecutionError, LivePrivacyError):
                    machine.transition("MALFORMED_RESULT", "structured result failed exact extraction or privacy gate")
                    final_state = machine.state
                    structured = None
                    structured_output_status = "SCHEMA_MISMATCH" if isinstance(raw_result if 'raw_result' in locals() else None, Mapping) else "MALFORMED"
                    schema_status = "FAIL"
                    schema_error_class = "STRUCTURED_RESULT_CONTRACT_REJECTED"
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
            structured_output_status = "MALFORMED"
            schema_status = "FAIL"
            schema_error_class = "BOUNDED_RESULT_HANDLING_FAILURE"
            os_validation = "FAIL"
            reconciliation = "NOT_REQUIRED"

        if final_state != "COMPLETED_VALIDATED":
            failure_forensics_capsule = _failure_forensics(
                observation=observation, adapter=adapter, envelope=envelope,
                before_digest=before_digest, after_digest=after_digest,
                parser_status=parser_status, parser_error_class=parser_error_class,
                schema_status=schema_status, schema_error_class=schema_error_class,
                structured_output_status=structured_output_status,
                structured_output_present=structured_output_present,
                diagnostic_class=classify_failure(
                    process_return_code=observation.process.returncode,
                    timed_out=observation.process.timed_out,
                    parser_status=parser_status,
                    schema_status=schema_status,
                    structured_output_status=structured_output_status,
                ),
                raw_spool_retention_status="RETAINED_UNTIL_DURABLE_RECEIPT",
                raw_spool_disposal_status="PENDING",
            )
        capture_capsule = _close_capture(observation, structured, retain_for_reconciliation=False)
        if failure_forensics_capsule is not None:
            cleanup = capture_capsule.get("spool_cleanup_status") if isinstance(capture_capsule, Mapping) else None
            failure_forensics_capsule = update_spool_disposition(
                failure_forensics_capsule,
                retention_status="CLEANED_AFTER_DURABLE_RECEIPT" if cleanup == "CLEANED" else "UNKNOWN" if cleanup == "FAILED" else "RETAINED_UNTIL_DURABLE_RECEIPT",
                disposal_status="CLEANED" if cleanup == "CLEANED" else "RETAINED" if cleanup == "PENDING" else "UNKNOWN",
            )

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
        capture_capsule = _close_capture(observation, None, retain_for_reconciliation=True)
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

    return LiveAttemptResult(
        receipt and observation, receipt, validation, tuple(item.to_dict() for item in machine.history), durable,
        capture_capsule=capture_capsule,
        failure_forensics_capsule=failure_forensics_capsule,
    )


__all__ = ["LIVE_EXECUTION_SCHEMA", "LiveAttemptResult", "LiveExecutionError", "execute_bounded_attempt"]
