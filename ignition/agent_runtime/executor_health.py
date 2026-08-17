"""Durable executor capability and health leases for Control Plane R2.

The store records bounded observations made by an adapter or offline probe. A
lease is a routing input with an expiry, not proof that an executor completed
work and not a permission grant wider than its declared ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import time
from typing import Any, Iterable, Mapping

from agent_kernel.contracts import _id, sha256_json

from .control import FileLock, _atomic_json


HEALTH_LEASE_SCHEMA = "os-control-plane-executor-health-lease-r1"
HEALTH_STATES = frozenset({"HEALTHY", "DEGRADED", "STALE", "UNAVAILABLE", "UNSAFE_TO_PROBE", "UNKNOWN"})
PROBE_KINDS = frozenset({"DECLARATIVE", "READ_ONLY", "OFFLINE_FIXTURE", "ADAPTER_PROBE"})
HEALTH_RANK = {"HEALTHY": 0, "DEGRADED": 1, "STALE": 2, "UNKNOWN": 3, "UNSAFE_TO_PROBE": 4, "UNAVAILABLE": 5}
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "thoughts", "reasoning", "api_key", "token", "cookie", "authorization", "secret"})


class ExecutorHealthError(RuntimeError):
    """An executor observation or durable health lease is invalid."""


class ExecutorLeaseUnavailable(ExecutorHealthError):
    """A lease cannot satisfy a bounded routing request."""


def _public_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
        raise ExecutorHealthError(f"{field} must be a non-empty public value")
    return value


def _public_tuple(values: Iterable[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise ExecutorHealthError(f"{field} must be a string collection")
    result = tuple(sorted({_public_text(item, f"{field}[]") for item in values}))
    return result


@dataclass(frozen=True)
class ExecutorCapabilityLease:
    executor_id: str
    family: str
    adapter_version: str
    observed_version: str
    capability_tokens: tuple[str, ...]
    permission_ceiling: tuple[str, ...]
    workspace_modes: tuple[str, ...]
    supports_progress: bool
    supports_cancel: bool
    supports_resume: bool
    supports_handoff: bool
    max_concurrency: int
    status: str
    observed_at: float
    expires_at: float
    probe_kind: str
    failure_streak: int = 0
    cooldown_until: float = 0.0
    privacy_class: str = "LOCAL_PUBLIC_FIXTURE"
    evidence_refs: tuple[str, ...] = ()
    health_reason: str = "observation recorded"
    lease_digest: str | None = None

    def __post_init__(self) -> None:
        _id(self.executor_id, "executor_id")
        _public_text(self.family, "family")
        _public_text(self.adapter_version, "adapter_version")
        _public_text(self.observed_version, "observed_version")
        object.__setattr__(self, "capability_tokens", _public_tuple(self.capability_tokens, "capability_tokens"))
        object.__setattr__(self, "permission_ceiling", _public_tuple(self.permission_ceiling, "permission_ceiling"))
        object.__setattr__(self, "workspace_modes", _public_tuple(self.workspace_modes, "workspace_modes"))
        object.__setattr__(self, "evidence_refs", _public_tuple(self.evidence_refs, "evidence_refs"))
        if not all(isinstance(item, bool) for item in (self.supports_progress, self.supports_cancel, self.supports_resume, self.supports_handoff)):
            raise ExecutorHealthError("support flags must be boolean")
        if not isinstance(self.max_concurrency, int) or isinstance(self.max_concurrency, bool) or self.max_concurrency <= 0:
            raise ExecutorHealthError("max_concurrency must be positive")
        if self.status not in HEALTH_STATES:
            raise ExecutorHealthError(f"unknown health status: {self.status}")
        if self.probe_kind not in PROBE_KINDS:
            raise ExecutorHealthError(f"unknown probe kind: {self.probe_kind}")
        if not isinstance(self.observed_at, (int, float)) or not isinstance(self.expires_at, (int, float)) or self.expires_at <= self.observed_at:
            raise ExecutorHealthError("health lease timestamps are invalid")
        if not isinstance(self.failure_streak, int) or isinstance(self.failure_streak, bool) or self.failure_streak < 0:
            raise ExecutorHealthError("failure_streak must be non-negative")
        if not isinstance(self.cooldown_until, (int, float)) or self.cooldown_until < 0:
            raise ExecutorHealthError("cooldown_until must be non-negative")
        _public_text(self.privacy_class, "privacy_class")
        _public_text(self.health_reason, "health_reason")
        expected = self._digest_for(self._body())
        if self.lease_digest is not None and self.lease_digest != expected:
            raise ExecutorHealthError("executor lease digest mismatch")
        object.__setattr__(self, "lease_digest", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id, "family": self.family, "adapter_version": self.adapter_version,
            "observed_version": self.observed_version, "capability_tokens": list(self.capability_tokens),
            "permission_ceiling": list(self.permission_ceiling), "workspace_modes": list(self.workspace_modes),
            "supports_progress": self.supports_progress, "supports_cancel": self.supports_cancel,
            "supports_resume": self.supports_resume, "supports_handoff": self.supports_handoff,
            "max_concurrency": self.max_concurrency, "status": self.status, "observed_at": self.observed_at,
            "expires_at": self.expires_at, "probe_kind": self.probe_kind, "failure_streak": self.failure_streak,
            "cooldown_until": self.cooldown_until, "privacy_class": self.privacy_class,
            "evidence_refs": list(self.evidence_refs), "health_reason": self.health_reason,
        }

    @staticmethod
    def _digest_for(value: Mapping[str, Any]) -> str:
        return sha256_json(value)

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "lease_digest": self.lease_digest}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutorCapabilityLease":
        required = {"executor_id", "family", "adapter_version", "observed_version", "capability_tokens", "permission_ceiling", "workspace_modes", "supports_progress", "supports_cancel", "supports_resume", "supports_handoff", "max_concurrency", "status", "observed_at", "expires_at", "probe_kind", "failure_streak", "cooldown_until", "privacy_class", "evidence_refs", "health_reason", "lease_digest"}
        if not isinstance(data, Mapping) or set(data) != required:
            raise ExecutorHealthError("executor lease keys mismatch")
        return cls(**dict(data))

    def effective_status(self, now: float) -> str:
        if now >= self.expires_at and self.status not in {"UNAVAILABLE", "UNSAFE_TO_PROBE"}:
            return "STALE"
        if self.cooldown_until > now and self.status in {"HEALTHY", "DEGRADED"}:
            return "UNSAFE_TO_PROBE"
        return self.status

    def usable(
        self,
        *,
        now: float,
        required_capabilities: Iterable[str] = (),
        required_permissions: Iterable[str] = (),
        workspace_mode: str | None = None,
        required_concurrency: int = 1,
        allow_degraded: bool = False,
    ) -> bool:
        status = self.effective_status(now)
        if status != "HEALTHY" and not (allow_degraded and status == "DEGRADED"):
            return False
        if not set(required_capabilities) <= set(self.capability_tokens):
            return False
        if not set(required_permissions) <= set(self.permission_ceiling):
            return False
        if workspace_mode is not None and workspace_mode not in self.workspace_modes:
            return False
        return isinstance(required_concurrency, int) and 0 < required_concurrency <= self.max_concurrency


class ExecutorHealthStore:
    """Atomic, locked health lease index with explicit stale/cooldown states."""

    def __init__(self, path: str | Path, *, clock: Any = None) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.clock = clock or time.time

    def _read(self) -> list[ExecutorCapabilityLease]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != HEALTH_LEASE_SCHEMA or not isinstance(data.get("leases"), list):
                raise ExecutorHealthError("health lease store schema mismatch")
            leases = [ExecutorCapabilityLease.from_dict(item) for item in data["leases"]]
            if len({item.executor_id for item in leases}) != len(leases):
                raise ExecutorHealthError("health lease store has duplicate executor ids")
            return leases
        except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
            raise ExecutorHealthError("health lease store is malformed") from exc

    def _write(self, leases: Iterable[ExecutorCapabilityLease]) -> None:
        _atomic_json(self.path, {"schema": HEALTH_LEASE_SCHEMA, "leases": [item.to_dict() for item in sorted(leases, key=lambda item: item.executor_id)]})

    def observe(self, lease: ExecutorCapabilityLease) -> ExecutorCapabilityLease:
        if not isinstance(lease, ExecutorCapabilityLease):
            raise ExecutorHealthError("observe accepts ExecutorCapabilityLease only")
        with FileLock(self.lock_path):
            leases = [item for item in self._read() if item.executor_id != lease.executor_id]
            leases.append(lease)
            self._write(leases)
        return lease

    def get(self, executor_id: str, *, now: float | None = None) -> ExecutorCapabilityLease:
        _id(executor_id, "executor_id")
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            leases = self._read()
            found = next((item for item in leases if item.executor_id == executor_id), None)
            if found is None:
                raise ExecutorLeaseUnavailable(f"no health lease for {executor_id}")
            effective = found.effective_status(current)
            if effective == "STALE" and effective != found.status:
                found = replace(found, status=effective, health_reason="lease expired or cooldown is active", lease_digest=None)
                leases = [found if item.executor_id == executor_id else item for item in leases]
                self._write(leases)
            return found

    def record_failure(self, executor_id: str, reason: str, *, cooldown_seconds: float = 30.0) -> ExecutorCapabilityLease:
        _public_text(reason, "reason")
        if not isinstance(cooldown_seconds, (int, float)) or cooldown_seconds <= 0:
            raise ExecutorHealthError("cooldown_seconds must be positive")
        now = float(self.clock())
        with FileLock(self.lock_path):
            leases = self._read()
            current = next((item for item in leases if item.executor_id == executor_id), None)
            if current is None:
                raise ExecutorLeaseUnavailable(f"no health lease for {executor_id}")
            streak = current.failure_streak + 1
            status = "UNSAFE_TO_PROBE" if streak >= 3 else "DEGRADED"
            updated = replace(current, status=status, observed_at=now, expires_at=max(current.expires_at, now + cooldown_seconds), failure_streak=streak, cooldown_until=now + cooldown_seconds, health_reason=reason, lease_digest=None)
            self._write(updated if item.executor_id == executor_id else item for item in leases)
            return updated

    def usable(self, executor_id: str, **requirements: Any) -> bool:
        requested_now = requirements.pop("now", None)
        current = float(self.clock() if requested_now is None else requested_now)
        try:
            lease = self.get(executor_id, now=current)
        except ExecutorLeaseUnavailable:
            return False
        return lease.usable(now=current, **requirements)

    def route_candidates(self, *, now: float | None = None, required_capabilities: Iterable[str] = (), required_permissions: Iterable[str] = (), workspace_mode: str | None = None, required_concurrency: int = 1, allow_degraded: bool = False) -> tuple[ExecutorCapabilityLease, ...]:
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            leases = self._read()
        candidates = [item for item in leases if item.usable(now=current, required_capabilities=required_capabilities, required_permissions=required_permissions, workspace_mode=workspace_mode, required_concurrency=required_concurrency, allow_degraded=allow_degraded)]
        return tuple(sorted(candidates, key=lambda item: (HEALTH_RANK[item.effective_status(current)], item.failure_streak, item.max_concurrency, item.executor_id)))

    def reap_expired(self, *, now: float | None = None) -> tuple[ExecutorCapabilityLease, ...]:
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            leases = self._read()
            updated = [replace(item, status="STALE", health_reason="lease expired or cooldown is active", lease_digest=None) if item.effective_status(current) == "STALE" and item.status != "STALE" else item for item in leases]
            self._write(updated)
        return tuple(item for item in updated if item.status == "STALE")

    def audit(self, *, now: float | None = None) -> dict[str, Any]:
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            leases = self._read()
        counts = {status: 0 for status in sorted(HEALTH_STATES)}
        for item in leases:
            counts[item.effective_status(current)] += 1
        return {"status": "PASS", "schema": HEALTH_LEASE_SCHEMA, "lease_count": len(leases), "effective_status_counts": counts, "claim_ceiling": "Observed executor capability/health routing only; no execution, truth, permission or Owner authority."}


__all__ = ["ExecutorCapabilityLease", "ExecutorHealthError", "ExecutorHealthStore", "ExecutorLeaseUnavailable", "HEALTH_LEASE_SCHEMA", "HEALTH_STATES"]
