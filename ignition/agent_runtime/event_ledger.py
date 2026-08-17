"""Append-only canonical operational events for OS Control Plane R2.

The ledger is a runtime coordination primitive, not a Git-backed lock and not
a Knowledge registry.  It stores bounded public payloads, enforces per-
aggregate compare-and-swap versions, chains every record, and can rebuild a
deterministic operational snapshot after a process or snapshot failure.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence

from agent_kernel.contracts import _id, _string, _summary, _tuple_strings, sha256_json

from .control import FileLock, _atomic_json, utc_now


EVENT_LEDGER_SCHEMA = "os-control-plane-event-ledger-r1"
EVENT_SCHEMA = "os-control-plane-event-r1"
ZERO_HASH = "0" * 64
EVENT_TYPES = frozenset({
    "EPISODE_CREATED",
    "RUN_READY",
    "RUN_LEASED",
    "RUN_STARTED",
    "RUN_CHECKPOINTED",
    "RUN_TERMINAL",
    "ROUTE_SELECTED",
    "ROUTE_REJECTED",
    "APPROVAL_REQUESTED",
    "APPROVAL_DECIDED",
    "APPROVAL_STALE",
    "RESOURCE_INTENT_ACQUIRED",
    "RESOURCE_INTENT_RELEASED",
    "RESOURCE_INTENT_CONFLICTED",
    "DISPATCH_CREATED",
    "DISPATCH_ACCEPTED",
    "DISPATCH_PROGRESS",
    "DISPATCH_RECEIPT",
    "VALIDATION_RECORDED",
    "RECONCILIATION_RECORDED",
    "CANCELLATION_REQUESTED",
    "DEADLINE_EXPIRED",
    "MEMORY_ABSORBED",
    "MEMORY_TOMBSTONED",
    "EXECUTOR_HEALTH_CHANGED",
})
SENSITIVITY_CLASSES = frozenset({"PUBLIC_OPERATIONAL", "INTERNAL_OPERATIONAL", "SENSITIVE_REFERENCE"})
RETENTION_CLASSES = frozenset({"RUN", "SHORT", "LONG", "UNTIL_FORGOTTEN"})
_HASH = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_MARKERS = (
    "access_token",
    "api_key",
    "bearer ",
    "client_secret",
    "password",
    "private model reasoning",
    "hidden reasoning",
    "chain-of-thought",
    "chain of thought",
    "full_prompt",
    "raw_prompt",
    "prompt_body",
    "completion_text",
)


class EventLedgerError(RuntimeError):
    """Base error for an unreadable or unsafe operational ledger."""


class LedgerCorruptionError(EventLedgerError):
    """Raised when the append-only chain or payload integrity is invalid."""


class StaleWriterError(EventLedgerError):
    """Raised when a writer's aggregate version is no longer current."""


class DuplicateEventError(EventLedgerError):
    """Raised when an event or idempotency key is replayed."""


class SnapshotMismatchError(EventLedgerError):
    """Raised when a snapshot is not a valid prefix of the current ledger."""


