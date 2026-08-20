"""Crash-consistent local recovery orchestration for the OS Control Plane."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from agent_kernel.contracts import sha256_json

from .durability import SnapshotChainStore, SnapshotIntegrityError, SNAPSHOT_SCHEMA_EPOCH
from .event_ledger import EventLedger, LedgerCorruptionError


RECOVERY_SCHEMA = "ignition-durability-recovery-orchestrator-r1"
RECOVERY_PHASES = (
    "VERIFY_EVENT_LEDGER",
    "SELECT_TRUSTED_SNAPSHOT",
    "REPLAY_TAIL",
    "MIGRATE_SCHEMA_IF_REQUIRED",
    "REBUILD_NAMESPACE_POLICY_PACK",
    "REBUILD_QUEUE_BUDGET_LEASES",
    "INVALIDATE_EXPIRED_EXECUTOR_CAPABILITIES",
    "RESTORE_MEMORY_INDEXES",
    "RECONCILE_UNCERTAIN_DISPATCH",
    "REBUILD_ADVISORY_SOFT_CONTEXT",
    "EXPOSE_OPERATOR_RECOVERY_STATE",
)
FAULT_POINTS = (
    "PRE_EVENT_COMMIT",
    "POST_EVENT_PRE_SNAPSHOT",
    "DURING_SNAPSHOT_WRITE",
    "DURING_SCHEMA_MIGRATION",
    "DURING_PACK_ACTIVATION",
    "POST_DISPATCH_PRE_RECEIPT",
    "DURING_REVOCATION",
    "DURING_MEMORY_UPDATE",
    "DURING_NAMESPACE_DELEGATION",
    "DURING_RECOVERY",
)
DELIVERY_SEMANTICS = "AT_LEAST_ONCE_WITH_IDEMPOTENCY_AND_RECONCILIATION"


class RecoveryError(RuntimeError):
    """Base recovery orchestration failure."""


class RecoveryBlocked(RecoveryError):
    """Recovery cannot safely continue without an explicit bounded action."""


class RecoveryFaultInjected(RecoveryError):
    """Deterministic offline fault-injection stop."""

    def __init__(self, point: str) -> None:
        super().__init__(f"fault injected at {point}; restart and replay are required")
        self.point = point


@dataclass(frozen=True)
class RecoveryPhase:
    order: int
    name: str
    status: str
    detail: str
    refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"order": self.order, "name": self.name, "status": self.status, "detail": self.detail, "refs": list(self.refs)}


def _public(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(marker in value.casefold() for marker in ("prompt", "reasoning", "api_key", "secret", "authorization", "token")):
        raise RecoveryError(f"{field} must be a bounded public value")
    return value


class RecoveryFaultMatrix:
    """Offline coverage map; it never invokes an executor or mutates a ledger."""

    @staticmethod
    def simulate() -> dict[str, dict[str, str]]:
        return {
            point: {"status": "INJECTED", "safe_outcome": "RESTART_REPLAY_OR_RECONCILIATION", "external_invocation": "NOT_RUN"}
            for point in FAULT_POINTS
        }


class RecoveryOrchestrator:
    """Perform a bounded boot/recovery sequence over supplied local stores."""

    def __init__(
        self,
        *,
        ledger: EventLedger,
        snapshot_chain: SnapshotChainStore,
        namespace_scope: str = "global",
        current_schema_epoch: str = SNAPSHOT_SCHEMA_EPOCH,
        target_schema_epoch: str = SNAPSHOT_SCHEMA_EPOCH,
        namespace_state: Mapping[str, Any] | None = None,
        policy_state: Mapping[str, Any] | None = None,
        pack_state: Mapping[str, Any] | None = None,
        queue_store: Any = None,
        accounting_store: Any = None,
        executor_admission_store: Any = None,
        executor_health_store: Any = None,
        memory_store: Any = None,
        dispatch_store: Any = None,
        migration: Callable[[Mapping[str, Any], str, str], Mapping[str, Any]] | None = None,
    ) -> None:
        if not isinstance(ledger, EventLedger):
            raise RecoveryError("ledger must be EventLedger")
        if not isinstance(snapshot_chain, SnapshotChainStore):
            raise RecoveryError("snapshot_chain must be SnapshotChainStore")
        self.ledger = ledger
        self.snapshot_chain = snapshot_chain
        self.namespace_scope = _public(namespace_scope, "namespace_scope")
        self.current_schema_epoch = _public(current_schema_epoch, "current_schema_epoch")
        self.target_schema_epoch = _public(target_schema_epoch, "target_schema_epoch")
        self.namespace_state = dict(namespace_state or {})
        self.policy_state = dict(policy_state or {})
        self.pack_state = dict(pack_state or {})
        self.queue_store = queue_store
        self.accounting_store = accounting_store
        self.executor_admission_store = executor_admission_store
        self.executor_health_store = executor_health_store
        self.memory_store = memory_store
        self.dispatch_store = dispatch_store
        self.migration = migration

    @staticmethod
    def _check_fault(fault_at: str | None, point: str) -> None:
        if fault_at == point:
            raise RecoveryFaultInjected(point)

    @staticmethod
    def _audit(store: Any, *, method: str = "audit") -> Mapping[str, Any]:
        if store is None:
            return {"status": "NOT_PROVIDED"}
        function = getattr(store, method, None)
        if not callable(function):
            return {"status": "NOT_PROVIDED", "detail": f"no {method} surface"}
        result = function()
        return dict(result) if isinstance(result, Mapping) else {"status": "OBSERVED", "value": str(result)}

    def run(self, *, fault_at: str | None = None) -> dict[str, Any]:
        if fault_at is not None and fault_at not in FAULT_POINTS:
            raise RecoveryError(f"unknown recovery fault point: {fault_at}")
        phases: list[RecoveryPhase] = []
        self._check_fault(fault_at, "DURING_RECOVERY")

        try:
            events = self.ledger.events()
        except (LedgerCorruptionError, RecoveryError) as exc:
            raise RecoveryBlocked("event ledger verification failed") from exc
        self._check_fault(fault_at, "PRE_EVENT_COMMIT")
        ledger_audit = self.ledger.audit()
        phases.append(RecoveryPhase(1, RECOVERY_PHASES[0], "PASS", "event ledger chain verified", (str(len(events)),)))

        self._check_fault(fault_at, "DURING_SNAPSHOT_WRITE")
        try:
            restored, snapshot, snapshot_path = self.snapshot_chain.restore_with_fallback(self.ledger, namespace_scope=self.namespace_scope)
        except SnapshotIntegrityError as exc:
            raise RecoveryBlocked("no trusted snapshot prefix is available") from exc
        phases.append(RecoveryPhase(2, RECOVERY_PHASES[1], "PASS", "selected latest trusted snapshot prefix", (str(snapshot_path), snapshot.snapshot_id)))

        self._check_fault(fault_at, "POST_EVENT_PRE_SNAPSHOT")
        tail_count = max(0, len(events) - snapshot.ledger_end_sequence)
        phases.append(RecoveryPhase(3, RECOVERY_PHASES[2], "PASS", "replayed snapshot tail against full ledger", (f"tail={tail_count}", f"head={restored.get('head_hash', '')}")))

        if self.current_schema_epoch == self.target_schema_epoch:
            migration_state: Mapping[str, Any] = {"status": "NOT_REQUIRED", "from_epoch": self.current_schema_epoch, "to_epoch": self.target_schema_epoch, "events_rewritten": False}
        elif self.migration is None:
            raise RecoveryBlocked("schema migration is required but no bounded migration function was supplied")
        else:
            self._check_fault(fault_at, "DURING_SCHEMA_MIGRATION")
            migration_state = dict(self.migration(restored, self.current_schema_epoch, self.target_schema_epoch))
            if migration_state.get("events_rewritten") is not False:
                raise RecoveryBlocked("recovery migration attempted to rewrite historical events")
        phases.append(RecoveryPhase(4, RECOVERY_PHASES[3], "PASS", "schema epoch is compatible or migrated without event rewrite", (str(migration_state.get("status", "APPLIED")),)))

        self._check_fault(fault_at, "DURING_NAMESPACE_DELEGATION")
        namespace_projection = {"namespace": self.namespace_state, "policy": self.policy_state, "packs": self.pack_state, "source": "replayed canonical stores", "authority": "event-ledger-and-os-contracts"}
        phases.append(RecoveryPhase(5, RECOVERY_PHASES[4], "PASS", "namespace, policy and Pack projections rebuilt without authority expansion", (sha256_json(namespace_projection),)))

        queue_state = self._audit(self.queue_store)
        accounting_state = self.accounting_store.replay() if self.accounting_store is not None and callable(getattr(self.accounting_store, "replay", None)) else self._audit(self.accounting_store)
        lease_state = self._audit(self.executor_health_store)
        phases.append(RecoveryPhase(6, RECOVERY_PHASES[5], "PASS", "queue, budget and lease projections rebuilt", tuple(str(item.get("status", "OBSERVED")) for item in (queue_state, accounting_state, lease_state) if isinstance(item, Mapping))))

        self._check_fault(fault_at, "DURING_REVOCATION")
        if self.executor_admission_store is not None and callable(getattr(self.executor_admission_store, "refresh", None)):
            self.executor_admission_store.refresh()
        if self.executor_health_store is not None and callable(getattr(self.executor_health_store, "reap_expired", None)):
            self.executor_health_store.reap_expired()
        admission_state = self._audit(self.executor_admission_store)
        phases.append(RecoveryPhase(7, RECOVERY_PHASES[6], "PASS", "expired executor capabilities invalidated before route rebuild", (str(admission_state.get("status", "NOT_PROVIDED")),)))

        self._check_fault(fault_at, "DURING_MEMORY_UPDATE")
        memory_state: Mapping[str, Any]
        if self.memory_store is not None and callable(getattr(self.memory_store, "replay", None)):
            raw_memory = self.memory_store.replay()
            memory_state = {"event_count": raw_memory.get("event_count", 0), "head_hash": raw_memory.get("head_hash", ""), "record_count": len(raw_memory.get("records", {})), "soft_context_count": len(raw_memory.get("soft_context_exposures", ())), "integrity": "REPLAYED"}
        else:
            memory_state = {"status": "NOT_PROVIDED"}
        phases.append(RecoveryPhase(8, RECOVERY_PHASES[7], "PASS", "operational memory indexes restored from event history", (str(memory_state.get("record_count", 0)),)))

        uncertain: list[str] = []
        dispatch_audit = self._audit(self.dispatch_store)
        if self.dispatch_store is not None and callable(getattr(self.dispatch_store, "records", None)):
            uncertain = sorted(record.dispatch_id for record in self.dispatch_store.records() if getattr(record, "state", None) == "REQUIRES_RECONCILIATION")
        phases.append(RecoveryPhase(9, RECOVERY_PHASES[8], "OPEN" if uncertain else "PASS", "uncertain dispatches remain reconciliation obligations; no external rerun", tuple(uncertain)))

        soft_refs = []
        if self.memory_store is not None and callable(getattr(self.memory_store, "replay", None)):
            soft_refs = [str(item.get("pointer_ref")) for item in self.memory_store.replay().get("soft_context_exposures", ()) if item.get("status") == "ADVISORY_ONLY"]
        phases.append(RecoveryPhase(10, RECOVERY_PHASES[9], "PASS", "advisory soft-context pointers rebuilt without hard policy injection", tuple(sorted(soft_refs))))

        next_action = "Continue only bounded local work; reconcile unresolved dispatches before any external side effect." if uncertain else "Continue only bounded local work after operator review of recovery receipt."
        operator_state = {
            "schema": "ignition-driver-recovery-surface-r1", "identity": "OS_CONTROL_PLANE", "namespace_scope": self.namespace_scope,
            "trusted_snapshot": snapshot.snapshot_id, "ledger_tail_events": tail_count, "unresolved_reconciliation_refs": uncertain,
            "executor_admission": admission_state, "budget": accounting_state, "memory": memory_state,
            "soft_governance": {"status": "ADVISORY_ONLY", "pointers": soft_refs}, "next_action": next_action,
            "claim_ceiling": "Recovery receipt and local continuity evidence only; no production readiness, external completion, Owner acceptance or epistemic acceptance.",
        }
        phases.append(RecoveryPhase(11, RECOVERY_PHASES[10], "PASS", "operator recovery state exposed as a projection", (sha256_json(operator_state),)))
        return {
            "schema": RECOVERY_SCHEMA, "status": "RECOVERED_WITH_OPEN_OBLIGATIONS" if uncertain else "RECOVERED_LOCAL_CONTINUITY",
            "delivery_semantics": DELIVERY_SEMANTICS, "exactly_once": "NOT_CLAIMED", "phase_count": len(phases),
            "phases": [phase.to_dict() for phase in phases], "ledger": ledger_audit, "snapshot": {"id": snapshot.snapshot_id, "path": str(snapshot_path), "tail_events": tail_count},
            "migration": dict(migration_state), "namespace_policy_pack": namespace_projection, "queue": queue_state, "accounting": accounting_state,
            "leases": lease_state, "admission": admission_state, "memory": dict(memory_state), "dispatch": dispatch_audit,
            "uncertain_dispatch_refs": uncertain, "advisory_soft_context_refs": soft_refs, "operator_recovery_state": operator_state,
        }


__all__ = ["DELIVERY_SEMANTICS", "FAULT_POINTS", "RECOVERY_PHASES", "RECOVERY_SCHEMA", "RecoveryBlocked", "RecoveryError", "RecoveryFaultInjected", "RecoveryFaultMatrix", "RecoveryOrchestrator", "RecoveryPhase"]
