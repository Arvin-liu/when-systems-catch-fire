"""Cross-executor progress, receipt and operational-memory convergence R1.

External sessions and vendor histories stay outside the OS.  This module keeps
only sortable public progress records, receipt status/digests, and bounded
projections that an existing OperationalMemoryStore may append.  It never
stores prompts, hidden reasoning, token telemetry or private session bodies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .approval_handoff import ApprovalBridgeDecision, FailoverDecision
from .contracts import FederatedProgressEvent, FederatedResultReceipt, FederationContractError, canonical_digest


PROGRESS_INGEST_STATES = frozenset({"NEW", "DUPLICATE", "LATE_EVENT", "LATE_TERMINAL", "POST_TERMINAL_EVENT"})
RECEIPT_INGEST_STATES = frozenset({"VERIFIED", "FAILURE_RECORDED", "UNVERIFIED", "DUPLICATE"})
MEMORY_PROJECTION_TYPES = frozenset({"EPISODIC", "FAILURE", "APPROVAL", "ROLLBACK", "UNRESOLVED_CONTINUATION"})
_TERMINAL_PROGRESS_STATES = frozenset({
    "COMPLETED_VALIDATED",
    "COMPLETED_UNVALIDATED",
    "FAILED",
    "FAILED_VALIDATION",
    "BLOCKED_WITH_EVIDENCE",
    "CANCELLED",
    "REQUIRES_RECONCILIATION",
})
_PRIVATE_MARKERS = ("prompt", "chain-of-thought", "chain_of_thought", "cot", "reasoning", "token", "secret", "cookie", "authorization", "api_key", "password")


class ConvergenceError(FederationContractError):
    """Raised when an external record cannot cross the OS convergence boundary."""


def _public(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConvergenceError(f"{field} must be a non-empty string")
    lowered = value.casefold()
    if any(marker in lowered for marker in _PRIVATE_MARKERS):
        raise ConvergenceError(f"{field} contains hidden or secret material")
    return value


def _strings(values: Sequence[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise ConvergenceError(f"{field} must be an array")
    result = tuple(_public(value, f"{field}[]") for value in values)
    if len(result) != len(set(result)):
        raise ConvergenceError(f"{field} must not contain duplicates")
    return result


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_terminal(event: FederatedProgressEvent) -> bool:
    return event.state in _TERMINAL_PROGRESS_STATES


@dataclass(frozen=True)
class ProgressIngestResult:
    status: str
    event_key: str
    event: FederatedProgressEvent
    highest_sequence_before: int

    def __post_init__(self) -> None:
        if self.status not in PROGRESS_INGEST_STATES:
            raise ConvergenceError("progress ingest status is unsupported")
        _public(self.event_key, "progress.event_key")
        if not isinstance(self.event, FederatedProgressEvent):
            raise ConvergenceError("progress result event must be FederatedProgressEvent")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "event_key": self.event_key,
            "event": self.event.to_dict(),
            "highest_sequence_before": self.highest_sequence_before,
        }


class ProgressLedger:
    """Deduplicate public events without letting late events regress state."""

    def __init__(self) -> None:
        self._events: dict[str, list[tuple[str, FederatedProgressEvent]]] = {}
        self._seen_keys: set[str] = set()
        self._highest: dict[str, int] = {}
        self._terminal_sequence: dict[str, int] = {}

    def ingest(self, event: FederatedProgressEvent, *, event_key: str | None = None) -> ProgressIngestResult:
        if not isinstance(event, FederatedProgressEvent):
            raise ConvergenceError("ProgressLedger accepts FederatedProgressEvent only")
        key = event_key or canonical_digest(event.to_dict())
        _public(key, "progress.event_key")
        task_id = event.federation_task_id
        highest_before = self._highest.get(task_id, -1)
        if key in self._seen_keys:
            return ProgressIngestResult("DUPLICATE", key, event, highest_before)
        if event.sequence < highest_before:
            status = "LATE_TERMINAL" if _is_terminal(event) else "LATE_EVENT"
        elif task_id in self._terminal_sequence and not _is_terminal(event):
            status = "POST_TERMINAL_EVENT"
        else:
            status = "NEW"
        self._seen_keys.add(key)
        self._events.setdefault(task_id, []).append((key, event))
        self._highest[task_id] = max(highest_before, event.sequence)
        if _is_terminal(event):
            self._terminal_sequence[task_id] = max(self._terminal_sequence.get(task_id, -1), event.sequence)
        return ProgressIngestResult(status, key, event, highest_before)

    def ordered(self, federation_task_id: str) -> tuple[FederatedProgressEvent, ...]:
        _public(federation_task_id, "federation_task_id")
        values = self._events.get(federation_task_id, ())
        return tuple(event for _, event in sorted(values, key=lambda item: (item[1].sequence, item[1].executor_id, item[0])))

    def canonical(self, federation_task_id: str) -> FederatedProgressEvent | None:
        ordered = self.ordered(federation_task_id)
        if not ordered:
            return None
        return ordered[-1]

    def audit(self) -> dict[str, Any]:
        return {
            "status": "PASS",
            "task_count": len(self._events),
            "event_count": sum(len(items) for items in self._events.values()),
            "deduplicated_event_keys": len(self._seen_keys),
        }


@dataclass(frozen=True)
class ReceiptIngestResult:
    status: str
    receipt_digest: str
    federation_task_id: str
    terminal_state: str
    validation_refs: tuple[str, ...]
    artifact_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in RECEIPT_INGEST_STATES:
            raise ConvergenceError("receipt ingest status is unsupported")
        _public(self.receipt_digest, "receipt.receipt_digest")
        _public(self.federation_task_id, "receipt.federation_task_id")
        _public(self.terminal_state, "receipt.terminal_state")
        _strings(self.validation_refs, "receipt.validation_refs")
        _strings(self.artifact_refs, "receipt.artifact_refs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "receipt_digest": self.receipt_digest,
            "federation_task_id": self.federation_task_id,
            "terminal_state": self.terminal_state,
            "validation_refs": list(self.validation_refs),
            "artifact_refs": list(self.artifact_refs),
        }


class ReceiptRegistry:
    """Store only receipt digest/status metadata, never raw vendor telemetry."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._records: dict[str, ReceiptIngestResult] = {}

    def register(self, receipt: FederatedResultReceipt) -> ReceiptIngestResult:
        if not isinstance(receipt, FederatedResultReceipt):
            raise ConvergenceError("ReceiptRegistry accepts FederatedResultReceipt only")
        digest = receipt.receipt_digest
        if digest in self._seen:
            return ReceiptIngestResult("DUPLICATE", digest, receipt.federation_task_id, receipt.terminal_state, tuple(receipt.validation_refs), tuple(item.ref for item in receipt.artifact_refs))
        self._seen.add(digest)
        if receipt.terminal_state == "COMPLETED_VALIDATED" and receipt.validation_refs:
            status = "VERIFIED"
        elif receipt.terminal_state in {"FAILED", "FAILED_VALIDATION", "BLOCKED_WITH_EVIDENCE", "CANCELLED"}:
            status = "FAILURE_RECORDED"
        else:
            status = "UNVERIFIED"
        result = ReceiptIngestResult(status, digest, receipt.federation_task_id, receipt.terminal_state, tuple(receipt.validation_refs), tuple(item.ref for item in receipt.artifact_refs))
        self._records[receipt.federation_task_id] = result
        return result

    def latest(self, federation_task_id: str) -> ReceiptIngestResult | None:
        return self._records.get(federation_task_id)


