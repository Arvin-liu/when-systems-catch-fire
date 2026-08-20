"""Append-only, namespace-scoped operational memory durability R2."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Iterable, Mapping, Sequence

from agent_kernel.contracts import sha256_json

from .control import FileLock, _atomic_json, utc_now


DURABLE_MEMORY_SCHEMA = "ignition-durability-operational-memory-r2"
DURABLE_MEMORY_EVENT_SCHEMA = "ignition-durability-operational-memory-event-r2"
DURABLE_MEMORY_EPOCH = "operational-memory-epoch-2"
MEMORY_EVENT_TYPES = frozenset({"MEMORY_APPENDED", "MEMORY_SUPERSEDED", "MEMORY_EXPIRED", "MEMORY_FORGOTTEN", "MEMORY_TOMBSTONED", "SOFT_CONTEXT_EXPOSED"})
MEMORY_STATES = frozenset({"ACTIVE", "SUPERSEDED", "EXPIRED", "FORGOTTEN", "TOMBSTONED"})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "thoughts", "reasoning", "api_key", "access_token", "token", "cookie", "authorization", "secret"})


class DurableMemoryError(ValueError):
    """Raised when memory events, namespace scope or snapshots are unsafe."""


class MemoryNamespaceDenied(DurableMemoryError):
    """Raised when a memory operation crosses its namespace boundary."""


class MemorySnapshotIntegrityError(DurableMemoryError):
    """Raised when a memory snapshot is stale, partial or tampered."""


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or ".." in value:
        raise DurableMemoryError(f"{field} is not a canonical identifier")
    return value


def _public(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
        raise DurableMemoryError(f"{field} contains private or hidden content")
    return value


def _strings(values: Iterable[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise DurableMemoryError(f"{field} must be a string collection")
    return tuple(sorted({_public(item, f"{field}[]") for item in values}))


def _timestamp(value: Any, field: str) -> str:
    value = _public(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DurableMemoryError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise DurableMemoryError(f"{field} must include a timezone")
    return value


def _optional_timestamp(value: Any, field: str) -> str | None:
    return None if value is None else _timestamp(value, field)


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise DurableMemoryError(f"{field} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class DurableMemoryRecord:
    memory_id: str
    namespace_id: str
    memory_scope: str
    semantic_key: str
    source_event_ref: str
    source_run_id: str
    schema_epoch: str
    created_at: str
    summary: str
    tags: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    state: str = "ACTIVE"
    supersedes: str | None = None
    superseded_by: str | None = None
    expires_at: str | None = None
    integrity_sha256: str | None = None

    def __post_init__(self) -> None:
        for field in ("memory_id", "namespace_id", "memory_scope", "semantic_key", "source_event_ref", "source_run_id"):
            _id(getattr(self, field), field)
        if self.schema_epoch != DURABLE_MEMORY_EPOCH:
            raise DurableMemoryError("memory schema epoch is unsupported")
        _timestamp(self.created_at, "created_at")
        _public(self.summary, "summary")
        object.__setattr__(self, "tags", _strings(self.tags, "tags"))
        object.__setattr__(self, "provenance_refs", _strings(self.provenance_refs, "provenance_refs"))
        if self.state not in MEMORY_STATES:
            raise DurableMemoryError(f"unknown memory state: {self.state}")
        if self.supersedes is not None:
            _id(self.supersedes, "supersedes")
        if self.superseded_by is not None:
            _id(self.superseded_by, "superseded_by")
        object.__setattr__(self, "expires_at", _optional_timestamp(self.expires_at, "expires_at"))
        expected = sha256_json(self._body())
        if self.integrity_sha256 is not None and self.integrity_sha256 != expected:
            raise DurableMemoryError("memory record integrity mismatch")
        object.__setattr__(self, "integrity_sha256", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id, "namespace_id": self.namespace_id, "memory_scope": self.memory_scope,
            "semantic_key": self.semantic_key, "source_event_ref": self.source_event_ref, "source_run_id": self.source_run_id,
            "schema_epoch": self.schema_epoch, "created_at": self.created_at, "summary": self.summary, "tags": list(self.tags),
            "provenance_refs": list(self.provenance_refs), "state": self.state, "supersedes": self.supersedes,
            "superseded_by": self.superseded_by, "expires_at": self.expires_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "integrity_sha256": self.integrity_sha256}

    @classmethod
    def create(cls, *, memory_id: str, namespace_id: str, memory_scope: str, semantic_key: str, source_event_ref: str, source_run_id: str, summary: str, tags: Sequence[str] = (), provenance_refs: Sequence[str] = (), created_at: str | None = None, expires_at: str | None = None, supersedes: str | None = None) -> "DurableMemoryRecord":
        return cls(memory_id, namespace_id, memory_scope, semantic_key, source_event_ref, source_run_id, DURABLE_MEMORY_EPOCH, created_at or utc_now(), summary, tuple(tags), tuple(provenance_refs), "ACTIVE", supersedes=supersedes, expires_at=expires_at)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DurableMemoryRecord":
        required = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required:
            raise DurableMemoryError("memory record keys mismatch")
        return cls(**dict(data))


@dataclass(frozen=True)
class DurableMemoryEvent:
    event_id: str
    sequence: int
    event_type: str
    memory_id: str
    namespace_id: str
    schema_epoch: str
    payload: Mapping[str, Any]
    occurred_at: float
    idempotency_key: str
    previous_event_hash: str
    event_hash: str | None = None

    def __post_init__(self) -> None:
        for field in ("event_id", "memory_id", "namespace_id", "idempotency_key"):
            _id(getattr(self, field), field)
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise DurableMemoryError("memory event sequence must be non-negative")
        if self.event_type not in MEMORY_EVENT_TYPES:
            raise DurableMemoryError("unknown memory event type")
        if self.schema_epoch != DURABLE_MEMORY_EPOCH:
            raise DurableMemoryError("memory event schema epoch is unsupported")
        if not isinstance(self.occurred_at, (int, float)) or self.occurred_at < 0:
            raise DurableMemoryError("memory event occurred_at must be non-negative")
        _digest(self.previous_event_hash, "previous_event_hash")
        _public_json(self.payload, "event.payload")
        expected = sha256_json(self._unsigned_dict())
        if self.event_hash is not None and self.event_hash != expected:
            raise DurableMemoryError("memory event hash mismatch")
        object.__setattr__(self, "event_hash", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema": DURABLE_MEMORY_EVENT_SCHEMA, "event_id": self.event_id, "sequence": self.sequence,
            "event_type": self.event_type, "memory_id": self.memory_id, "namespace_id": self.namespace_id,
            "schema_epoch": self.schema_epoch, "payload": dict(self.payload), "occurred_at": self.occurred_at,
            "idempotency_key": self.idempotency_key, "previous_event_hash": self.previous_event_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "event_hash": self.event_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DurableMemoryEvent":
        required = set(cls.__dataclass_fields__) | {"schema"}  # type: ignore[attr-defined]
        if not isinstance(data, Mapping) or set(data) != required or data.get("schema") != DURABLE_MEMORY_EVENT_SCHEMA:
            raise DurableMemoryError("memory event keys/schema mismatch")
        return cls(event_id=data["event_id"], sequence=data["sequence"], event_type=data["event_type"], memory_id=data["memory_id"], namespace_id=data["namespace_id"], schema_epoch=data["schema_epoch"], payload=data["payload"], occurred_at=data["occurred_at"], idempotency_key=data["idempotency_key"], previous_event_hash=data["previous_event_hash"], event_hash=data["event_hash"])


def _public_json(value: Any, field: str) -> Any:
    if isinstance(value, str):
        return _public(value, field)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if not isinstance(key, str) or not key.strip() or any(marker in key.casefold() for marker in _FORBIDDEN):
                raise DurableMemoryError(f"{field} contains a private field")
            result[key] = _public_json(child, f"{field}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_public_json(child, f"{field}[]") for child in value]
    raise DurableMemoryError(f"{field} is not JSON-safe")


class DurableOperationalMemoryStore:
    """Namespace-scoped event store; projections are rebuilt from its chain."""

    def __init__(self, path: str | Path, *, snapshot_path: str | Path | None = None) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.snapshot_path = Path(snapshot_path) if snapshot_path is not None else self.path.with_suffix(".snapshot.json")

    def _read_unlocked(self) -> list[DurableMemoryEvent]:
        if not self.path.exists():
            return []
        events: list[DurableMemoryEvent] = []
        previous = "0" * 64
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise DurableMemoryError("memory event ledger cannot be read") from exc
        for line_number, line in enumerate(lines, 1):
            try:
                event = DurableMemoryEvent.from_dict(json.loads(line))
            except (json.JSONDecodeError, TypeError, DurableMemoryError) as exc:
                raise DurableMemoryError(f"invalid memory event at line {line_number}") from exc
            if event.sequence != len(events) or event.previous_event_hash != previous:
                raise DurableMemoryError("memory event chain is not contiguous")
            events.append(event)
            previous = event.event_hash or previous
        self._replay(events)
        return events

    def events(self) -> tuple[DurableMemoryEvent, ...]:
        with FileLock(self.lock_path):
            return tuple(self._read_unlocked())

    def _append_unlocked(self, event: DurableMemoryEvent, events: list[DurableMemoryEvent]) -> None:
        if event.sequence != len(events) or event.previous_event_hash != (events[-1].event_hash if events else "0" * 64):
            raise DurableMemoryError("memory event append is not the next chain event")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _redact(record: DurableMemoryRecord, state: str) -> DurableMemoryRecord:
        return replace(record, state=state, summary="[REDACTED_OPERATIONAL_MEMORY]", tags=(), provenance_refs=(), integrity_sha256=None)

    def _replay(self, events: Iterable[DurableMemoryEvent]) -> dict[str, Any]:
        records: dict[str, DurableMemoryRecord] = {}
        soft: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        for event in events:
            if event.idempotency_key in seen_keys:
                raise DurableMemoryError("duplicate memory event idempotency key")
            seen_keys.add(event.idempotency_key)
            if event.event_type == "MEMORY_APPENDED":
                if event.memory_id in records:
                    raise DurableMemoryError("memory append duplicated an existing memory id")
                record = DurableMemoryRecord.from_dict(event.payload["record"])
                if record.memory_id != event.memory_id or record.namespace_id != event.namespace_id:
                    raise MemoryNamespaceDenied("memory append namespace mismatch")
                records[event.memory_id] = record
            elif event.event_type == "MEMORY_SUPERSEDED":
                old_id = event.payload["old_memory_id"]
                replacement = DurableMemoryRecord.from_dict(event.payload["replacement"])
                old = records.get(old_id)
                if old is None or old.state != "ACTIVE" or replacement.supersedes != old_id:
                    raise DurableMemoryError("invalid memory supersession lineage")
                if replacement.namespace_id != old.namespace_id or replacement.memory_id != event.memory_id:
                    raise MemoryNamespaceDenied("memory supersession crosses namespace")
                records[old_id] = replace(old, state="SUPERSEDED", superseded_by=replacement.memory_id, integrity_sha256=None)
                if replacement.memory_id in records:
                    raise DurableMemoryError("supersession replacement already exists")
                records[replacement.memory_id] = replacement
            elif event.event_type in {"MEMORY_EXPIRED", "MEMORY_FORGOTTEN", "MEMORY_TOMBSTONED"}:
                record = records.get(event.memory_id)
                if record is None or record.namespace_id != event.namespace_id:
                    raise MemoryNamespaceDenied("memory action namespace mismatch")
                target = {"MEMORY_EXPIRED": "EXPIRED", "MEMORY_FORGOTTEN": "FORGOTTEN", "MEMORY_TOMBSTONED": "TOMBSTONED"}[event.event_type]
                records[event.memory_id] = self._redact(record, target)
            else:
                pointer = dict(event.payload)
                if pointer.get("status") != "ADVISORY_ONLY" or pointer.get("claim_ceiling") != "SOFT_CONTEXT_POINTER_NOT_TRUTH_OR_AUTHORITY":
                    raise DurableMemoryError("soft context pointer is not advisory-only")
                soft.append({"event_id": event.event_id, "namespace_id": event.namespace_id, **pointer})
        return {"records": records, "soft_context_exposures": tuple(soft), "seen_idempotency": seen_keys}

    def replay(self) -> dict[str, Any]:
        with FileLock(self.lock_path):
            events = self._read_unlocked()
            state = self._replay(events)
        return {"records": dict(state["records"]), "soft_context_exposures": tuple(state["soft_context_exposures"]), "event_count": len(events), "head_hash": events[-1].event_hash if events else "0" * 64}

    def _append_event(self, event: DurableMemoryEvent) -> None:
        with FileLock(self.lock_path):
            events = self._read_unlocked()
            if any(item.idempotency_key == event.idempotency_key for item in events):
                raise DurableMemoryError("memory event idempotency key already exists")
            self._append_unlocked(event, events)

    def _new_event(self, *, event_type: str, memory_id: str, namespace_id: str, payload: Mapping[str, Any], idempotency_key: str, occurred_at: float | None = None) -> DurableMemoryEvent:
        _id(memory_id, "memory_id")
        _id(namespace_id, "namespace_id")
        _id(idempotency_key, "idempotency_key")
        with FileLock(self.lock_path):
            events = self._read_unlocked()
            return DurableMemoryEvent(event_id=f"memory-event-{event_type.casefold().replace('_', '-')}-{len(events)}", sequence=len(events), event_type=event_type, memory_id=memory_id, namespace_id=namespace_id, schema_epoch=DURABLE_MEMORY_EPOCH, payload=dict(payload), occurred_at=float(time.time() if occurred_at is None else occurred_at), idempotency_key=idempotency_key, previous_event_hash=events[-1].event_hash if events else "0" * 64)

    def append(self, record: DurableMemoryRecord, *, idempotency_key: str | None = None, occurred_at: float | None = None) -> DurableMemoryRecord:
        if not isinstance(record, DurableMemoryRecord) or record.state != "ACTIVE" or record.supersedes is not None:
            raise DurableMemoryError("append accepts a fresh ACTIVE memory record")
        key = idempotency_key or f"append-{record.memory_id}"
        event = self._new_event(event_type="MEMORY_APPENDED", memory_id=record.memory_id, namespace_id=record.namespace_id, payload={"record": record.to_dict()}, idempotency_key=key, occurred_at=occurred_at)
        self._append_event(event)
        return record

    def _require_in_namespace(self, memory_id: str, namespace_id: str) -> DurableMemoryRecord:
        _id(memory_id, "memory_id")
        _id(namespace_id, "namespace_id")
        record = self.replay()["records"].get(memory_id)
        if record is None:
            raise DurableMemoryError("memory does not exist")
        if record.namespace_id != namespace_id:
            raise MemoryNamespaceDenied("memory belongs to another namespace")
        return record

    def supersede(self, old_memory_id: str, replacement: DurableMemoryRecord, *, namespace_id: str, occurred_at: float | None = None) -> DurableMemoryRecord:
        old = self._require_in_namespace(old_memory_id, namespace_id)
        if old.state != "ACTIVE" or replacement.state != "ACTIVE" or replacement.supersedes != old_memory_id:
            raise DurableMemoryError("supersession requires an active replacement naming the old memory")
        if replacement.namespace_id != namespace_id:
            raise MemoryNamespaceDenied("replacement namespace mismatch")
        event = self._new_event(event_type="MEMORY_SUPERSEDED", memory_id=replacement.memory_id, namespace_id=namespace_id, payload={"old_memory_id": old_memory_id, "replacement": replacement.to_dict()}, idempotency_key=f"supersede-{old_memory_id}-{replacement.memory_id}", occurred_at=occurred_at)
        self._append_event(event)
        return replacement

    def _transition(self, memory_id: str, namespace_id: str, event_type: str, *, reason: str, occurred_at: float | None = None) -> DurableMemoryRecord:
        old = self._require_in_namespace(memory_id, namespace_id)
        if old.state in {"FORGOTTEN", "EXPIRED", "TOMBSTONED"}:
            return old
        _public(reason, "reason")
        event = self._new_event(event_type=event_type, memory_id=memory_id, namespace_id=namespace_id, payload={"reason": reason, "original_integrity_sha256": old.integrity_sha256}, idempotency_key=f"{event_type.casefold()}-{memory_id}", occurred_at=occurred_at)
        self._append_event(event)
        return self.replay()["records"][memory_id]

    def expire(self, memory_id: str, *, namespace_id: str, reason: str = "memory expiry policy", occurred_at: float | None = None) -> DurableMemoryRecord:
        return self._transition(memory_id, namespace_id, "MEMORY_EXPIRED", reason=reason, occurred_at=occurred_at)

    def forget(self, memory_id: str, *, namespace_id: str, reason: str = "memory forget request", occurred_at: float | None = None) -> DurableMemoryRecord:
        return self._transition(memory_id, namespace_id, "MEMORY_FORGOTTEN", reason=reason, occurred_at=occurred_at)

    def tombstone(self, memory_id: str, *, namespace_id: str, reason: str = "memory tombstone", occurred_at: float | None = None) -> DurableMemoryRecord:
        return self._transition(memory_id, namespace_id, "MEMORY_TOMBSTONED", reason=reason, occurred_at=occurred_at)

    def expose_soft_context(self, *, pointer_ref: str, source_namespace_id: str, target_namespace_id: str, occurred_at: float | None = None) -> dict[str, Any]:
        _id(pointer_ref, "pointer_ref")
        _id(source_namespace_id, "source_namespace_id")
        _id(target_namespace_id, "target_namespace_id")
        payload = {"pointer_ref": pointer_ref, "source_namespace_id": source_namespace_id, "target_namespace_id": target_namespace_id, "status": "ADVISORY_ONLY", "claim_ceiling": "SOFT_CONTEXT_POINTER_NOT_TRUTH_OR_AUTHORITY"}
        event = self._new_event(event_type="SOFT_CONTEXT_EXPOSED", memory_id=f"soft-pointer-{pointer_ref}", namespace_id=source_namespace_id, payload=payload, idempotency_key=f"soft-context-{pointer_ref}-{target_namespace_id}", occurred_at=occurred_at)
        self._append_event(event)
        return {"event_id": event.event_id, **payload}

    def query(self, *, namespace_id: str, semantic_key: str | None = None, include_inactive: bool = False) -> list[DurableMemoryRecord]:
        _id(namespace_id, "namespace_id")
        if semantic_key is not None:
            _id(semantic_key, "semantic_key")
        records = self.replay()["records"].values()
        result = [item for item in records if item.namespace_id == namespace_id and (include_inactive or item.state == "ACTIVE") and (semantic_key is None or item.semantic_key == semantic_key)]
        return sorted(result, key=lambda item: (item.semantic_key, item.created_at, item.memory_id))

    def snapshot(self, *, namespace_id: str, persist: bool = True) -> dict[str, Any]:
        _id(namespace_id, "namespace_id")
        with FileLock(self.lock_path):
            events = self._read_unlocked()
            state = self._replay(events)
        records = [record.to_dict() for record in sorted(state["records"].values(), key=lambda item: item.memory_id) if record.namespace_id == namespace_id]
        soft = [item for item in state["soft_context_exposures"] if item["namespace_id"] == namespace_id]
        snapshot = {"schema": DURABLE_MEMORY_SCHEMA, "schema_epoch": DURABLE_MEMORY_EPOCH, "namespace_id": namespace_id, "event_count": len(events), "ledger_head_hash": events[-1].event_hash if events else "0" * 64, "records": records, "soft_context_exposures": soft, "claim_ceiling": "Operational memory only; soft context remains advisory and cannot become truth or authority."}
        snapshot["state_sha256"] = sha256_json({key: snapshot[key] for key in ("schema", "schema_epoch", "namespace_id", "event_count", "ledger_head_hash", "records", "soft_context_exposures", "claim_ceiling")})
        if persist:
            _atomic_json(self.snapshot_path, snapshot)
        return snapshot

    @staticmethod
    def restore_snapshot(snapshot: Mapping[str, Any], *, namespace_id: str) -> dict[str, Any]:
        if not isinstance(snapshot, Mapping) or snapshot.get("schema") != DURABLE_MEMORY_SCHEMA or snapshot.get("schema_epoch") != DURABLE_MEMORY_EPOCH:
            raise MemorySnapshotIntegrityError("memory snapshot schema mismatch")
        _id(namespace_id, "namespace_id")
        if snapshot.get("namespace_id") != namespace_id:
            raise MemoryNamespaceDenied("memory snapshot namespace mismatch")
        required = {"schema", "schema_epoch", "namespace_id", "event_count", "ledger_head_hash", "records", "soft_context_exposures", "claim_ceiling", "state_sha256"}
        if set(snapshot) != required:
            raise MemorySnapshotIntegrityError("memory snapshot keys mismatch")
        _digest(snapshot["ledger_head_hash"], "ledger_head_hash")
        expected = sha256_json({key: snapshot[key] for key in ("schema", "schema_epoch", "namespace_id", "event_count", "ledger_head_hash", "records", "soft_context_exposures", "claim_ceiling")})
        if snapshot["state_sha256"] != expected:
            raise MemorySnapshotIntegrityError("memory snapshot digest mismatch")
        if snapshot["claim_ceiling"] != "Operational memory only; soft context remains advisory and cannot become truth or authority.":
            raise MemorySnapshotIntegrityError("memory snapshot claim ceiling changed")
        records = [DurableMemoryRecord.from_dict(item) for item in snapshot["records"]]
        if any(record.namespace_id != namespace_id for record in records):
            raise MemoryNamespaceDenied("memory snapshot contains another namespace")
        soft = [_public_json(item, "soft_context_exposures[]") for item in snapshot["soft_context_exposures"]]
        if any(item.get("status") != "ADVISORY_ONLY" for item in soft):
            raise MemorySnapshotIntegrityError("soft context snapshot is not advisory")
        return {"namespace_id": namespace_id, "records": tuple(records), "soft_context_exposures": tuple(soft), "event_count": snapshot["event_count"], "ledger_head_hash": snapshot["ledger_head_hash"], "state_sha256": snapshot["state_sha256"]}

    def audit(self, *, namespace_id: str | None = None) -> dict[str, Any]:
        state = self.replay()
        records = list(state["records"].values())
        if namespace_id is not None:
            _id(namespace_id, "namespace_id")
            records = [item for item in records if item.namespace_id == namespace_id]
        return {"status": "PASS", "schema": DURABLE_MEMORY_SCHEMA, "schema_epoch": DURABLE_MEMORY_EPOCH, "event_count": state["event_count"], "record_count": len(records), "active_count": sum(item.state == "ACTIVE" for item in records), "soft_context_count": len(state["soft_context_exposures"]), "claim_ceiling": "Operational memory recall and integrity only; not Knowledge truth, permission or Owner authority."}


__all__ = ["DURABLE_MEMORY_EPOCH", "DURABLE_MEMORY_EVENT_SCHEMA", "DURABLE_MEMORY_SCHEMA", "DurableMemoryError", "DurableMemoryEvent", "DurableMemoryRecord", "DurableOperationalMemoryStore", "MemoryNamespaceDenied", "MemorySnapshotIntegrityError", "MEMORY_EVENT_TYPES", "MEMORY_STATES"]
