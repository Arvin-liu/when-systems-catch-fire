"""Durable bounded queue, admission and cancellation controls for R2."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import time
from typing import Any, Iterable, Mapping

from agent_kernel.contracts import _id, sha256_json

from .control import FileLock, _atomic_json


QUEUE_SCHEMA = "os-control-plane-queue-control-r1"
QUEUE_STATES = frozenset({
    "QUEUED", "ADMITTED", "DISPATCHED", "CANCELLED_BEFORE_DISPATCH", "CANCEL_REQUESTED_REQUIRES_RECONCILIATION",
    "EXPIRED_BEFORE_DISPATCH", "REJECTED_BACKPRESSURE", "REJECTED_QUOTA", "COMPLETED_VALIDATED", "FAILED", "REQUIRES_RECONCILIATION",
})
ACTIVE_QUEUE_STATES = frozenset({"QUEUED", "ADMITTED"})
TERMINAL_QUEUE_STATES = frozenset(QUEUE_STATES - ACTIVE_QUEUE_STATES - {"DISPATCHED"})
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "reasoning", "api_key", "token", "cookie", "authorization", "secret"})


class QueueControlError(RuntimeError):
    """A queue contract or durable-state failure."""


class QueueAdmissionError(QueueControlError):
    """The queue refused an item because of backpressure or quota."""

    def __init__(self, message: str, *, queue_id: str, state: str) -> None:
        super().__init__(message)
        self.queue_id = queue_id
        self.state = state


class QueueNotDispatchable(QueueControlError):
    """A queue item cannot cross the dispatch boundary."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
        raise QueueControlError(f"{field} must be a non-empty public string")
    return value


