"""Durable dispatch, progress and reconciliation controls for external effects."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import time
from typing import Any, Iterable, Mapping

from agent_kernel.contracts import _id, sha256_json

from .control import FileLock, _atomic_json


DISPATCH_SCHEMA = "os-control-plane-durable-dispatch-r1"
EFFECT_CLASSES = frozenset({"READ_ONLY", "EXTERNAL_SIDE_EFFECT", "UNKNOWN_SIDE_EFFECT"})
DISPATCH_STATES = frozenset({"CREATED", "SENT", "ACKNOWLEDGED", "RUNNING", "RECEIPT_RECORDED", "COMPLETED_VALIDATED", "FAILED_VALIDATION", "REJECTED", "RETRY_ELIGIBLE_READ_ONLY", "REQUIRES_RECONCILIATION"})
PROGRESS_STATES = frozenset({"RUNNING", "WAITING", "PAUSED"})
RECEIPT_TERMINALS = frozenset({"COMPLETED", "FAILED", "CANCELLED", "UNKNOWN", "REQUIRES_RECONCILIATION"})
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "reasoning", "api_key", "token", "cookie", "authorization", "secret"})


class DispatchError(RuntimeError):
    """A dispatch contract or reconciliation failure."""


class DispatchConflict(DispatchError):
    """An idempotency, sequence or lifecycle conflict."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
        raise DispatchError(f"{field} must be a non-empty public string")
    return value


