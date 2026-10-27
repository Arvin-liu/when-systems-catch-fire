"""Deterministic OS resource-intent arbitration for Control Plane R2.

This module grants no filesystem, network, message or Git capability.  It
only records which bounded work unit may concurrently claim a logical
resource.  Unknown/external side effects are deliberately conservative:
overlap is never concurrent and no automatic failover is implied.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import _id, sha256_json

from .control import FileLock, _atomic_json, utc_now


RESOURCE_SCHEMA = "os-control-plane-resource-arbiter-r1"
INTENT_TYPES = frozenset({
    "READ_SHARED",
    "WRITE_EXCLUSIVE",
    "APPEND_SHARED",
    "MUTATE_METADATA",
    "EXTERNAL_SIDE_EFFECT",
    "UNKNOWN_SIDE_EFFECT",
})
EXCLUSIVE_INTENTS = frozenset({"WRITE_EXCLUSIVE", "MUTATE_METADATA", "EXTERNAL_SIDE_EFFECT", "UNKNOWN_SIDE_EFFECT"})
_HASH_CHARS = set("0123456789abcdef")


class ResourceArbitrationError(RuntimeError):
    """Base arbitration failure."""


class ResourceConflict(ResourceArbitrationError):
    """An intent cannot be granted without overlapping an active/waiting claim."""

    def __init__(self, message: str, *, blockers: Sequence[Mapping[str, Any]] = (), reason: str = "CONFLICT") -> None:
        super().__init__(message)
        self.blockers = tuple(dict(item) for item in blockers)
        self.reason = reason


class DeadlockPreventionError(ResourceArbitrationError):
    """The caller presented multi-resource intents outside canonical order."""


class ResourceCorruptionError(ResourceArbitrationError):
    """Persisted resource state failed validation."""


def _timestamp(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise ResourceArbitrationError(f"{field} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ResourceArbitrationError(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ResourceArbitrationError(f"{field} must include a timezone")
    return value


def _resource_key(resource: str) -> tuple[str, str]:
    if not isinstance(resource, str) or ":" not in resource:
        raise ResourceArbitrationError("resource must be kind:canonical-name")
    kind, name = resource.split(":", 1)
    if not kind or not name or "\x00" in resource or "//" in name or "/../" in f"/{name}/":
        raise ResourceArbitrationError("resource must be canonical and non-empty")
    if name.startswith("/") and kind not in {"workspace", "repository"}:
        raise ResourceArbitrationError("absolute resources are limited to workspace/repository references")
    return kind, name


def resources_overlap(left: str, right: str) -> bool:
    """Conservative hierarchical overlap for canonical logical resources."""

    left_kind, left_name = _resource_key(left)
    right_kind, right_name = _resource_key(right)
    if left_kind != right_kind:
        return False
    if left_name == right_name:
        return True
    if left_kind in {"workspace", "repository"} and (left_name.startswith(right_name + "/") or right_name.startswith(left_name + "/")):
        return True
    for pattern, value in ((left_name, right_name), (right_name, left_name)):
        if pattern.endswith("/*") and value.startswith(pattern[:-1]):
            return True
    return False


def intents_conflict(left: "ResourceIntent", right: "ResourceIntent") -> bool:
    if not resources_overlap(left.resource, right.resource):
        return False
    if left.intent_type == "READ_SHARED" and right.intent_type == "READ_SHARED":
        return False
    if left.intent_type == "APPEND_SHARED" and right.intent_type == "APPEND_SHARED":
        return False
    # Unknown and external effects are never assumed safe or idempotent.
    if left.intent_type in {"UNKNOWN_SIDE_EFFECT", "EXTERNAL_SIDE_EFFECT"} or right.intent_type in {"UNKNOWN_SIDE_EFFECT", "EXTERNAL_SIDE_EFFECT"}:
        return True
    return True


@dataclass(frozen=True)
class ResourceIntent:
    intent_id: str
    run_id: str
    resource: str
    intent_type: str
    priority: int = 0
    created_at: str = ""
    ttl_seconds: float = 60.0

    def __post_init__(self) -> None:
        _id(self.intent_id, "intent_id")
        _id(self.run_id, "run_id")
        _resource_key(self.resource)
        if self.intent_type not in INTENT_TYPES:
            raise ResourceArbitrationError(f"unknown intent_type: {self.intent_type}")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool) or self.priority < 0:
            raise ResourceArbitrationError("priority must be a non-negative integer")
        _timestamp(self.created_at or utc_now(), "created_at")
        if not isinstance(self.ttl_seconds, (int, float)) or isinstance(self.ttl_seconds, bool) or self.ttl_seconds <= 0:
            raise ResourceArbitrationError("ttl_seconds must be positive")

    @property
    def canonical_key(self) -> tuple[str, str, str, str]:
        kind, name = _resource_key(self.resource)
        return kind, name, self.intent_type, self.intent_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "run_id": self.run_id,
            "resource": self.resource,
            "intent_type": self.intent_type,
            "priority": self.priority,
            "created_at": self.created_at or utc_now(),
            "ttl_seconds": self.ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ResourceIntent":
        return cls(**data)


@dataclass(frozen=True)
class IntentLease:
    lease_id: str
    intent: ResourceIntent
    issued_at: float
    expires_at: float
    status: str = "ACTIVE"
    grant_sequence: int = 0

    def __post_init__(self) -> None:
        _id(self.lease_id, "lease_id")
        if not isinstance(self.issued_at, (int, float)) or not isinstance(self.expires_at, (int, float)) or self.expires_at <= self.issued_at:
            raise ResourceArbitrationError("lease timestamps are invalid")
        if self.status not in {"ACTIVE", "RELEASED", "EXPIRED"}:
            raise ResourceArbitrationError(f"unknown lease status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "intent": self.intent.to_dict(),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "status": self.status,
            "grant_sequence": self.grant_sequence,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IntentLease":
        return cls(lease_id=data["lease_id"], intent=ResourceIntent.from_dict(data["intent"]), issued_at=data["issued_at"], expires_at=data["expires_at"], status=data["status"], grant_sequence=data.get("grant_sequence", 0))


class ResourceArbiter:
    """Locked, durable, atomic multi-resource intent arbiter."""

    def __init__(self, path: str | Path, *, clock: Any = None) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.clock = clock or time.time

    def _read(self) -> tuple[list[IntentLease], list[dict[str, Any]], int]:
        if not self.path.exists():
            return [], [], 0
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != RESOURCE_SCHEMA:
                raise ResourceCorruptionError("resource arbiter schema mismatch")
            leases = [IntentLease.from_dict(item) for item in data.get("leases", [])]
            waiters = [dict(item) for item in data.get("waiters", [])]
            sequence = data.get("next_grant_sequence", 0)
            if not isinstance(sequence, int) or sequence < 0:
                raise ResourceCorruptionError("resource grant sequence is invalid")
            return leases, waiters, sequence
        except (OSError, json.JSONDecodeError, TypeError, KeyError, ResourceArbitrationError) as exc:
            if isinstance(exc, ResourceCorruptionError):
                raise
            raise ResourceCorruptionError("resource arbiter state is malformed") from exc

    def _write(self, leases: Sequence[IntentLease], waiters: Sequence[Mapping[str, Any]], sequence: int) -> None:
        _atomic_json(self.path, {"schema": RESOURCE_SCHEMA, "leases": [item.to_dict() for item in leases], "waiters": [dict(item) for item in waiters], "next_grant_sequence": sequence})

    @staticmethod
    def _expire(leases: Sequence[IntentLease], now: float) -> list[IntentLease]:
        return [IntentLease(**{**lease.to_dict(), "intent": lease.intent, "status": "EXPIRED"}) if lease.status == "ACTIVE" and lease.expires_at <= now else lease for lease in leases]

    def _record_waiter(self, waiters: list[dict[str, Any]], intent: ResourceIntent, now: float, reason: str) -> None:
        if any(item.get("intent_id") == intent.intent_id for item in waiters):
            return
        waiters.append({"intent_id": intent.intent_id, "run_id": intent.run_id, "resource": intent.resource, "intent_type": intent.intent_type, "priority": intent.priority, "created_at": intent.created_at or utc_now(), "ttl_seconds": intent.ttl_seconds, "wait_started_at": now, "reason": reason})

    def acquire_many(self, intents: Sequence[ResourceIntent], *, now: float | None = None) -> tuple[IntentLease, ...]:
        requested = tuple(intents)
        if not requested:
            raise ResourceArbitrationError("acquire_many requires at least one intent")
        if any(not isinstance(intent, ResourceIntent) for intent in requested):
            raise ResourceArbitrationError("acquire_many accepts ResourceIntent values only")
        keys = [intent.canonical_key for intent in requested]
        if keys != sorted(keys):
            raise DeadlockPreventionError("multi-resource acquisition must use canonical resource ordering")
        if len({intent.intent_id for intent in requested}) != len(requested):
            raise ResourceArbitrationError("intent ids must be unique within an acquisition")
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            leases, waiters, sequence = self._read()
            leases = self._expire(leases, current)
            active = [lease for lease in leases if lease.status == "ACTIVE"]
            blockers: list[dict[str, Any]] = []
            for intent in requested:
                for lease in active:
                    if lease.intent.run_id == intent.run_id and lease.intent.intent_id == intent.intent_id:
                        blockers.append({"lease_id": lease.lease_id, "intent_id": lease.intent.intent_id, "intent_type": lease.intent.intent_type, "reason": "DUPLICATE_ACTIVE_INTENT"})
                    elif intents_conflict(intent, lease.intent):
                        blockers.append({"lease_id": lease.lease_id, "intent_id": lease.intent.intent_id, "run_id": lease.intent.run_id, "resource": lease.intent.resource, "intent_type": lease.intent.intent_type, "reason": "ACTIVE_OVERLAP"})
                for other in requested:
                    if other is not intent and intents_conflict(intent, other):
                        blockers.append({"intent_id": other.intent_id, "run_id": other.run_id, "resource": other.resource, "reason": "ATOMIC_BATCH_OVERLAP"})
                for waiter in waiters:
                    if waiter.get("intent_id") == intent.intent_id:
                        continue
                    waiting_intent = ResourceIntent(
                        intent_id=waiter["intent_id"],
                        run_id=waiter["run_id"],
                        resource=waiter["resource"],
                        intent_type=waiter["intent_type"],
                        priority=int(waiter.get("priority", 0)),
                        created_at=waiter.get("created_at") or utc_now(),
                        ttl_seconds=float(waiter.get("ttl_seconds", 60.0)),
                    ) if "ttl_seconds" in waiter else None
                    if waiting_intent and intents_conflict(intent, waiting_intent) and waiting_intent.priority >= intent.priority:
                        blockers.append({"intent_id": waiting_intent.intent_id, "run_id": waiting_intent.run_id, "resource": waiting_intent.resource, "reason": "STARVATION_GUARD"})
            if blockers:
                reason = "UNKNOWN_SIDE_EFFECT_SERIALIZATION" if any(item.get("intent_type") in {"UNKNOWN_SIDE_EFFECT", "EXTERNAL_SIDE_EFFECT"} for item in blockers) or any(intent.intent_type in {"UNKNOWN_SIDE_EFFECT", "EXTERNAL_SIDE_EFFECT"} for intent in requested) else "RESOURCE_CONFLICT"
                for intent in requested:
                    self._record_waiter(waiters, intent, current, reason)
                self._write(leases, waiters, sequence)
                raise ResourceConflict("resource intent acquisition was denied atomically", blockers=blockers, reason=reason)
            new_leases: list[IntentLease] = []
            for intent in requested:
                sequence += 1
                lease = IntentLease(
                    lease_id=f"resource-lease-{intent.run_id}-{intent.intent_id}-{sequence}",
                    intent=intent,
                    issued_at=current,
                    expires_at=current + float(intent.ttl_seconds),
                    grant_sequence=sequence,
                )
                new_leases.append(lease)
            granted_ids = {intent.intent_id for intent in requested}
            waiters = [item for item in waiters if item.get("intent_id") not in granted_ids]
            leases.extend(new_leases)
            self._write(leases, waiters, sequence)
            return tuple(new_leases)

    def acquire(self, intent: ResourceIntent, *, now: float | None = None) -> IntentLease:
        return self.acquire_many((intent,), now=now)[0]

    def release(self, lease_id: str) -> IntentLease:
        _id(lease_id, "lease_id")
        with FileLock(self.lock_path):
            leases, waiters, sequence = self._read()
            found: IntentLease | None = None
            updated: list[IntentLease] = []
            for lease in leases:
                if lease.lease_id == lease_id:
                    found = IntentLease(**{**lease.to_dict(), "intent": lease.intent, "status": "RELEASED"})
                    lease = found
                updated.append(lease)
            if found is None:
                raise ResourceArbitrationError("lease does not exist")
            self._write(updated, waiters, sequence)
            return found

    def reap_expired(self, *, now: float | None = None) -> list[IntentLease]:
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            leases, waiters, sequence = self._read()
            updated = self._expire(leases, current)
            expired = [lease for before, lease in zip(leases, updated) if before.status == "ACTIVE" and lease.status == "EXPIRED"]
            self._write(updated, waiters, sequence)
            return expired

    def active(self, *, now: float | None = None) -> list[IntentLease]:
        self.reap_expired(now=now)
        with FileLock(self.lock_path):
            leases, _, _ = self._read()
        return [lease for lease in leases if lease.status == "ACTIVE"]

    def waiting(self) -> list[dict[str, Any]]:
        with FileLock(self.lock_path):
            _, waiters, _ = self._read()
        return sorted(waiters, key=lambda item: (-int(item.get("priority", 0)), float(item.get("wait_started_at", 0)), str(item.get("intent_id", ""))))

    def audit(self) -> dict[str, Any]:
        leases, waiters, sequence = self._read()
        return {
            "status": "PASS",
            "schema": RESOURCE_SCHEMA,
            "lease_count": len(leases),
            "active_count": sum(lease.status == "ACTIVE" for lease in leases),
            "waiting_count": len(waiters),
            "next_grant_sequence": sequence,
            "unknown_side_effect_policy": "NO_OVERLAP_NO_AUTOMATIC_FAILOVER",
        }


__all__ = [
    "DeadlockPreventionError",
    "EXCLUSIVE_INTENTS",
    "IntentLease",
    "INTENT_TYPES",
    "ResourceArbiter",
    "ResourceArbitrationError",
    "ResourceConflict",
    "ResourceCorruptionError",
    "ResourceIntent",
    "intents_conflict",
    "resources_overlap",
]