def _tuple(values: Iterable[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise QueueControlError(f"{field} must be a string collection")
    result = tuple(sorted({_text(value, f"{field}[]") for value in values}))
    return result


@dataclass(frozen=True)
class QueueItem:
    queue_id: str
    run_id: str
    profile_ref: str
    project_ref: str
    priority: int
    enqueued_at: float
    deadline_epoch: float | None = None
    not_before_epoch: float = 0.0
    cost_units: int = 1
    executor_id: str | None = None
    required_capabilities: tuple[str, ...] = ()
    state: str = "QUEUED"
    sequence: int = 0
    admitted_at: float | None = None
    dispatched_at: float | None = None
    terminal_reason: str | None = None
    item_digest: str | None = None

    def __post_init__(self) -> None:
        _id(self.queue_id, "queue_id")
        _id(self.run_id, "run_id")
        _id(self.profile_ref, "profile_ref")
        _id(self.project_ref, "project_ref")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool) or not 0 <= self.priority <= 1000:
            raise QueueControlError("priority must be between 0 and 1000")
        if not isinstance(self.enqueued_at, (int, float)) or self.enqueued_at < 0:
            raise QueueControlError("enqueued_at must be non-negative")
        if self.deadline_epoch is not None and (not isinstance(self.deadline_epoch, (int, float)) or self.deadline_epoch <= 0):
            raise QueueControlError("deadline_epoch must be positive")
        if not isinstance(self.not_before_epoch, (int, float)) or self.not_before_epoch < 0:
            raise QueueControlError("not_before_epoch must be non-negative")
        if not isinstance(self.cost_units, int) or isinstance(self.cost_units, bool) or self.cost_units <= 0:
            raise QueueControlError("cost_units must be positive")
        if self.executor_id is not None:
            _id(self.executor_id, "executor_id")
        object.__setattr__(self, "required_capabilities", _tuple(self.required_capabilities, "required_capabilities"))
        if self.state not in QUEUE_STATES:
            raise QueueControlError(f"unknown queue state: {self.state}")
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise QueueControlError("sequence must be non-negative")
        for value, field in ((self.admitted_at, "admitted_at"), (self.dispatched_at, "dispatched_at")):
            if value is not None and (not isinstance(value, (int, float)) or value < 0):
                raise QueueControlError(f"{field} must be non-negative or null")
        if self.terminal_reason is not None:
            _text(self.terminal_reason, "terminal_reason")
        expected = sha256_json(self._body())
        if self.item_digest is not None and self.item_digest != expected:
            raise QueueControlError("queue item digest mismatch")
        object.__setattr__(self, "item_digest", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "queue_id": self.queue_id, "run_id": self.run_id, "profile_ref": self.profile_ref,
            "project_ref": self.project_ref, "priority": self.priority, "enqueued_at": self.enqueued_at,
            "deadline_epoch": self.deadline_epoch, "not_before_epoch": self.not_before_epoch,
            "cost_units": self.cost_units, "executor_id": self.executor_id,
            "required_capabilities": list(self.required_capabilities), "state": self.state,
            "sequence": self.sequence, "admitted_at": self.admitted_at, "dispatched_at": self.dispatched_at,
            "terminal_reason": self.terminal_reason,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "item_digest": self.item_digest}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "QueueItem":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise QueueControlError("queue item keys mismatch")
        return cls(**dict(data))


class WorkQueue:
    """Locked queue with bounded depth, quotas and deterministic admission."""

    def __init__(self, path: str | Path, *, max_depth: int, profile_limits: Mapping[str, int] | None = None, project_limits: Mapping[str, int] | None = None, aging_seconds: float = 30.0, clock: Any = None) -> None:
        if not isinstance(max_depth, int) or max_depth <= 0:
            raise QueueControlError("max_depth must be positive")
        if not isinstance(aging_seconds, (int, float)) or aging_seconds <= 0:
            raise QueueControlError("aging_seconds must be positive")
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.max_depth = max_depth
        self.profile_limits = {str(key): int(value) for key, value in (profile_limits or {}).items()}
        self.project_limits = {str(key): int(value) for key, value in (project_limits or {}).items()}
        if any(value <= 0 for value in (*self.profile_limits.values(), *self.project_limits.values())):
            raise QueueControlError("queue quotas must be positive")
        self.aging_seconds = float(aging_seconds)
        self.clock = clock or time.time

    def _read(self) -> tuple[list[QueueItem], int, bool, int]:
        if not self.path.exists():
            return [], 0, False, 0
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != QUEUE_SCHEMA or not isinstance(data.get("items"), list):
                raise QueueControlError("queue schema mismatch")
            items = [QueueItem.from_dict(item) for item in data["items"]]
            if len({item.queue_id for item in items}) != len(items):
                raise QueueControlError("queue contains duplicate queue ids")
            return items, int(data.get("next_sequence", 0)), bool(data.get("paused", False)), int(data.get("backpressure_events", 0))
        except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
            if isinstance(exc, QueueControlError):
                raise
            raise QueueControlError("queue state is malformed") from exc

    def _write(self, items: Iterable[QueueItem], sequence: int, paused: bool, backpressure_events: int) -> None:
        _atomic_json(self.path, {"schema": QUEUE_SCHEMA, "next_sequence": sequence, "paused": paused, "backpressure_events": backpressure_events, "items": [item.to_dict() for item in sorted(items, key=lambda item: item.sequence)]})

    @staticmethod
    def _active(items: Iterable[QueueItem]) -> list[QueueItem]:
        return [item for item in items if item.state in ACTIVE_QUEUE_STATES]

    def enqueue(self, item: QueueItem) -> QueueItem:
        if not isinstance(item, QueueItem):
            raise QueueControlError("enqueue accepts QueueItem only")
        with FileLock(self.lock_path):
            items, sequence, paused, backpressure_events = self._read()
            existing = next((entry for entry in items if entry.queue_id == item.queue_id), None)
            if existing is not None:
                if existing.item_digest != item.item_digest:
                    raise QueueControlError("queue id is bound to a different item")
                return existing
            active = self._active(items)
            profile_count = sum(entry.profile_ref == item.profile_ref for entry in active)
            project_count = sum(entry.project_ref == item.project_ref for entry in active)
            sequence += 1
            if len(active) >= self.max_depth:
                rejected = replace(item, state="REJECTED_BACKPRESSURE", sequence=sequence, terminal_reason="queue depth backpressure", item_digest=None)
                items.append(rejected)
                self._write(items, sequence, paused, backpressure_events + 1)
                raise QueueAdmissionError("queue depth backpressure rejected item", queue_id=item.queue_id, state=rejected.state)
            if profile_count >= self.profile_limits.get(item.profile_ref, self.max_depth) or project_count >= self.project_limits.get(item.project_ref, self.max_depth):
                rejected = replace(item, state="REJECTED_QUOTA", sequence=sequence, terminal_reason="profile or project quota", item_digest=None)
                items.append(rejected)
                self._write(items, sequence, paused, backpressure_events)
                raise QueueAdmissionError("queue quota rejected item", queue_id=item.queue_id, state=rejected.state)
            queued = replace(item, state="QUEUED", sequence=sequence, item_digest=None)
            items.append(queued)
            self._write(items, sequence, paused, backpressure_events)
            return queued

    def _normalize_expired(self, items: list[QueueItem], now: float) -> list[QueueItem]:
        normalized: list[QueueItem] = []
        for item in items:
            if item.state in ACTIVE_QUEUE_STATES and item.deadline_epoch is not None and now >= item.deadline_epoch:
                normalized.append(replace(item, state="EXPIRED_BEFORE_DISPATCH", terminal_reason="deadline expired before dispatch", item_digest=None))
            else:
                normalized.append(item)
        return normalized

    def admit_next(self, *, now: float | None = None) -> QueueItem | None:
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            items, sequence, paused, backpressure_events = self._read()
            items = self._normalize_expired(items, current)
            if paused:
                self._write(items, sequence, paused, backpressure_events)
                return None
            candidates = [item for item in items if item.state == "QUEUED" and item.not_before_epoch <= current]
            if not candidates:
                self._write(items, sequence, paused, backpressure_events)
                return None
            selected = min(candidates, key=lambda item: (-(item.priority + int(max(0.0, current - item.enqueued_at) / self.aging_seconds)), item.sequence, item.queue_id))
            admitted = replace(selected, state="ADMITTED", admitted_at=current, item_digest=None)
            items = [admitted if item.queue_id == selected.queue_id else item for item in items]
            self._write(items, sequence, paused, backpressure_events)
            return admitted

    def dispatch(self, queue_id: str, *, now: float | None = None) -> QueueItem:
        _id(queue_id, "queue_id")
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            items, sequence, paused, backpressure_events = self._read()
            items = self._normalize_expired(items, current)
            selected = next((item for item in items if item.queue_id == queue_id), None)
            if selected is None or selected.state != "ADMITTED":
                raise QueueNotDispatchable("only an admitted item may cross the dispatch boundary")
            if paused:
                raise QueueNotDispatchable("queue is paused")
            dispatched = replace(selected, state="DISPATCHED", dispatched_at=current, item_digest=None)
            items = [dispatched if item.queue_id == queue_id else item for item in items]
            self._write(items, sequence, paused, backpressure_events)
            return dispatched

    def cancel(self, queue_id: str, *, reason: str = "cancel requested") -> QueueItem:
        _id(queue_id, "queue_id")
        _text(reason, "reason")
        with FileLock(self.lock_path):
            items, sequence, paused, backpressure_events = self._read()
            selected = next((item for item in items if item.queue_id == queue_id), None)
            if selected is None:
                raise QueueControlError("queue item does not exist")
            if selected.state in {"QUEUED", "ADMITTED"}:
                state = "CANCELLED_BEFORE_DISPATCH"
            elif selected.state == "DISPATCHED":
                state = "CANCEL_REQUESTED_REQUIRES_RECONCILIATION"
            else:
                return selected
            updated = replace(selected, state=state, terminal_reason=reason, item_digest=None)
            items = [updated if item.queue_id == queue_id else item for item in items]
            self._write(items, sequence, paused, backpressure_events)
            return updated

    def complete(self, queue_id: str, state: str, *, reason: str) -> QueueItem:
        _id(queue_id, "queue_id")
        _text(reason, "reason")
        if state not in {"COMPLETED_VALIDATED", "FAILED", "REQUIRES_RECONCILIATION"}:
            raise QueueControlError("queue completion state is not allowed")
        with FileLock(self.lock_path):
            items, sequence, paused, backpressure_events = self._read()
            selected = next((item for item in items if item.queue_id == queue_id), None)
            if selected is None or selected.state not in {"DISPATCHED", "CANCEL_REQUESTED_REQUIRES_RECONCILIATION"}:
                raise QueueNotDispatchable("only dispatched items may be completed")
            updated = replace(selected, state=state, terminal_reason=reason, item_digest=None)
            items = [updated if item.queue_id == queue_id else item for item in items]
            self._write(items, sequence, paused, backpressure_events)
            return updated

    def get(self, queue_id: str) -> QueueItem:
        _id(queue_id, "queue_id")
        with FileLock(self.lock_path):
            item = next((entry for entry in self._read()[0] if entry.queue_id == queue_id), None)
        if item is None:
            raise QueueControlError("queue item does not exist")
        return item

    def pause(self) -> None:
        with FileLock(self.lock_path):
            items, sequence, _, backpressure_events = self._read()
            self._write(items, sequence, True, backpressure_events)

    def resume(self) -> None:
        with FileLock(self.lock_path):
            items, sequence, _, backpressure_events = self._read()
            self._write(items, sequence, False, backpressure_events)

    def expire(self, *, now: float | None = None) -> tuple[QueueItem, ...]:
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            items, sequence, paused, backpressure_events = self._read()
            normalized = self._normalize_expired(items, current)
            self._write(normalized, sequence, paused, backpressure_events)
        return tuple(item for before, item in zip(items, normalized) if before.state in ACTIVE_QUEUE_STATES and item.state == "EXPIRED_BEFORE_DISPATCH")

    def audit(self) -> dict[str, Any]:
        with FileLock(self.lock_path):
            items, sequence, paused, backpressure_events = self._read()
        counts = {state: sum(item.state == state for item in items) for state in sorted(QUEUE_STATES)}
        return {"status": "PASS", "schema": QUEUE_SCHEMA, "paused": paused, "next_sequence": sequence, "depth": sum(counts[state] for state in ACTIVE_QUEUE_STATES), "state_counts": counts, "backpressure_events": backpressure_events, "claim_ceiling": "Queue admission and dispatch state only; no worker execution or external completion authority."}


__all__ = ["ACTIVE_QUEUE_STATES", "QueueAdmissionError", "QueueControlError", "QueueItem", "QueueNotDispatchable", "QUEUE_SCHEMA", "QUEUE_STATES", "WorkQueue"]