@dataclass(frozen=True)
class MemoryProjection:
    memory_id: str
    memory_type: str
    source_run_id: str
    summary: str
    provenance_refs: tuple[str, ...]
    tags: tuple[str, ...]
    created_at: str
    visibility: str = "SHARED_OPERATIONAL"
    sensitivity_class: str = "INTERNAL_OPERATIONAL"
    retention_class: str = "LONG"
    forget_policy: str = "MANUAL"

    def __post_init__(self) -> None:
        _public(self.memory_id, "memory_projection.memory_id")
        if self.memory_type not in MEMORY_PROJECTION_TYPES:
            raise ConvergenceError("memory projection type is unsupported")
        _public(self.source_run_id, "memory_projection.source_run_id")
        _public(self.summary, "memory_projection.summary")
        object.__setattr__(self, "provenance_refs", _strings(self.provenance_refs, "memory_projection.provenance_refs"))
        object.__setattr__(self, "tags", _strings(self.tags, "memory_projection.tags"))
        _public(self.created_at, "memory_projection.created_at")

    def to_memory_entry(self) -> Any:
        """Create an entry for the existing OperationalMemoryStore boundary."""

        from agent_runtime.memory import MemoryEntry

        return MemoryEntry.create(
            memory_id=self.memory_id,
            memory_type=self.memory_type,
            source_run_id=self.source_run_id,
            summary=self.summary,
            provenance_refs=self.provenance_refs,
            tags=self.tags,
            created_at=self.created_at,
            visibility=self.visibility,
            sensitivity_class=self.sensitivity_class,
            retention_class=self.retention_class,
            forget_policy=self.forget_policy,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "source_run_id": self.source_run_id,
            "summary": self.summary,
            "provenance_refs": list(self.provenance_refs),
            "tags": list(self.tags),
            "created_at": self.created_at,
            "visibility": self.visibility,
            "sensitivity_class": self.sensitivity_class,
            "retention_class": self.retention_class,
            "forget_policy": self.forget_policy,
        }


