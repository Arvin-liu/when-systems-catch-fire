"""Fail-closed executor admission and conformance-epoch routing gates.

The admission record is an OS-owned observation.  It is not a vendor
invocation, a completion claim, or a permission grant beyond the declared
intersection.  A record leaves the routable pool when its observed version,
conformance epoch, health lease, or capability revocation is no longer valid.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import re
import time
from typing import Any, Iterable, Mapping

from agent_kernel.contracts import sha256_json

from .control import FileLock, _atomic_json


EXECUTOR_ADMISSION_SCHEMA = "ignition-durability-executor-admission-r1"
ADMISSION_STATUSES = frozenset({"ADMITTED", "DRAINING", "REVOKED", "EXPIRED", "REJECTED"})
HEALTH_STATUSES = frozenset({"HEALTHY", "DEGRADED", "STALE", "UNAVAILABLE", "UNKNOWN"})
PRIVACY_BOUNDARIES = frozenset({"LOCAL_FIXTURE_ONLY", "LOCAL_INTERNAL", "PUBLIC_BOUNDED"})
PERMISSION_CEILING = "DECLARED_CAPABILITIES_INTERSECT_OS_POLICY"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_FORBIDDEN = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "thoughts", "reasoning", "api_key", "token", "cookie", "authorization", "secret"})


class ExecutorAdmissionError(ValueError):
    """Raised when an executor admission or route decision is unsafe."""


class ExecutorRouteDenied(ExecutorAdmissionError):
    """Raised when a record is not currently eligible for routing."""


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or ".." in value:
        raise ExecutorAdmissionError(f"{field} is not a canonical identifier")
    return value


def _public(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in _FORBIDDEN):
        raise ExecutorAdmissionError(f"{field} must be a non-empty public value")
    return value


def _strings(values: Iterable[str], field: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise ExecutorAdmissionError(f"{field} must be a string collection")
    result = tuple(sorted({_public(item, f"{field}[]") for item in values}))
    if nonempty and not result:
        raise ExecutorAdmissionError(f"{field} must not be empty")
    return result


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ExecutorAdmissionError(f"{field} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class ExecutorAdmission:
    executor_id: str
    adapter_family: str
    observed_version: str
    conformance_epoch: int
    declared_capabilities: tuple[str, ...]
    permission_ceiling: tuple[str, ...]
    workspace_support: tuple[str, ...]
    handoff_semantics: str
    recovery_semantics: str
    health_lease_id: str
    health_status: str
    observed_at: float
    health_expires_at: float
    privacy_boundary: str
    conformance_receipt_ref: str
    capability_grant_ids: tuple[str, ...] = ()
    status: str = "ADMITTED"
    status_reason: str = "conformance and health lease admitted"
    admission_digest: str | None = None

    def __post_init__(self) -> None:
        _id(self.executor_id, "executor_id")
        for field in ("adapter_family", "observed_version", "handoff_semantics", "recovery_semantics", "health_lease_id", "conformance_receipt_ref", "status_reason"):
            _public(getattr(self, field), field)
        if not isinstance(self.conformance_epoch, int) or isinstance(self.conformance_epoch, bool) or self.conformance_epoch < 1:
            raise ExecutorAdmissionError("conformance_epoch must be a positive integer")
        object.__setattr__(self, "declared_capabilities", _strings(self.declared_capabilities, "declared_capabilities", nonempty=True))
        object.__setattr__(self, "permission_ceiling", _strings(self.permission_ceiling, "permission_ceiling", nonempty=True))
        object.__setattr__(self, "workspace_support", _strings(self.workspace_support, "workspace_support", nonempty=True))
        object.__setattr__(self, "capability_grant_ids", tuple(sorted({_id(item, "capability_grant_ids[]") for item in self.capability_grant_ids})))
        if self.health_status not in HEALTH_STATUSES:
            raise ExecutorAdmissionError(f"unknown health status: {self.health_status}")
        if not isinstance(self.observed_at, (int, float)) or not isinstance(self.health_expires_at, (int, float)) or self.health_expires_at <= self.observed_at:
            raise ExecutorAdmissionError("health lease timestamps are invalid")
        if self.privacy_boundary not in PRIVACY_BOUNDARIES:
            raise ExecutorAdmissionError(f"unknown privacy boundary: {self.privacy_boundary}")
        if self.status not in ADMISSION_STATUSES:
            raise ExecutorAdmissionError(f"unknown admission status: {self.status}")
        if self.status == "ADMITTED" and self.health_status != "HEALTHY":
            raise ExecutorAdmissionError("an admitted executor must have a healthy lease")
        body = self._body()
        expected = sha256_json(body)
        if self.admission_digest is not None and self.admission_digest != expected:
            raise ExecutorAdmissionError("admission digest mismatch")
        object.__setattr__(self, "admission_digest", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id,
            "adapter_family": self.adapter_family,
            "observed_version": self.observed_version,
            "conformance_epoch": self.conformance_epoch,
            "declared_capabilities": list(self.declared_capabilities),
            "permission_ceiling": list(self.permission_ceiling),
            "workspace_support": list(self.workspace_support),
            "handoff_semantics": self.handoff_semantics,
            "recovery_semantics": self.recovery_semantics,
            "health_lease_id": self.health_lease_id,
            "health_status": self.health_status,
            "observed_at": self.observed_at,
            "health_expires_at": self.health_expires_at,
            "privacy_boundary": self.privacy_boundary,
            "conformance_receipt_ref": self.conformance_receipt_ref,
            "capability_grant_ids": list(self.capability_grant_ids),
            "status": self.status,
            "status_reason": self.status_reason,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "admission_digest": self.admission_digest}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutorAdmission":
        required = {
            "executor_id", "adapter_family", "observed_version", "conformance_epoch", "declared_capabilities",
            "permission_ceiling", "workspace_support", "handoff_semantics", "recovery_semantics", "health_lease_id",
            "health_status", "observed_at", "health_expires_at", "privacy_boundary", "conformance_receipt_ref",
            "capability_grant_ids", "status", "status_reason", "admission_digest",
        }
        if not isinstance(data, Mapping) or set(data) != required:
            raise ExecutorAdmissionError("executor admission keys mismatch")
        return cls(**dict(data))


class ExecutorAdmissionStore:
    """Atomic admission index consulted immediately before routing."""

    def __init__(self, path: str | Path, *, clock: Any = None) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.clock = clock or time.time

    def _read(self) -> list[ExecutorAdmission]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != EXECUTOR_ADMISSION_SCHEMA or not isinstance(data.get("records"), list):
                raise ExecutorAdmissionError("admission store schema mismatch")
            records = [ExecutorAdmission.from_dict(item) for item in data["records"]]
            if len({item.executor_id for item in records}) != len(records):
                raise ExecutorAdmissionError("admission store has duplicate executor ids")
            return records
        except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
            raise ExecutorAdmissionError("admission store is malformed") from exc

    def _write(self, records: Iterable[ExecutorAdmission]) -> None:
        _atomic_json(self.path, {"schema": EXECUTOR_ADMISSION_SCHEMA, "records": [item.to_dict() for item in sorted(records, key=lambda item: item.executor_id)]})

    def admit(self, record: ExecutorAdmission, *, expected_conformance_epoch: int, now: float | None = None) -> ExecutorAdmission:
        if not isinstance(record, ExecutorAdmission):
            raise ExecutorAdmissionError("admit accepts ExecutorAdmission only")
        current = float(self.clock() if now is None else now)
        if record.conformance_epoch != expected_conformance_epoch:
            raise ExecutorAdmissionError("conformance epoch is not current")
        if record.health_status != "HEALTHY" or current >= record.health_expires_at:
            raise ExecutorAdmissionError("admission requires a live healthy health lease")
        admitted = replace(record, status="ADMITTED", status_reason="conformance epoch and health lease verified", admission_digest=None)
        with FileLock(self.lock_path):
            records = self._read()
            existing = next((item for item in records if item.executor_id == record.executor_id), None)
            if existing is not None and existing.status == "ADMITTED" and (existing.observed_version != record.observed_version or existing.conformance_epoch != record.conformance_epoch):
                raise ExecutorAdmissionError("version or epoch drift requires explicit removal before re-admission")
            self._write([item for item in records if item.executor_id != record.executor_id] + [admitted])
        return admitted

    def get(self, executor_id: str) -> ExecutorAdmission:
        _id(executor_id, "executor_id")
        with FileLock(self.lock_path):
            found = next((item for item in self._read() if item.executor_id == executor_id), None)
        if found is None:
            raise ExecutorRouteDenied(f"executor {executor_id} has no admission")
        return found

    def _transition_locked(self, records: list[ExecutorAdmission], executor_id: str, status: str, reason: str) -> tuple[list[ExecutorAdmission], ExecutorAdmission]:
        current = next((item for item in records if item.executor_id == executor_id), None)
        if current is None:
            raise ExecutorRouteDenied(f"executor {executor_id} has no admission")
        updated = replace(current, status=status, status_reason=reason, admission_digest=None)
        return [updated if item.executor_id == executor_id else item for item in records], updated

    def mark_version_drift(self, executor_id: str, observed_version: str) -> ExecutorAdmission:
        _id(executor_id, "executor_id")
        _public(observed_version, "observed_version")
        with FileLock(self.lock_path):
            records, updated = self._transition_locked(self._read(), executor_id, "REJECTED", f"observed version drifted to {observed_version}; no automatic vendor rerun")
            self._write(records)
        return updated

    def revoke(self, executor_id: str, *, reason: str = "capability revoked") -> ExecutorAdmission:
        _id(executor_id, "executor_id")
        _public(reason, "reason")
        with FileLock(self.lock_path):
            records, updated = self._transition_locked(self._read(), executor_id, "REVOKED", reason)
            self._write(records)
        return updated

    def refresh(self, *, now: float | None = None) -> tuple[ExecutorAdmission, ...]:
        current = float(self.clock() if now is None else now)
        with FileLock(self.lock_path):
            records = self._read()
            updated: list[ExecutorAdmission] = []
            for item in records:
                if item.status == "ADMITTED" and current >= item.health_expires_at:
                    item = replace(item, status="EXPIRED", status_reason="health lease expired; removed from routable pool", admission_digest=None)
                elif item.status == "ADMITTED" and item.health_status != "HEALTHY":
                    item = replace(item, status="DRAINING", status_reason="health lease is not healthy; drain without permission expansion", admission_digest=None)
                updated.append(item)
            self._write(updated)
        return tuple(updated)

    def route(
        self,
        executor_id: str,
        *,
        required_capabilities: Iterable[str] = (),
        workspace: str | None = None,
        observed_version: str | None = None,
        conformance_epoch: int | None = None,
        revocation_store: Any = None,
        now: float | None = None,
    ) -> ExecutorAdmission:
        _id(executor_id, "executor_id")
        current = float(self.clock() if now is None else now)
        requested = set(_strings(required_capabilities, "required_capabilities"))
        with FileLock(self.lock_path):
            records = self._read()
            record = next((item for item in records if item.executor_id == executor_id), None)
            if record is None:
                raise ExecutorRouteDenied(f"executor {executor_id} has no admission")
            if record.status != "ADMITTED":
                raise ExecutorRouteDenied(f"executor {executor_id} is {record.status}, not routable")
            if current >= record.health_expires_at:
                records, _ = self._transition_locked(records, executor_id, "EXPIRED", "health lease expired; removed from routable pool")
                self._write(records)
                raise ExecutorRouteDenied("health lease expired")
            if record.health_status != "HEALTHY":
                records, _ = self._transition_locked(records, executor_id, "DRAINING", "health degraded; drain without permission expansion")
                self._write(records)
                raise ExecutorRouteDenied("health lease is not healthy")
            if observed_version is not None and observed_version != record.observed_version:
                records, _ = self._transition_locked(records, executor_id, "REJECTED", "observed version drift; no automatic vendor rerun")
                self._write(records)
                raise ExecutorRouteDenied("observed version drift")
            if conformance_epoch is not None and conformance_epoch != record.conformance_epoch:
                records, _ = self._transition_locked(records, executor_id, "REJECTED", "conformance epoch drift")
                self._write(records)
                raise ExecutorRouteDenied("conformance epoch drift")
            if not requested <= set(record.declared_capabilities):
                raise ExecutorRouteDenied("required capability is not declared")
            if workspace is not None and workspace not in record.workspace_support:
                raise ExecutorRouteDenied("workspace is outside the admission boundary")
            if revocation_store is not None and any(not revocation_store.is_admissible(grant_id, now=current) for grant_id in record.capability_grant_ids):
                records, _ = self._transition_locked(records, executor_id, "REVOKED", "capability grant revoked; removed from routable pool")
                self._write(records)
                raise ExecutorRouteDenied("capability grant revoked")
            return record

    def routable_ids(self, *, now: float | None = None) -> tuple[str, ...]:
        current = float(self.clock() if now is None else now)
        self.refresh(now=current)
        with FileLock(self.lock_path):
            records = self._read()
        return tuple(sorted(item.executor_id for item in records if item.status == "ADMITTED" and item.health_status == "HEALTHY" and current < item.health_expires_at))

    def audit(self, *, now: float | None = None) -> dict[str, Any]:
        current = float(self.clock() if now is None else now)
        self.refresh(now=current)
        with FileLock(self.lock_path):
            records = self._read()
        counts = {status: sum(item.status == status for item in records) for status in sorted(ADMISSION_STATUSES)}
        return {
            "status": "PASS",
            "schema": EXECUTOR_ADMISSION_SCHEMA,
            "record_count": len(records),
            "routable_ids": [item.executor_id for item in records if item.status == "ADMITTED"],
            "status_counts": counts,
            "claim_ceiling": "Offline admission, conformance and health routing observations only; no vendor invocation or completion authority.",
        }


__all__ = [
    "ADMISSION_STATUSES", "EXECUTOR_ADMISSION_SCHEMA", "ExecutorAdmission", "ExecutorAdmissionError",
    "ExecutorAdmissionStore", "ExecutorRouteDenied", "HEALTH_STATUSES", "PERMISSION_CEILING", "PRIVACY_BOUNDARIES",
]