def _digest(value: Any, field: str) -> str:
    _text(value, field)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise DispatchError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _refs(values: Iterable[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise DispatchError(f"{field} must be a string collection")
    return tuple(sorted({_text(value, f"{field}[]") for value in values}))


@dataclass(frozen=True)
class DispatchEnvelope:
    dispatch_id: str
    task_id: str
    executor_id: str
    idempotency_key: str
    payload_digest: str
    effect_class: str
    created_at: float
    timeout_seconds: float
    envelope_digest: str | None = None

    def __post_init__(self) -> None:
        for value, field in ((self.dispatch_id, "dispatch_id"), (self.task_id, "task_id"), (self.executor_id, "executor_id"), (self.idempotency_key, "idempotency_key")):
            _id(value, field)
        _digest(self.payload_digest, "payload_digest")
        if self.effect_class not in EFFECT_CLASSES:
            raise DispatchError(f"unknown effect class: {self.effect_class}")
        if not isinstance(self.created_at, (int, float)) or self.created_at < 0:
            raise DispatchError("created_at must be non-negative")
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise DispatchError("timeout_seconds must be positive")
        expected = sha256_json(self._body())
        if self.envelope_digest is not None and self.envelope_digest != expected:
            raise DispatchError("dispatch envelope digest mismatch")
        object.__setattr__(self, "envelope_digest", expected)

    def _body(self) -> dict[str, Any]:
        return {"dispatch_id": self.dispatch_id, "task_id": self.task_id, "executor_id": self.executor_id, "idempotency_key": self.idempotency_key, "payload_digest": self.payload_digest, "effect_class": self.effect_class, "created_at": self.created_at, "timeout_seconds": self.timeout_seconds}

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "envelope_digest": self.envelope_digest}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DispatchEnvelope":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise DispatchError("dispatch envelope keys mismatch")
        return cls(**dict(data))


@dataclass(frozen=True)
class DispatchProgress:
    dispatch_id: str
    task_id: str
    executor_id: str
    idempotency_key: str
    sequence: int
    state: str
    public_summary: str
    refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value, field in ((self.dispatch_id, "dispatch_id"), (self.task_id, "task_id"), (self.executor_id, "executor_id"), (self.idempotency_key, "idempotency_key")):
            _id(value, field)
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 0:
            raise DispatchError("progress sequence must be non-negative")
        if self.state not in PROGRESS_STATES:
            raise DispatchError("progress state is not non-terminal")
        _text(self.public_summary, "public_summary")
        object.__setattr__(self, "refs", _refs(self.refs, "refs"))

    def to_dict(self) -> dict[str, Any]:
        return {"dispatch_id": self.dispatch_id, "task_id": self.task_id, "executor_id": self.executor_id, "idempotency_key": self.idempotency_key, "sequence": self.sequence, "state": self.state, "public_summary": self.public_summary, "refs": list(self.refs)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DispatchProgress":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise DispatchError("dispatch progress keys mismatch")
        return cls(**dict(data))


@dataclass(frozen=True)
class DispatchReceipt:
    dispatch_id: str
    task_id: str
    executor_id: str
    idempotency_key: str
    sequence: int
    terminal_state: str
    public_summary: str
    artifact_digest: str
    reported_at: float
    receipt_digest: str | None = None

    def __post_init__(self) -> None:
        for value, field in ((self.dispatch_id, "dispatch_id"), (self.task_id, "task_id"), (self.executor_id, "executor_id"), (self.idempotency_key, "idempotency_key")):
            _id(value, field)
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 0:
            raise DispatchError("receipt sequence must be non-negative")
        if self.terminal_state not in RECEIPT_TERMINALS:
            raise DispatchError("unknown receipt terminal state")
        _text(self.public_summary, "receipt.public_summary")
        _digest(self.artifact_digest, "artifact_digest")
        if not isinstance(self.reported_at, (int, float)) or self.reported_at < 0:
            raise DispatchError("reported_at must be non-negative")
        expected = sha256_json(self._body())
        if self.receipt_digest is not None and self.receipt_digest != expected:
            raise DispatchError("receipt digest mismatch")
        object.__setattr__(self, "receipt_digest", expected)

    def _body(self) -> dict[str, Any]:
        return {"dispatch_id": self.dispatch_id, "task_id": self.task_id, "executor_id": self.executor_id, "idempotency_key": self.idempotency_key, "sequence": self.sequence, "terminal_state": self.terminal_state, "public_summary": self.public_summary, "artifact_digest": self.artifact_digest, "reported_at": self.reported_at}

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "receipt_digest": self.receipt_digest}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DispatchReceipt":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise DispatchError("dispatch receipt keys mismatch")
        return cls(**dict(data))


@dataclass(frozen=True)
class DispatchRecord:
    dispatch_id: str
    task_id: str
    executor_id: str
    idempotency_key: str
    payload_digest: str
    effect_class: str
    created_at: float
    timeout_seconds: float
    state: str = "CREATED"
    attempt: int = 0
    last_sequence: int = -1
    ack_ref: str | None = None
    progress_events: tuple[DispatchProgress, ...] = ()
    receipt: DispatchReceipt | None = None
    validation_refs: tuple[str, ...] = ()
    safe_failover: bool = False
    terminal_reason: str | None = None
    dispatch_digest: str | None = None

    def __post_init__(self) -> None:
        for value, field in ((self.dispatch_id, "dispatch_id"), (self.task_id, "task_id"), (self.executor_id, "executor_id"), (self.idempotency_key, "idempotency_key")):
            _id(value, field)
        _digest(self.payload_digest, "payload_digest")
        if self.effect_class not in EFFECT_CLASSES or self.state not in DISPATCH_STATES:
            raise DispatchError("dispatch record class or state is invalid")
        if not isinstance(self.created_at, (int, float)) or not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise DispatchError("dispatch record timing is invalid")
        if not isinstance(self.attempt, int) or self.attempt < 0 or not isinstance(self.last_sequence, int) or self.last_sequence < -1:
            raise DispatchError("dispatch attempt or sequence is invalid")
        if self.ack_ref is not None:
            _text(self.ack_ref, "ack_ref")
        if any(not isinstance(item, DispatchProgress) for item in self.progress_events):
            raise DispatchError("progress_events must contain DispatchProgress values")
        if self.receipt is not None and not isinstance(self.receipt, DispatchReceipt):
            raise DispatchError("receipt must be DispatchReceipt or null")
        object.__setattr__(self, "validation_refs", _refs(self.validation_refs, "validation_refs"))
        if self.terminal_reason is not None:
            _text(self.terminal_reason, "terminal_reason")
        expected = sha256_json(self._body())
        if self.dispatch_digest is not None and self.dispatch_digest != expected:
            raise DispatchError("dispatch record digest mismatch")
        object.__setattr__(self, "dispatch_digest", expected)

    def _body(self) -> dict[str, Any]:
        return {"dispatch_id": self.dispatch_id, "task_id": self.task_id, "executor_id": self.executor_id, "idempotency_key": self.idempotency_key, "payload_digest": self.payload_digest, "effect_class": self.effect_class, "created_at": self.created_at, "timeout_seconds": self.timeout_seconds}

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "state": self.state, "attempt": self.attempt, "last_sequence": self.last_sequence, "ack_ref": self.ack_ref, "progress_events": [item.to_dict() for item in self.progress_events], "receipt": self.receipt.to_dict() if self.receipt else None, "validation_refs": list(self.validation_refs), "safe_failover": self.safe_failover, "terminal_reason": self.terminal_reason, "dispatch_digest": self.dispatch_digest}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DispatchRecord":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise DispatchError("dispatch record keys mismatch")
        values = dict(data)
        values["progress_events"] = tuple(DispatchProgress.from_dict(item) for item in values["progress_events"])
        values["receipt"] = DispatchReceipt.from_dict(values["receipt"]) if values["receipt"] is not None else None
        return cls(**values)