def project_progress(event: FederatedProgressEvent, *, memory_id: str, source_run_id: str, event_key: str) -> MemoryProjection:
    if not isinstance(event, FederatedProgressEvent):
        raise ConvergenceError("project_progress requires FederatedProgressEvent")
    _public(event_key, "progress.event_key")
    refs = tuple(dict.fromkeys((*event.refs, f"federation-event:{event_key}")))
    return MemoryProjection(
        memory_id=memory_id,
        memory_type="EPISODIC",
        source_run_id=source_run_id,
        summary=f"External executor public progress: {event.public_summary}",
        provenance_refs=refs,
        tags=("external-executor", event.executor_id, event.state.casefold()),
        created_at=_now(),
    )


def project_receipt(receipt: FederatedResultReceipt, *, memory_id: str, source_run_id: str, ingest: ReceiptIngestResult) -> MemoryProjection:
    if not isinstance(receipt, FederatedResultReceipt) or not isinstance(ingest, ReceiptIngestResult):
        raise ConvergenceError("project_receipt requires a receipt and ingest result")
    if ingest.status == "VERIFIED":
        memory_type = "EPISODIC"
        summary = f"Validated external receipt {receipt.receipt_digest[:16]} recorded with OS validator refs."
        refs = tuple((*receipt.validation_refs, *(item.ref for item in receipt.artifact_refs)))
    elif ingest.status == "FAILURE_RECORDED":
        memory_type = "FAILURE"
        summary = f"External executor failure recorded with terminal state {receipt.terminal_state}."
        refs = (f"receipt:{receipt.receipt_digest}",)
    else:
        memory_type = "UNRESOLVED_CONTINUATION"
        summary = f"External receipt {receipt.receipt_digest[:16]} requires reconciliation; executor completion was not accepted as validation."
        refs = (f"receipt:{receipt.receipt_digest}",)
    return MemoryProjection(
        memory_id=memory_id,
        memory_type=memory_type,
        source_run_id=source_run_id,
        summary=summary,
        provenance_refs=refs,
        tags=("external-receipt", ingest.status.casefold()),
        created_at=_now(),
    )


def project_approval(decision: ApprovalBridgeDecision, *, memory_id: str, source_run_id: str) -> MemoryProjection:
    if not isinstance(decision, ApprovalBridgeDecision):
        raise ConvergenceError("project_approval requires ApprovalBridgeDecision")
    refs = (decision.external_observation.observation_ref,) if decision.external_observation.observation_ref else ()
    return MemoryProjection(
        memory_id=memory_id,
        memory_type="APPROVAL",
        source_run_id=source_run_id,
        summary=f"Federation approval bridge recorded {decision.status}: {decision.reason}",
        provenance_refs=refs,
        tags=("external-approval", decision.status.casefold()),
        created_at=_now(),
    )


