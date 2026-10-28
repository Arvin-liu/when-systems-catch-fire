"""Deterministic fault matrix for durable live capture and context loss."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import signal
import sys
import tempfile
from typing import Any

from .live_capture import LiveCaptureError, LiveCaptureWriter
from .live_transport import LiveProcessTransport, LiveTransportError


LIVE_CAPTURE_FAULT_MATRIX_SCHEMA = "ignition-139-live-capture-fault-matrix-r1"
PYTHON = sys.executable


@dataclass(frozen=True)
class CaptureFaultCaseResult:
    case_id: str
    guard: str
    observed: str
    status: str = "PASS"

    def to_dict(self) -> dict[str, str]:
        return {"case_id": self.case_id, "guard": self.guard, "observed": self.observed, "status": self.status}


CASE_SPECS = (
    ("small_output", "small output completes with complete capsule"),
    ("oversized_output", "context overflow leaves durable complete capture"),
    ("outer_consumer_exception", "outer context failure does not erase capsule"),
    ("malformed_jsonl", "raw digest survives public parser failure"),
    ("capture_cap_reached", "durable cap is explicit incomplete truncation"),
    ("exit_before_first_event", "process exit without event remains observable"),
    ("timeout_process_group_cleanup", "timeout records process group cleanup"),
    ("signal_termination", "signal termination is explicit"),
    ("spool_write_failure", "spool failure fails closed"),
    ("spool_deleted_early", "missing spool blocks dispatch"),
    ("secret_marker_output", "secret-like output cannot enter public projection"),
    ("hidden_reasoning_event", "hidden reasoning event is rejected"),
    ("result_before_trailing_logs", "structured result remains recoverable before large logs"),
    ("duplicate_finalize", "finalization is idempotent"),
    ("context_unavailable_capsule_complete", "complete capsule is independently recoverable"),
    ("context_unavailable_capsule_incomplete", "incomplete capsule requires reconciliation"),
)


def _writer(directory: str, number: int) -> LiveCaptureWriter:
    return LiveCaptureWriter.create(
        capture_id=f"capture-matrix-{number}",
        task_id="IGNITION-20260825-139",
        dispatch_id=f"dispatch-matrix-{number}",
        attempt_id=f"attempt-matrix-{number}",
        executor_id="external.synthetic",
        adapter_id="synthetic-live-r1",
        parent=directory,
    )


def _transport(**kwargs: Any) -> LiveProcessTransport:
    values = {"executable_allowlist": (PYTHON,), "output_cap_bytes": 128, "capture_output_cap_bytes": 16 * 1024 * 1024}
    values.update(kwargs)
    return LiveProcessTransport(**values)


def _run_case(case_id: str, number: int) -> str:
    with tempfile.TemporaryDirectory(prefix=f"capture-matrix-{number}-") as directory:
        writer = _writer(directory, number)
        if case_id == "small_output":
            result = _transport().run((PYTHON, "-c", "print('small')"), cwd=directory, timeout_seconds=2, capture=writer)
            writer.cleanup_spool()
            return "COMPLETE" if result.capture_capsule["capture_completeness"] == "COMPLETE" and result.returncode == 0 else "UNEXPECTED"
        if case_id in {"oversized_output", "context_unavailable_capsule_complete"}:
            code = "import sys; print('{\"type\":\"progress\",\"step\":1}', flush=True); sys.stdout.write('x' * (1024 * 1024)); sys.stdout.flush()"
            result = _transport().run((PYTHON, "-c", code), cwd=directory, timeout_seconds=3, capture=writer)
            complete = result.capture_capsule["capture_completeness"] == "COMPLETE"
            bounded = result.context_truncated and not result.output_truncated
            writer.cleanup_spool()
            return "CONTEXT_LOST_CAPTURE_COMPLETE" if complete and bounded else "UNEXPECTED"
        if case_id == "outer_consumer_exception":
            result = _transport().run((PYTHON, "-c", "print('consumer-independent')"), cwd=directory, timeout_seconds=2, capture=writer)
            try:
                raise RuntimeError("simulated outer model context exception")
            except RuntimeError:
                recovered = result.capture_capsule["capture_completeness"] == "COMPLETE"
            writer.cleanup_spool()
            return "CAPSULE_RECOVERABLE" if recovered else "UNEXPECTED"
        if case_id == "malformed_jsonl":
            result = _transport().run((PYTHON, "-c", "import sys; sys.stdout.write('{not-json\\n'); sys.stdout.flush()"), cwd=directory, timeout_seconds=2, capture=writer)
            observed = result.capture_parse_error == "PUBLIC_EVENT_JSONL_MALFORMED" and result.capture_capsule["capture_completeness"] == "COMPLETE"
            writer.cleanup_spool()
            return "RAW_COMPLETE_PUBLIC_PARSE_FAIL" if observed else "UNEXPECTED"
        if case_id in {"capture_cap_reached", "context_unavailable_capsule_incomplete"}:
            result = _transport(capture_output_cap_bytes=32).run((PYTHON, "-c", "import sys; sys.stdout.write('x' * 4096); sys.stdout.flush()"), cwd=directory, timeout_seconds=2, capture=writer)
            incomplete = result.output_truncated and result.capture_capsule["capture_completeness"] == "INCOMPLETE"
            writer.cleanup_spool()
            return "TRUNCATED_REQUIRES_RECONCILIATION" if incomplete else "UNEXPECTED"
        if case_id == "exit_before_first_event":
            result = _transport().run((PYTHON, "-c", "import sys; sys.exit(7)"), cwd=directory, timeout_seconds=2, capture=writer)
            observed = result.returncode == 7 and result.capture_capsule["public_events"]["count"] == 0
            writer.cleanup_spool()
            return "EXIT_WITH_ZERO_EVENTS_OBSERVED" if observed else "UNEXPECTED"
        if case_id == "timeout_process_group_cleanup":
            result = _transport().run((PYTHON, "-c", "import time; print('started', flush=True); time.sleep(2)"), cwd=directory, timeout_seconds=0.05, capture=writer)
            observed = result.timed_out and result.capture_capsule["process_observation"]["process_group_status"] == "CONFIRMED_GONE"
            writer.cleanup_spool()
            return "TIMEOUT_GROUP_CLEANUP_OBSERVED" if observed else "UNEXPECTED"
        if case_id == "signal_termination":
            result = _transport().run((PYTHON, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"), cwd=directory, timeout_seconds=2, capture=writer)
            observed = result.returncode == -signal.SIGTERM and result.capture_capsule["process_observation"]["signal"] == "SIGTERM"
            writer.cleanup_spool()
            return "SIGNAL_EXPLICIT" if observed else "UNEXPECTED"
        if case_id == "spool_write_failure":
            def fail_write(_chunk: bytes) -> None:
                raise LiveCaptureError("simulated disk failure")
            writer.write_stdout = fail_write  # type: ignore[method-assign]
            result = _transport().run((PYTHON, "-c", "print('will fail')"), cwd=directory, timeout_seconds=2, capture=writer)
            observed = result.capture_capsule["capture_completeness"] == "INCOMPLETE" and result.capture_capsule["spool_cleanup_status"] == "PENDING"
            writer.cleanup_spool()
            return "SPOOL_FAILURE_FAIL_CLOSED" if observed else "UNEXPECTED"
        if case_id == "spool_deleted_early":
            shutil.rmtree(writer.spool_path)
            try:
                _transport().run((PYTHON, "-c", "print('must not start')"), cwd=directory, timeout_seconds=2, capture=writer)
            except LiveTransportError:
                return "DISPATCH_BLOCKED_MISSING_SPOOL"
            return "UNEXPECTED"
        if case_id == "secret_marker_output":
            result = _transport().run((PYTHON, "-c", "print('secret=do-not-project')"), cwd=directory, timeout_seconds=2, capture=writer)
            observed = result.capture_capsule["secret_scan_status"] == "FAIL" and "do-not-project" not in result.stdout
            writer.cleanup_spool()
            return "SECRET_REJECTED_AND_CONTEXT_REDACTED" if observed else "UNEXPECTED"
        if case_id == "hidden_reasoning_event":
            result = _transport().run((PYTHON, "-c", "print('{\"hidden_reasoning\":\"private\"}')"), cwd=directory, timeout_seconds=2, capture=writer)
            observed = result.capture_capsule["secret_scan_status"] == "FAIL" and result.capture_capsule["capture_completeness"] == "INCOMPLETE"
            writer.cleanup_spool()
            return "PRIVATE_EVENT_REJECTED" if observed else "UNEXPECTED"
        if case_id == "result_before_trailing_logs":
            result_value = {"nonce": "0123456789abcdef01234567", "line_count": 3, "field_value": "value", "checksum_prefix": "deadbeef"}
            code = f"import json, sys; print(json.dumps({json.dumps({'type':'result','result':result_value})}), flush=True); sys.stdout.write('z' * (1024 * 1024)); sys.stdout.flush()"
            result = _transport().run((PYTHON, "-c", code), cwd=directory, timeout_seconds=3, capture=writer)
            writer.attach_structured_result(result_value)
            observed = result.captured_events and result.captured_events[0].get("result") == result_value and result.capture_capsule["capture_completeness"] == "COMPLETE"
            writer.cleanup_spool()
            return "STRUCTURED_RESULT_RECOVERABLE" if observed else "UNEXPECTED"
        if case_id == "duplicate_finalize":
            first = writer.finalize(return_code=0)
            second = writer.finalize(return_code=9)
            writer.cleanup_spool()
            return "IDEMPOTENT_FINALIZE" if first == second else "UNEXPECTED"
    raise AssertionError(case_id)


def run_capture_fault_matrix() -> dict[str, Any]:
    results: list[dict[str, str]] = []
    for index, (case_id, guard) in enumerate(CASE_SPECS, start=1):
        try:
            observed = _run_case(case_id, index)
            status = "PASS" if observed != "UNEXPECTED" else "FAIL"
        except Exception as exc:
            observed = "FAIL_CLOSED_EXCEPTION:" + type(exc).__name__
            status = "FAIL"
        results.append(CaptureFaultCaseResult(case_id, guard, observed, status).to_dict())
    return {
        "schema": LIVE_CAPTURE_FAULT_MATRIX_SCHEMA,
        "case_count": len(results),
        "cases": results,
        "all_fail_closed": all(item["status"] == "PASS" for item in results),
        "claim_ceiling": "Deterministic host-side capture, privacy and context-loss evidence only; no live completion is inferred.",
    }


__all__ = ["CASE_SPECS", "CaptureFaultCaseResult", "LIVE_CAPTURE_FAULT_MATRIX_SCHEMA", "run_capture_fault_matrix"]
