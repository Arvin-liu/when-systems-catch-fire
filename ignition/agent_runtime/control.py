"""Durable approval, lease and action-journal controls for Runtime R1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Callable, Mapping

from agent_kernel.contracts import KernelValidationError, _id, _string, _summary, sha256_json


class ControlConflict(RuntimeError):
    """Raised when durable control state cannot be safely reused."""


class LeaseConflict(ControlConflict):
    """An active action or lease already owns the requested slot."""


class IdempotencyConflict(ControlConflict):
    """The same idempotency key was presented with a different packet."""


class ApprovalConflict(ControlConflict):
    """An approval request cannot be changed from its current state."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.r1-", delete=False
        ) as handle:
            temp_name = handle.name
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass


class FileLock:
    """A process-level lock whose lock file is never removed."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._handle: Any = None

    def __enter__(self) -> "FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a+", encoding="utf-8")
        fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            self._handle.close()
            self._handle = None


@dataclass(frozen=True)
class ExecutionLease:
    lease_id: str
    run_id: str
    action_id: str
    idempotency_key: str
    packet_digest: str
    executor_class_id: str
    executor_instance_id: str
    issued_at: float
    expires_at: float
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        for value, field in (
            (self.lease_id, "lease_id"),
            (self.run_id, "run_id"),
            (self.action_id, "action_id"),
            (self.idempotency_key, "idempotency_key"),
            (self.executor_class_id, "executor_class_id"),
            (self.executor_instance_id, "executor_instance_id"),
        ):
            _id(value, field)
        if len(self.packet_digest) != 64 or any(char not in "0123456789abcdef" for char in self.packet_digest):
            raise KernelValidationError("packet_digest must be a lowercase SHA-256 digest")
        if not isinstance(self.issued_at, (int, float)) or not isinstance(self.expires_at, (int, float)):
            raise KernelValidationError("lease timestamps must be numeric")
        if self.expires_at <= self.issued_at:
            raise KernelValidationError("lease expires_at must be after issued_at")
        if self.status not in {"ACTIVE", "COMPLETED", "RELEASED", "EXPIRED"}:
            raise KernelValidationError(f"unknown lease status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "run_id": self.run_id,
            "action_id": self.action_id,
            "idempotency_key": self.idempotency_key,
            "packet_digest": self.packet_digest,
            "executor_class_id": self.executor_class_id,
            "executor_instance_id": self.executor_instance_id,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionLease":
        required = {
            "lease_id", "run_id", "action_id", "idempotency_key", "packet_digest",
            "executor_class_id", "executor_instance_id", "issued_at", "expires_at", "status",
        }
        if set(data) != required:
            raise KernelValidationError("ExecutionLease keys mismatch")
        return cls(**data)


class LeaseStore:
    """A locked, durable lease and idempotency index."""

    def __init__(self, path: str | Path, *, ttl_seconds: float = 60.0, clock: Callable[[], float] | None = None) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.ttl_seconds = float(ttl_seconds)
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.clock = clock or time.time

    def _read(self) -> list[ExecutionLease]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("leases"), list):
            raise ControlConflict("lease store is malformed")
        return [ExecutionLease.from_dict(item) for item in data["leases"]]

    def _write(self, leases: list[ExecutionLease]) -> None:
        _atomic_json(self.path, {"schema": "execution-lease-r1", "leases": [item.to_dict() for item in leases]})

    def acquire(
        self,
        *,
        run_id: str,
        action_id: str,
        idempotency_key: str,
        packet_digest: str,
        executor_class_id: str,
        executor_instance_id: str,
    ) -> ExecutionLease:
        now = float(self.clock())
        with FileLock(self.lock_path):
            leases = self._read()
            normalized: list[ExecutionLease] = []
            for lease in leases:
                if lease.status == "ACTIVE" and lease.expires_at <= now:
                    lease = ExecutionLease(**{**lease.to_dict(), "status": "EXPIRED"})
                normalized.append(lease)
            leases = normalized
            for lease in leases:
                if lease.idempotency_key == idempotency_key:
                    if lease.packet_digest != packet_digest:
                        raise IdempotencyConflict("idempotency key is bound to a different packet digest")
                    if lease.status == "ACTIVE":
                        raise LeaseConflict("idempotency key has an active lease")
                    self._write(leases)
                    return lease
                if lease.status == "ACTIVE" and (lease.action_id == action_id or lease.run_id == run_id and lease.action_id == action_id):
                    raise LeaseConflict("action already has an active lease")
            lease = ExecutionLease(
                lease_id=f"lease-{action_id}-{int(now * 1000)}",
                run_id=run_id,
                action_id=action_id,
                idempotency_key=idempotency_key,
                packet_digest=packet_digest,
                executor_class_id=executor_class_id,
                executor_instance_id=executor_instance_id,
                issued_at=now,
                expires_at=now + self.ttl_seconds,
            )
            leases.append(lease)
            self._write(leases)
            return lease

    def set_status(self, lease_id: str, status: str) -> ExecutionLease:
        _id(lease_id, "lease_id")
        if status not in {"COMPLETED", "RELEASED", "EXPIRED"}:
            raise ValueError("lease status update is invalid")
        with FileLock(self.lock_path):
            leases = self._read()
            found: ExecutionLease | None = None
            updated: list[ExecutionLease] = []
            for lease in leases:
                if lease.lease_id == lease_id:
                    found = lease = ExecutionLease(**{**lease.to_dict(), "status": status})
                updated.append(lease)
            if found is None:
                raise ControlConflict("lease does not exist")
            self._write(updated)
            return found

    def find(self, *, action_id: str, idempotency_key: str) -> ExecutionLease | None:
        with FileLock(self.lock_path):
            for lease in reversed(self._read()):
                if lease.action_id == action_id and lease.idempotency_key == idempotency_key:
                    return lease
        return None

    def reactivate(self, lease_id: str) -> ExecutionLease:
        """Re-open only an expired/released lease after preimage reconciliation."""

        _id(lease_id, "lease_id")
        now = float(self.clock())
        with FileLock(self.lock_path):
            leases = self._read()
            found: ExecutionLease | None = None
            updated: list[ExecutionLease] = []
            for lease in leases:
                if lease.lease_id == lease_id:
                    if lease.status == "COMPLETED":
                        found = lease
                    elif lease.status in {"EXPIRED", "RELEASED"}:
                        found = ExecutionLease(**{**lease.to_dict(), "issued_at": now, "expires_at": now + self.ttl_seconds, "status": "ACTIVE"})
                    else:
                        found = lease
                    lease = found
                updated.append(lease)
            if found is None:
                raise ControlConflict("lease does not exist")
            self._write(updated)
            return found

    def list(self) -> list[ExecutionLease]:
        with FileLock(self.lock_path):
            return self._read()


@dataclass(frozen=True)
class ApprovalRequestR1:
    request_id: str
    run_id: str
    action_id: str
    action_digest: str
    impact_summary: str
    risk_class: str
    requested_capabilities: tuple[str, ...]
    requested_reads: tuple[str, ...]
    requested_writes: tuple[str, ...]
    expires_at: float
    lease_id: str | None = None
    status: str = "PENDING"
    created_at: str = ""

    def __post_init__(self) -> None:
        for value, field in ((self.request_id, "request_id"), (self.run_id, "run_id"), (self.action_id, "action_id")):
            _id(value, field)
        if len(self.action_digest) != 64 or any(char not in "0123456789abcdef" for char in self.action_digest):
            raise KernelValidationError("action_digest must be a lowercase SHA-256 digest")
        _summary(self.impact_summary, "impact_summary")
        _string(self.risk_class, "risk_class")
        if not self.requested_capabilities:
            raise KernelValidationError("approval request must declare capabilities")
        if not isinstance(self.expires_at, (int, float)):
            raise KernelValidationError("approval expires_at must be numeric")
        if self.lease_id is not None:
            _id(self.lease_id, "lease_id")
        if self.status not in {"PENDING", "ALLOWED", "DENIED", "EXPIRED"}:
            raise KernelValidationError("unknown approval status")
        if self.created_at:
            _string(self.created_at, "created_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "run_id": self.run_id,
            "action_id": self.action_id,
            "action_digest": self.action_digest,
            "impact_summary": self.impact_summary,
            "risk_class": self.risk_class,
            "requested_capabilities": list(self.requested_capabilities),
            "requested_reads": list(self.requested_reads),
            "requested_writes": list(self.requested_writes),
            "expires_at": self.expires_at,
            "lease_id": self.lease_id,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ApprovalRequestR1":
        required = {"request_id", "run_id", "action_id", "action_digest", "impact_summary", "risk_class", "requested_capabilities", "requested_reads", "requested_writes", "expires_at", "lease_id", "status", "created_at"}
        if set(data) != required:
            raise KernelValidationError("ApprovalRequestR1 keys mismatch")
        return cls(
            **{**data, "requested_capabilities": tuple(data["requested_capabilities"]),
               "requested_reads": tuple(data["requested_reads"]), "requested_writes": tuple(data["requested_writes"])}
        )


@dataclass(frozen=True)
class ApprovalDecisionR1:
    decision_id: str
    request_id: str
    run_id: str
    action_digest: str
    decision: str
    authority_id: str
    authority_type: str
    decided_at: str
    reason_summary: str

    def __post_init__(self) -> None:
        for value, field in ((self.decision_id, "decision_id"), (self.request_id, "request_id"), (self.run_id, "run_id"), (self.authority_id, "authority_id")):
            _id(value, field)
        if len(self.action_digest) != 64 or any(char not in "0123456789abcdef" for char in self.action_digest):
            raise KernelValidationError("action_digest must be a lowercase SHA-256 digest")
        if self.decision not in {"ALLOW", "DENY"}:
            raise KernelValidationError("approval decision must be ALLOW or DENY")
        _string(self.authority_type, "authority_type")
        if self.authority_type.casefold() not in {"human", "operator", "synthetic_pilot", "cli"}:
            raise KernelValidationError("approval authority_type is not an accepted external authority")
        _string(self.decided_at, "decided_at")
        _summary(self.reason_summary, "reason_summary")

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "run_id": self.run_id,
            "action_digest": self.action_digest,
            "decision": self.decision,
            "authority_id": self.authority_id,
            "authority_type": self.authority_type,
            "decided_at": self.decided_at,
            "reason_summary": self.reason_summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ApprovalDecisionR1":
        required = {"decision_id", "request_id", "run_id", "action_digest", "decision", "authority_id", "authority_type", "decided_at", "reason_summary"}
        if set(data) != required:
            raise KernelValidationError("ApprovalDecisionR1 keys mismatch")
        return cls(**data)


class ApprovalStore:
    """Locked approval records; a decision never mutates the packet."""

    def __init__(self, path: str | Path, *, clock: Callable[[], float] | None = None) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.clock = clock or time.time

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"requests": [], "decisions": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("requests"), list) or not isinstance(data.get("decisions"), list):
            raise ControlConflict("approval store is malformed")
        return data

    def _write(self, data: dict[str, Any]) -> None:
        _atomic_json(self.path, {"schema": "approval-r1", "requests": data["requests"], "decisions": data["decisions"]})

    def create(self, request: ApprovalRequestR1) -> ApprovalRequestR1:
        with FileLock(self.lock_path):
            data = self._read()
            for item in data["requests"]:
                old = ApprovalRequestR1.from_dict(item)
                if old.request_id == request.request_id:
                    if old.to_dict() != request.to_dict():
                        raise ApprovalConflict("approval request id is already bound to a different request")
                    return old
            data["requests"].append(request.to_dict())
            self._write(data)
            return request

    def pending(self, *, run_id: str | None = None) -> list[ApprovalRequestR1]:
        with FileLock(self.lock_path):
            data = self._read()
            now = float(self.clock())
            result: list[ApprovalRequestR1] = []
            changed = False
            requests: list[dict[str, Any]] = []
            for item in data["requests"]:
                request = ApprovalRequestR1.from_dict(item)
                if request.status == "PENDING" and request.expires_at <= now:
                    request = ApprovalRequestR1(**{**request.to_dict(), "status": "EXPIRED"})
                    changed = True
                requests.append(request.to_dict())
                if request.status == "PENDING" and (run_id is None or request.run_id == run_id):
                    result.append(request)
            if changed:
                data["requests"] = requests
                self._write(data)
            return result

    def submit(self, decision: ApprovalDecisionR1) -> tuple[ApprovalRequestR1, ApprovalDecisionR1]:
        with FileLock(self.lock_path):
            data = self._read()
            target: ApprovalRequestR1 | None = None
            index = -1
            for position, item in enumerate(data["requests"]):
                request = ApprovalRequestR1.from_dict(item)
                if request.request_id == decision.request_id:
                    target, index = request, position
                    break
            if target is None:
                raise ApprovalConflict("approval request does not exist")
            if target.run_id != decision.run_id or target.action_digest != decision.action_digest:
                raise ApprovalConflict("approval decision lineage or digest mismatch")
            if target.status != "PENDING":
                raise ApprovalConflict("approval request is no longer pending")
            if target.expires_at <= float(self.clock()):
                expired = ApprovalRequestR1(**{**target.to_dict(), "status": "EXPIRED"})
                data["requests"][index] = expired.to_dict()
                self._write(data)
                raise ApprovalConflict("approval request has expired")
            status = "ALLOWED" if decision.decision == "ALLOW" else "DENIED"
            changed = ApprovalRequestR1(**{**target.to_dict(), "status": status})
            data["requests"][index] = changed.to_dict()
            data["decisions"] = [item for item in data["decisions"] if item.get("request_id") != decision.request_id]
            data["decisions"].append(decision.to_dict())
            self._write(data)
            return changed, decision

    def get(self, request_id: str) -> ApprovalRequestR1 | None:
        with FileLock(self.lock_path):
            data = self._read()
            changed = False
            requests: list[dict[str, Any]] = []
            now = float(self.clock())
            found: ApprovalRequestR1 | None = None
            for item in data["requests"]:
                request = ApprovalRequestR1.from_dict(item)
                if request.status == "PENDING" and request.expires_at <= now:
                    request = ApprovalRequestR1(**{**request.to_dict(), "status": "EXPIRED"})
                    changed = True
                requests.append(request.to_dict())
                if request.request_id == request_id:
                    found = request
            if changed:
                data["requests"] = requests
                self._write(data)
            return found


JOURNAL_STATUSES = {
    "PREPARED", "EXECUTING", "COMPLETED", "RECONCILED", "FAILED",
    "ROLLBACK_SUCCEEDED", "ROLLBACK_FAILED", "AMBIGUOUS",
}


class ActionJournal:
    """Append/update journal with explicit ambiguous states."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("records"), list):
            raise ControlConflict("action journal is malformed")
        return data["records"]

    def _write(self, records: list[dict[str, Any]]) -> None:
        _atomic_json(self.path, {"schema": "action-journal-r1", "records": records})

    def append(self, record: Mapping[str, Any]) -> dict[str, Any]:
        status = record.get("status")
        if status not in JOURNAL_STATUSES:
            raise ControlConflict(f"unknown journal status: {status}")
        item = dict(record)
        item.setdefault("created_at", utc_now())
        item["updated_at"] = utc_now()
        with FileLock(self.lock_path):
            records = self._read()
            records.append(item)
            self._write(records)
        return item

    def update(self, action_id: str, **changes: Any) -> dict[str, Any]:
        _id(action_id, "action_id")
        if "status" in changes and changes["status"] not in JOURNAL_STATUSES:
            raise ControlConflict("unknown journal status")
        with FileLock(self.lock_path):
            records = self._read()
            for index in range(len(records) - 1, -1, -1):
                if records[index].get("action_id") == action_id:
                    records[index] = {**records[index], **changes, "updated_at": utc_now()}
                    self._write(records)
                    return records[index]
        raise ControlConflict("journal action does not exist")

    def latest(self, action_id: str) -> dict[str, Any] | None:
        with FileLock(self.lock_path):
            for record in reversed(self._read()):
                if record.get("action_id") == action_id:
                    return dict(record)
        return None

    def records(self) -> list[dict[str, Any]]:
        with FileLock(self.lock_path):
            return [dict(item) for item in self._read()]


def packet_digest(packet: Mapping[str, Any]) -> str:
    """Hash the complete packet, including all bounded payload fields."""

    return sha256_json(dict(packet))