class DurableDispatchStore:
    """Locked idempotent dispatch journal with fail-closed reconciliation."""

    def __init__(self, path: str | Path, *, clock: Any = None) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.clock = clock or time.time

    def _read(self) -> list[DispatchRecord]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != DISPATCH_SCHEMA or not isinstance(data.get("records"), list):
                raise DispatchError("dispatch store schema mismatch")
            records = [DispatchRecord.from_dict(item) for item in data["records"]]
            if len({item.dispatch_id for item in records}) != len(records) or len({item.idempotency_key for item in records}) != len(records):
                raise DispatchError("dispatch store has duplicate identity")
            return records
        except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
            if isinstance(exc, DispatchError):
                raise
            raise DispatchError("dispatch store is malformed") from exc

    def _write(self, records: Iterable[DispatchRecord]) -> None:
        _atomic_json(self.path, {"schema": DISPATCH_SCHEMA, "records": [item.to_dict() for item in sorted(records, key=lambda item: item.created_at)]})

    def create(self, envelope: DispatchEnvelope) -> DispatchRecord:
        if not isinstance(envelope, DispatchEnvelope):
            raise DispatchError("create accepts DispatchEnvelope only")
        with FileLock(self.lock_path):
            records = self._read()
            existing = next((item for item in records if item.dispatch_id == envelope.dispatch_id or item.idempotency_key == envelope.idempotency_key), None)
            if existing is not None:
                same = (existing.dispatch_id, existing.task_id, existing.executor_id, existing.idempotency_key, existing.payload_digest, existing.effect_class) == (envelope.dispatch_id, envelope.task_id, envelope.executor_id, envelope.idempotency_key, envelope.payload_digest, envelope.effect_class)
                if not same:
                    raise DispatchConflict("dispatch identity or idempotency key is bound to different envelope")
                return existing
            record = DispatchRecord(**envelope._body(), dispatch_digest=None)
            records.append(record)
            self._write(records)
            return record

    def get(self, dispatch_id: str) -> DispatchRecord:
        _id(dispatch_id, "dispatch_id")
        with FileLock(self.lock_path):
            record = next((item for item in self._read() if item.dispatch_id == dispatch_id), None)
        if record is None:
            raise DispatchError("dispatch does not exist")
        return record

    def _replace(self, updated: DispatchRecord) -> DispatchRecord:
        with FileLock(self.lock_path):
            records = self._read()
            if not any(item.dispatch_id == updated.dispatch_id for item in records):
                raise DispatchError("dispatch does not exist")
            self._write(updated if item.dispatch_id == updated.dispatch_id else item for item in records)
        return updated

    def mark_sent(self, dispatch_id: str) -> DispatchRecord:
        record = self.get(dispatch_id)
        if record.state not in {"CREATED", "RETRY_ELIGIBLE_READ_ONLY"}:
            raise DispatchConflict("dispatch may be sent only once per created/retry attempt")
        return self._replace(replace(record, state="SENT", attempt=record.attempt + 1, safe_failover=False, dispatch_digest=None))

    def acknowledge(self, dispatch_id: str, *, accepted: bool, ack_ref: str) -> DispatchRecord:
        _text(ack_ref, "ack_ref")
        record = self.get(dispatch_id)
        if record.state != "SENT":
            raise DispatchConflict("acknowledgement is out of order or duplicated")
        return self._replace(replace(record, state="ACKNOWLEDGED" if accepted else "REJECTED", ack_ref=ack_ref, terminal_reason=None if accepted else "external executor rejected dispatch", dispatch_digest=None))

    def append_progress(self, progress: DispatchProgress) -> DispatchRecord:
        if not isinstance(progress, DispatchProgress):
            raise DispatchError("append_progress accepts DispatchProgress only")
        record = self.get(progress.dispatch_id)
        if (progress.task_id, progress.executor_id, progress.idempotency_key) != (record.task_id, record.executor_id, record.idempotency_key):
            raise DispatchConflict("progress identity does not match dispatch")
        if record.state not in {"ACKNOWLEDGED", "RUNNING"} or progress.sequence <= record.last_sequence:
            raise DispatchConflict("progress is duplicate, out of order or terminal")
        return self._replace(replace(record, state="RUNNING", last_sequence=progress.sequence, progress_events=(*record.progress_events, progress), dispatch_digest=None))

    def record_receipt(self, receipt: DispatchReceipt, *, reconciliation: bool = False) -> DispatchRecord:
        if not isinstance(receipt, DispatchReceipt):
            raise DispatchError("record_receipt accepts DispatchReceipt only")
        record = self.get(receipt.dispatch_id)
        if (receipt.task_id, receipt.executor_id, receipt.idempotency_key) != (record.task_id, record.executor_id, record.idempotency_key):
            raise DispatchConflict("receipt identity does not match dispatch")
        if record.state not in {"ACKNOWLEDGED", "RUNNING", "REQUIRES_RECONCILIATION"}:
            raise DispatchConflict("receipt is out of order or duplicated")
        if receipt.sequence <= record.last_sequence:
            raise DispatchConflict("receipt sequence regressed or duplicated")
        if record.state == "REQUIRES_RECONCILIATION" and not reconciliation:
            raise DispatchConflict("ambiguous dispatch requires explicit reconciliation")
        return self._replace(replace(record, state="RECEIPT_RECORDED", last_sequence=receipt.sequence, receipt=receipt, dispatch_digest=None))

    def validate_receipt(self, dispatch_id: str, *, validation_ref: str, passed: bool) -> DispatchRecord:
        _text(validation_ref, "validation_ref")
        if not isinstance(passed, bool):
            raise DispatchError("passed must be boolean")
        record = self.get(dispatch_id)
        if record.state != "RECEIPT_RECORDED" or record.receipt is None:
            raise DispatchConflict("only a recorded receipt can be OS validated")
        return self._replace(replace(record, state="COMPLETED_VALIDATED" if passed else "FAILED_VALIDATION", validation_refs=(*record.validation_refs, validation_ref), terminal_reason=None if passed else "OS validation rejected external receipt", dispatch_digest=None))

    def timeout(self, dispatch_id: str, *, reason: str = "acknowledgement timeout") -> DispatchRecord:
        _text(reason, "reason")
        record = self.get(dispatch_id)
        if record.state not in {"SENT", "ACKNOWLEDGED", "RUNNING"}:
            raise DispatchConflict("timeout is not applicable to the current dispatch state")
        if record.effect_class == "READ_ONLY":
            return self._replace(replace(record, state="RETRY_ELIGIBLE_READ_ONLY", safe_failover=True, terminal_reason=reason, dispatch_digest=None))
        return self._replace(replace(record, state="REQUIRES_RECONCILIATION", safe_failover=False, terminal_reason=reason, dispatch_digest=None))

    def retry_read_only(self, dispatch_id: str) -> DispatchRecord:
        record = self.get(dispatch_id)
        if record.state != "RETRY_ELIGIBLE_READ_ONLY" or record.effect_class != "READ_ONLY" or not record.safe_failover:
            raise DispatchConflict("only a timed-out read-only dispatch may retry")
        return self.mark_sent(self._replace(replace(record, state="CREATED", safe_failover=False, dispatch_digest=None)).dispatch_id)

    def audit(self) -> dict[str, Any]:
        with FileLock(self.lock_path):
            records = self._read()
        counts = {state: sum(item.state == state for item in records) for state in sorted(DISPATCH_STATES)}
        return {"status": "PASS", "schema": DISPATCH_SCHEMA, "record_count": len(records), "state_counts": counts, "claim_ceiling": "Durable dispatch, progress and reconciliation state only; external receipts require independent OS validation."}


__all__ = ["DISPATCH_SCHEMA", "DISPATCH_STATES", "DispatchConflict", "DispatchEnvelope", "DispatchError", "DispatchProgress", "DispatchReceipt", "DispatchRecord", "DurableDispatchStore"]