def _public_value(value: Any, field: str = "payload") -> Any:
    """Copy a bounded JSON value while rejecting secret/reasoning material."""

    if isinstance(value, str):
        lowered = value.casefold()
        if any(marker in lowered for marker in _FORBIDDEN_MARKERS):
            raise EventLedgerError(f"{field} contains forbidden secret or hidden-reasoning material")
        if "prompt" in lowered:
            raise EventLedgerError(f"{field} contains a prompt body")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value, key=lambda item: str(item)):
            if not isinstance(key, str) or not key.strip():
                raise EventLedgerError(f"{field} keys must be non-empty strings")
            if any(marker in key.casefold() for marker in _FORBIDDEN_MARKERS) or "prompt" in key.casefold():
                raise EventLedgerError(f"{field}.{key} is not a permitted public field")
            result[key] = _public_value(value[key], f"{field}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_public_value(item, f"{field}[]") for item in value]
    raise EventLedgerError(f"{field} contains a non-JSON value")


def _timestamp(value: str, field: str = "occurred_at") -> str:
    _string(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EventLedgerError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise EventLedgerError(f"{field} must include a timezone")
    return value


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise EventLedgerError(f"{field} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class CanonicalEvent:
    event_id: str
    sequence: int
    aggregate_id: str
    aggregate_version: int
    event_type: str
    event_version: int
    occurred_at: str
    actor_ref: str
    source_refs: tuple[str, ...]
    precondition_version: int
    payload_hash: str
    payload: Mapping[str, Any]
    previous_event_hash: str
    sensitivity: str
    retention_class: str
    idempotency_key: str
    event_hash: str = ""

    def __post_init__(self) -> None:
        _id(self.event_id, "event_id")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 0:
            raise EventLedgerError("sequence must be a non-negative integer")
        _id(self.aggregate_id, "aggregate_id")
        if not isinstance(self.aggregate_version, int) or self.aggregate_version <= 0:
            raise EventLedgerError("aggregate_version must be a positive integer")
        if self.event_type not in EVENT_TYPES:
            raise EventLedgerError(f"unknown event_type: {self.event_type}")
        if not isinstance(self.event_version, int) or self.event_version <= 0:
            raise EventLedgerError("event_version must be a positive integer")
        _timestamp(self.occurred_at)
        _id(self.actor_ref, "actor_ref")
        object.__setattr__(self, "source_refs", _tuple_strings(self.source_refs, "source_refs"))
        if not isinstance(self.precondition_version, int) or self.precondition_version < 0:
            raise EventLedgerError("precondition_version must be a non-negative integer")
        object.__setattr__(self, "payload", _public_value(self.payload))
        _hash(self.payload_hash, "payload_hash")
        if self.payload_hash != sha256_json(self.payload):
            raise LedgerCorruptionError(f"payload hash mismatch for {self.event_id}")
        _hash(self.previous_event_hash, "previous_event_hash")
        if self.sensitivity not in SENSITIVITY_CLASSES:
            raise EventLedgerError(f"unknown sensitivity: {self.sensitivity}")
        if self.retention_class not in RETENTION_CLASSES:
            raise EventLedgerError(f"unknown retention_class: {self.retention_class}")
        _id(self.idempotency_key, "idempotency_key")
        if self.event_hash:
            _hash(self.event_hash, "event_hash")

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema": EVENT_SCHEMA,
            "event_id": self.event_id,
            "sequence": self.sequence,
            "aggregate_id": self.aggregate_id,
            "aggregate_version": self.aggregate_version,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at,
            "actor_ref": self.actor_ref,
            "source_refs": list(self.source_refs),
            "precondition_version": self.precondition_version,
            "payload_hash": self.payload_hash,
            "payload": self.payload,
            "previous_event_hash": self.previous_event_hash,
            "sensitivity": self.sensitivity,
            "retention_class": self.retention_class,
            "idempotency_key": self.idempotency_key,
        }

    def with_hash(self) -> "CanonicalEvent":
        return replace(self, event_hash=sha256_json(self.unsigned_dict()))

    def to_dict(self) -> dict[str, Any]:
        data = self.unsigned_dict()
        data["event_hash"] = self.event_hash or sha256_json(data)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CanonicalEvent":
        required = {
            "schema", "event_id", "sequence", "aggregate_id", "aggregate_version", "event_type",
            "event_version", "occurred_at", "actor_ref", "source_refs", "precondition_version",
            "payload_hash", "payload", "previous_event_hash", "sensitivity", "retention_class",
            "idempotency_key", "event_hash",
        }
        if set(data) != required or data.get("schema") != EVENT_SCHEMA:
            raise LedgerCorruptionError("event schema or keys mismatch")
        event = cls(
            event_id=data["event_id"], sequence=data["sequence"], aggregate_id=data["aggregate_id"],
            aggregate_version=data["aggregate_version"], event_type=data["event_type"],
            event_version=data["event_version"], occurred_at=data["occurred_at"], actor_ref=data["actor_ref"],
            source_refs=tuple(data["source_refs"]), precondition_version=data["precondition_version"],
            payload_hash=data["payload_hash"], payload=data["payload"],
            previous_event_hash=data["previous_event_hash"], sensitivity=data["sensitivity"],
            retention_class=data["retention_class"], idempotency_key=data["idempotency_key"],
            event_hash=data["event_hash"],
        )
        if event.event_hash != sha256_json(event.unsigned_dict()):
            raise LedgerCorruptionError(f"event hash mismatch for {event.event_id}")
        return event


class EventLedger:
    """A locked JSONL event chain with per-aggregate CAS and replay."""

    def __init__(self, path: str | Path, *, snapshot_path: str | Path | None = None) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.snapshot_path = Path(snapshot_path) if snapshot_path is not None else self.path.with_suffix(".snapshot.json")

    def _read_unlocked(self) -> list[CanonicalEvent]:
        if not self.path.exists():
            return []
        try:
            raw_lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise EventLedgerError("event ledger cannot be read") from exc
        events: list[CanonicalEvent] = []
        previous = ZERO_HASH
        versions: dict[str, int] = {}
        seen_ids: set[str] = set()
        seen_idempotency: set[str] = set()
        for line_number, line in enumerate(raw_lines, 1):
            if not line.strip():
                raise LedgerCorruptionError(f"blank ledger line at {line_number}")
            try:
                event = CanonicalEvent.from_dict(json.loads(line))
            except (json.JSONDecodeError, TypeError, EventLedgerError) as exc:
                raise LedgerCorruptionError(f"invalid JSON at ledger line {line_number}") from exc
            if event.sequence != len(events):
                raise LedgerCorruptionError(f"sequence gap at ledger line {line_number}")
            if event.previous_event_hash != previous:
                raise LedgerCorruptionError(f"previous-event hash mismatch at ledger line {line_number}")
            if event.event_id in seen_ids or event.idempotency_key in seen_idempotency:
                raise LedgerCorruptionError(f"duplicate event identity at ledger line {line_number}")
            expected_before = versions.get(event.aggregate_id, 0)
            if event.precondition_version != expected_before or event.aggregate_version != expected_before + 1:
                raise LedgerCorruptionError(f"aggregate version gap for {event.aggregate_id}")
            seen_ids.add(event.event_id)
            seen_idempotency.add(event.idempotency_key)
            versions[event.aggregate_id] = event.aggregate_version
            previous = event.event_hash
            events.append(event)
        return events

    def events(self) -> list[CanonicalEvent]:
        with FileLock(self.lock_path):
            return self._read_unlocked()

    def current_version(self, aggregate_id: str) -> int:
        _id(aggregate_id, "aggregate_id")
        events = self.events()
        return next((event.aggregate_version for event in reversed(events) if event.aggregate_id == aggregate_id), 0)

    def append_event(
        self,
        *,
        aggregate_id: str,
        event_type: str,
        payload: Mapping[str, Any],
        actor_ref: str = "os-control-plane",
        source_refs: Sequence[str] = (),
        expected_version: int | None = None,
        event_id: str | None = None,
        idempotency_key: str | None = None,
        occurred_at: str | None = None,
        event_version: int = 1,
        sensitivity: str = "INTERNAL_OPERATIONAL",
        retention_class: str = "LONG",
    ) -> CanonicalEvent:
        _id(aggregate_id, "aggregate_id")
        _id(actor_ref, "actor_ref")
        public_payload = _public_value(payload)
        with FileLock(self.lock_path):
            events = self._read_unlocked()
            actual_version = next((event.aggregate_version for event in reversed(events) if event.aggregate_id == aggregate_id), 0)
            if expected_version is not None and expected_version != actual_version:
                raise StaleWriterError(
                    f"stale writer for {aggregate_id}: expected {expected_version}, current {actual_version}"
                )
            if event_id is None:
                event_id = f"event-{aggregate_id}-{actual_version + 1}-{sha256_json(public_payload)[:12]}"
            if idempotency_key is None:
                idempotency_key = f"idem-{event_id}"
            _id(event_id, "event_id")
            _id(idempotency_key, "idempotency_key")
            if any(existing.event_id == event_id or existing.idempotency_key == idempotency_key for existing in events):
                raise DuplicateEventError(f"event identity or idempotency key already exists: {event_id}")
            event = CanonicalEvent(
                event_id=event_id,
                sequence=len(events),
                aggregate_id=aggregate_id,
                aggregate_version=actual_version + 1,
                event_type=event_type,
                event_version=event_version,
                occurred_at=occurred_at or utc_now(),
                actor_ref=actor_ref,
                source_refs=tuple(source_refs),
                precondition_version=actual_version,
                payload_hash=sha256_json(public_payload),
                payload=public_payload,
                previous_event_hash=events[-1].event_hash if events else ZERO_HASH,
                sensitivity=sensitivity,
                retention_class=retention_class,
                idempotency_key=idempotency_key,
            ).with_hash()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
            return event

    def audit(self) -> dict[str, Any]:
        events = self.events()
        return {
            "status": "PASS",
            "schema": EVENT_LEDGER_SCHEMA,
            "event_count": len(events),
            "aggregate_count": len({event.aggregate_id for event in events}),
            "head_hash": events[-1].event_hash if events else ZERO_HASH,
            "claim_ceiling": "Bounded operational event integrity and replay only; not truth, permission or Owner authority.",
        }

    @staticmethod
    def _default_reduce(state: dict[str, Any], event: CanonicalEvent) -> None:
        aggregates = state.setdefault("aggregates", {})
        aggregate = aggregates.setdefault(event.aggregate_id, {"version": 0, "status": None, "events": []})
        aggregate["version"] = event.aggregate_version
        aggregate["last_event_type"] = event.event_type
        aggregate["last_event_id"] = event.event_id
        aggregate["events"].append(event.event_id)
        payload = event.payload
        if isinstance(payload, Mapping):
            if isinstance(payload.get("status"), str):
                aggregate["status"] = payload["status"]
            patch = payload.get("state_patch")
            if isinstance(patch, Mapping):
                for key in sorted(patch):
                    aggregate[str(key)] = patch[key]

    def replay(
        self,
        *,
        reducer: Callable[[dict[str, Any], CanonicalEvent], None] | None = None,
        initial_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        events = self.events()
        state: dict[str, Any] = json.loads(json.dumps(initial_state or {}, ensure_ascii=False))
        reduce = reducer or self._default_reduce
        for event in events:
            reduce(state, event)
        state["event_count"] = len(events)
        state["head_hash"] = events[-1].event_hash if events else ZERO_HASH
        return state

    def snapshot(self) -> dict[str, Any]:
        events = self.events()
        data = {
            "schema": "os-control-plane-snapshot-r1",
            "captured_sequence": len(events),
            "captured_head_hash": events[-1].event_hash if events else ZERO_HASH,
            "state": self.replay(),
        }
        data["state_sha256"] = sha256_json(data["state"])
        _atomic_json(self.snapshot_path, data)
        return data

    def replay_snapshot(self, snapshot_path: str | Path | None = None) -> dict[str, Any]:
        path = Path(snapshot_path) if snapshot_path is not None else self.snapshot_path
        try:
            snapshot = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SnapshotMismatchError("snapshot is unreadable") from exc
        if snapshot.get("schema") != "os-control-plane-snapshot-r1":
            raise SnapshotMismatchError("snapshot schema mismatch")
        state = snapshot.get("state")
        if not isinstance(state, Mapping) or snapshot.get("state_sha256") != sha256_json(state):
            raise SnapshotMismatchError("snapshot state digest mismatch")
        events = self.events()
        captured = snapshot.get("captured_sequence")
        if not isinstance(captured, int) or captured < 0 or captured > len(events):
            raise SnapshotMismatchError("snapshot sequence is not a ledger prefix")
        prefix_hash = events[captured - 1].event_hash if captured else ZERO_HASH
        if prefix_hash != snapshot.get("captured_head_hash"):
            raise SnapshotMismatchError("snapshot head is not a ledger prefix")
        rebuilt: dict[str, Any] = json.loads(json.dumps(state, ensure_ascii=False))
        rebuilt.pop("event_count", None)
        rebuilt.pop("head_hash", None)
        for event in events[captured:]:
            self._default_reduce(rebuilt, event)
        rebuilt["event_count"] = len(events)
        rebuilt["head_hash"] = events[-1].event_hash if events else ZERO_HASH
        return rebuilt


__all__ = [
    "CanonicalEvent",
    "DuplicateEventError",
    "EVENT_LEDGER_SCHEMA",
    "EVENT_TYPES",
    "EventLedger",
    "EventLedgerError",
    "LedgerCorruptionError",
    "SnapshotMismatchError",
    "StaleWriterError",
    "ZERO_HASH",
]