def project_recovery(decision: FailoverDecision, *, memory_id: str, source_run_id: str) -> MemoryProjection:
    if not isinstance(decision, FailoverDecision):
        raise ConvergenceError("project_recovery requires FailoverDecision")
    return MemoryProjection(
        memory_id=memory_id,
        memory_type="ROLLBACK" if decision.automatic else "FAILURE",
        source_run_id=source_run_id,
        summary=f"Federation recovery recorded {decision.status} for {decision.failover_reason}: {decision.reason}",
        provenance_refs=(f"executor:{decision.source_executor_id}", f"target:{decision.target_executor_id}"),
        tags=("external-recovery", decision.status.casefold()),
        created_at=_now(),
    )


@dataclass(frozen=True)
class AbsorptionResult:
    status: str
    event_key: str
    memory_id: str

    def __post_init__(self) -> None:
        if self.status not in {"ABSORBED", "DUPLICATE"}:
            raise ConvergenceError("memory absorption status is unsupported")
        _public(self.event_key, "absorption.event_key")
        _public(self.memory_id, "absorption.memory_id")


class FederationMemoryAbsorber:
    """Exactly-once in-process absorption into the existing memory store."""

    def __init__(self, store: Any) -> None:
        if not hasattr(store, "append"):
            raise ConvergenceError("memory store must expose append")
        self.store = store
        self._seen_event_keys: set[str] = set()
        self._seen_memory_ids: set[str] = set()

    def absorb(self, event_key: str, projection: MemoryProjection) -> AbsorptionResult:
        if not isinstance(projection, MemoryProjection):
            raise ConvergenceError("absorb requires MemoryProjection")
        _public(event_key, "absorption.event_key")
        if event_key in self._seen_event_keys or projection.memory_id in self._seen_memory_ids:
            return AbsorptionResult("DUPLICATE", event_key, projection.memory_id)
        self.store.append(projection.to_memory_entry())
        self._seen_event_keys.add(event_key)
        self._seen_memory_ids.add(projection.memory_id)
        return AbsorptionResult("ABSORBED", event_key, projection.memory_id)


class FederationConvergence:
    """Small OS coordinator for progress/receipt registries and memory sinks."""

    def __init__(self, memory_store: Any | None = None) -> None:
        self.progress = ProgressLedger()
        self.receipts = ReceiptRegistry()
        self.memory = FederationMemoryAbsorber(memory_store) if memory_store is not None else None

    def ingest_progress(self, event: FederatedProgressEvent, *, source_run_id: str, memory_id: str | None = None, event_key: str | None = None) -> ProgressIngestResult:
        result = self.progress.ingest(event, event_key=event_key)
        if result.status != "DUPLICATE" and self.memory is not None and memory_id is not None:
            self.memory.absorb(f"progress:{result.event_key}", project_progress(event, memory_id=memory_id, source_run_id=source_run_id, event_key=result.event_key))
        return result

    def ingest_receipt(self, receipt: FederatedResultReceipt, *, source_run_id: str, memory_id: str | None = None) -> ReceiptIngestResult:
        result = self.receipts.register(receipt)
        if result.status != "DUPLICATE" and self.memory is not None and memory_id is not None:
            self.memory.absorb(f"receipt:{result.receipt_digest}", project_receipt(receipt, memory_id=memory_id, source_run_id=source_run_id, ingest=result))
        return result

    def audit(self) -> dict[str, Any]:
        return {"status": "PASS", "progress": self.progress.audit(), "receipt_count": len(self.receipts._records), "memory_enabled": self.memory is not None}


__all__ = [
    "AbsorptionResult",
    "ConvergenceError",
    "FederationConvergence",
    "FederationMemoryAbsorber",
    "MemoryProjection",
    "ProgressIngestResult",
    "ProgressLedger",
    "ReceiptIngestResult",
    "ReceiptRegistry",
    "project_approval",
    "project_progress",
    "project_receipt",
    "project_recovery",
]
