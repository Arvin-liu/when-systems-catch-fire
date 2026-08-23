"""OS-owned steering, queue, budget and durable-dispatch bridge for live work."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Mapping

from agent_kernel.contracts import _id, sha256_json

from agent_runtime.accounting import AccountingError, AccountingStore, BudgetScope, CostVector
from agent_runtime.dispatch_reconciliation import DispatchConflict, DispatchEnvelope, DispatchReceipt, DurableDispatchStore
from agent_runtime.event_ledger import EventLedger, EventLedgerError
from agent_runtime.queue_control import QueueControlError, QueueItem, QueueNotDispatchable, WorkQueue
from agent_runtime.resource_arbitration import ResourceArbitrationError, ResourceIntent, ResourceArbiter
from agent_runtime.steering import IntentCapsule, SteeringValidationError

from .live_admission import LiveAdmissionDecision
from .live_bridge import LiveDispatchEnvelope


LIVE_ORCHESTRATION_SCHEMA = "ignition-136-live-orchestration-r1"
NO_NEW_BILLING_AUTHORITY_INVARIANT = "NO_NEW_BILLING_AUTHORITY_INVARIANT"


class LiveOrchestrationError(RuntimeError):
    """Raised when an OS traffic-system boundary refuses live preparation."""


@dataclass(frozen=True)
class LiveSteeringBinding:
    """The minimum OS-owned context allowed to cross into an executor adapter."""

    capsule: IntentCapsule
    why_next_ref: str
    priority: int
    profile_ref: str
    project_ref: str
    budget_scope: BudgetScope
    priority_source: str = "OS_STEERING_PRIORITY"

    def __post_init__(self) -> None:
        if not isinstance(self.capsule, IntentCapsule):
            raise LiveOrchestrationError("live steering binding requires an IntentCapsule")
        try:
            _id(self.why_next_ref, "why_next_ref")
            _id(self.profile_ref, "profile_ref")
            _id(self.project_ref, "project_ref")
        except ValueError as exc:
            raise LiveOrchestrationError("live steering reference is not canonical") from exc
        if not isinstance(self.priority, int) or isinstance(self.priority, bool) or not 0 <= self.priority <= 1000:
            raise LiveOrchestrationError("OS steering priority must be bounded")
        if self.priority_source != "OS_STEERING_PRIORITY":
            raise LiveOrchestrationError("live priority must come from the OS steering policy")
        if self.capsule.executor_can_mutate_canonical or self.capsule.authority_boundary != "OS_CANONICAL_EXECUTOR_REPORT_ONLY":
            raise LiveOrchestrationError("executor cannot mutate canonical Intent or Goal records")


@dataclass(frozen=True)
class LiveDispatchPlan:
    """Durable OS preparation; it is not an external completion receipt."""

    dispatch_id: str
    queue_id: str
    run_id: str
    reservation_id: str
    resource_lease_ids: tuple[str, ...]
    dispatch_record: Mapping[str, Any]
    ledger_event_ids: tuple[str, ...]
    status: str = "PREPARED"
    claim_ceiling: str = "OS dispatch preparation only; executor output requires independent validation."

    def __post_init__(self) -> None:
        for value, field in ((self.dispatch_id, "dispatch_id"), (self.queue_id, "queue_id"), (self.run_id, "run_id"), (self.reservation_id, "reservation_id")):
            _id(value, field)
        if self.status not in {"PREPARED", "STARTED", "FINALIZED"}:
            raise LiveOrchestrationError("unknown live dispatch plan status")
        if not isinstance(self.dispatch_record, Mapping):
            raise LiveOrchestrationError("dispatch_record must be a public mapping")
        if not isinstance(self.resource_lease_ids, tuple) or any(not isinstance(item, str) or not item.strip() for item in self.resource_lease_ids):
            raise LiveOrchestrationError("resource lease ids must be non-empty text")


class LiveDispatchCoordinator:
    """Connect one bounded live envelope to existing OS traffic primitives.

    This coordinator never selects a goal, grants permission, or interprets an
    executor result.  It persists only bounded refs/digests and leaves receipt
    validation to the live state machine and independent validator.
    """

    def __init__(
        self,
        *,
        envelope: LiveDispatchEnvelope,
        steering: LiveSteeringBinding,
        admission: LiveAdmissionDecision,
        queue: WorkQueue,
        resources: ResourceArbiter,
        accounting: AccountingStore,
        dispatch_store: DurableDispatchStore,
        ledger: EventLedger,
        clock: Any = None,
    ) -> None:
        if not isinstance(envelope, LiveDispatchEnvelope) or not isinstance(steering, LiveSteeringBinding):
            raise LiveOrchestrationError("live coordinator requires typed envelope and steering binding")
        if not isinstance(admission, LiveAdmissionDecision) or admission.status != "ADMITTED":
            raise LiveOrchestrationError("live coordinator requires an OS-admitted capability decision")
        if admission.executor_id != envelope.executor_id or admission.lease_id != envelope.capability_lease_ref:
            raise LiveOrchestrationError("admission decision is not bound to the live envelope")
        if envelope.budget_authority != "NO_NEW_BILLING_AUTHORITY":
            raise LiveOrchestrationError(NO_NEW_BILLING_AUTHORITY_INVARIANT + " violated")
        if envelope.workspace_mode != "DISPOSABLE_READ_ONLY" or envelope.side_effect_class != "READ_ONLY_SYNTHETIC":
            raise LiveOrchestrationError("live coordinator only admits disposable read-only synthetic work")
        if envelope.intent_capsule_ref is not None and envelope.intent_capsule_ref != steering.capsule.capsule_id:
            raise LiveOrchestrationError("Intent Capsule reference does not bind to the OS steering capsule")
        if tuple(envelope.permission_ceiling) != tuple(admission.effective_capabilities):
            raise LiveOrchestrationError("live envelope permission ceiling differs from the admitted OS intersection")
        if steering.budget_scope.executor_id != envelope.executor_id:
            raise LiveOrchestrationError("budget scope executor is not envelope executor")
        if steering.budget_scope.workspace_id != envelope.workspace_mode:
            raise LiveOrchestrationError("budget scope workspace is not disposable read-only")
        self.envelope = envelope
        self.steering = steering
        self.admission = admission
        self.queue = queue
        self.resources = resources
        self.accounting = accounting
        self.dispatch_store = dispatch_store
        self.ledger = ledger
        self.clock = clock or time.time
        self._plan: LiveDispatchPlan | None = None
        self._event_sequence = 0

    @property
    def plan(self) -> LiveDispatchPlan | None:
        return self._plan

    def _emit(self, event_type: str, payload: Mapping[str, Any]) -> str:
        self._event_sequence += 1
        event_id = f"live-event-{self.envelope.dispatch_id}-{self._event_sequence:02d}"
        self.ledger.append_event(
            aggregate_id=f"live-dispatch-{self.envelope.dispatch_id}",
            event_type=event_type,
            payload=dict(payload),
            actor_ref="os-live-bridge",
            source_refs=(self.envelope.task_id, self.envelope.capability_lease_ref),
            event_id=event_id,
            idempotency_key=f"live-idem-{self.envelope.dispatch_id}-{self._event_sequence:02d}",
            sensitivity="INTERNAL_OPERATIONAL",
            retention_class="LONG",
        )
        return event_id

    def prepare(self) -> LiveDispatchPlan:
        if self._plan is not None:
            return self._plan
        now = float(self.clock())
        queue_id = f"live-queue-{self.envelope.dispatch_id}"
        run_id = f"live-run-{self.envelope.dispatch_id}"
        reservation_id = f"live-budget-{self.envelope.dispatch_id}"
        intent_id = f"live-intent-{self.envelope.dispatch_id}"
        queue_item = QueueItem(
            queue_id=queue_id,
            run_id=run_id,
            profile_ref=self.steering.profile_ref,
            project_ref=self.steering.project_ref,
            priority=self.steering.priority,
            enqueued_at=now,
            deadline_epoch=now + self.envelope.timeout_seconds,
            cost_units=1,
            executor_id=self.envelope.executor_id,
            required_capabilities=self.envelope.permission_ceiling,
        )
        resource_intent = ResourceIntent(
            intent_id=intent_id,
            run_id=run_id,
            resource=f"executor:{self.envelope.executor_id}",
            intent_type="READ_SHARED",
            priority=self.steering.priority,
            ttl_seconds=self.envelope.timeout_seconds,
        )
        old_dispatch = DispatchEnvelope(
            dispatch_id=self.envelope.dispatch_id,
            task_id=self.envelope.task_id,
            executor_id=self.envelope.executor_id,
            idempotency_key=f"live-idempotency-{self.envelope.dispatch_id}",
            payload_digest=self.envelope.synthetic_input_digest,
            effect_class="READ_ONLY",
            created_at=now,
            timeout_seconds=self.envelope.timeout_seconds,
        )
        estimated = CostVector(action_count=1, wall_clock_seconds=self.envelope.timeout_seconds, output_bytes=1, event_volume=3)
        event_ids: list[str] = []
        resource_leases = ()
        try:
            queued = self.queue.enqueue(queue_item)
            admitted_queue = self.queue.admit_next(now=now)
            if admitted_queue is None or admitted_queue.queue_id != queued.queue_id:
                raise LiveOrchestrationError("OS queue did not admit the selected live item")
            event_ids.append(self._emit("ROUTE_SELECTED", {
                "status": "ADMITTED",
                "executor_id": self.envelope.executor_id,
                "priority": self.steering.priority,
                "priority_source": self.steering.priority_source,
                "why_next_ref": self.steering.why_next_ref,
                "intent_capsule_ref": self.steering.capsule.capsule_id,
                "permission_ceiling": list(self.envelope.permission_ceiling),
            }))
            resource_leases = self.resources.acquire_many((resource_intent,), now=now)
            event_ids.append(self._emit("RESOURCE_INTENT_ACQUIRED", {
                "lease_ids": [lease.lease_id for lease in resource_leases],
                "resource": resource_intent.resource,
                "intent_type": resource_intent.intent_type,
            }))
            self.accounting.reserve(
                reservation_id,
                self.steering.budget_scope,
                estimated,
                attempt_kind="PRIMARY",
                idempotency_key=f"live-budget-reserve-{self.envelope.dispatch_id}",
                occurred_at=now,
            )
            self.queue.dispatch(queue_id, now=now)
            record = self.dispatch_store.create(old_dispatch)
            event_ids.append(self._emit("DISPATCH_CREATED", {
                "dispatch_id": record.dispatch_id,
                "queue_id": queue_id,
                "reservation_id": reservation_id,
                "attempt_kind": "PRIMARY",
                "billing_authority": self.envelope.budget_authority,
                "retry_policy": self.envelope.retry_policy,
                "reconciliation_policy": self.envelope.reconciliation_policy,
                "synthetic_input_digest": self.envelope.synthetic_input_digest,
            }))
        except (QueueControlError, QueueNotDispatchable, ResourceArbitrationError, AccountingError, EventLedgerError, DispatchConflict, LiveOrchestrationError):
            for lease in resource_leases:
                try:
                    self.resources.release(lease.lease_id)
                except ResourceArbitrationError:
                    pass
            raise
        self._plan = LiveDispatchPlan(
            dispatch_id=self.envelope.dispatch_id,
            queue_id=queue_id,
            run_id=run_id,
            reservation_id=reservation_id,
            resource_lease_ids=tuple(lease.lease_id for lease in resource_leases),
            dispatch_record=record.to_dict(),
            ledger_event_ids=tuple(event_ids),
        )
        return self._plan

    def start(self) -> Mapping[str, Any]:
        """Cross the durable dispatch boundary exactly once after preparation."""

        plan = self.prepare()
        record = self.dispatch_store.mark_sent(plan.dispatch_id)
        record = self.dispatch_store.acknowledge(plan.dispatch_id, accepted=True, ack_ref=f"live-admitted-{plan.dispatch_id}")
        self._emit("DISPATCH_ACCEPTED", {
            "dispatch_id": plan.dispatch_id,
            "executor_id": self.envelope.executor_id,
            "attempt": record.attempt,
            "why_next_ref": self.steering.why_next_ref,
            "intent_capsule_ref": self.steering.capsule.capsule_id,
        })
        return record.to_dict()

    def public_plan(self) -> dict[str, Any]:
        plan = self.prepare()
        return {
            "schema": LIVE_ORCHESTRATION_SCHEMA,
            "dispatch_id": plan.dispatch_id,
            "queue_id": plan.queue_id,
            "run_id": plan.run_id,
            "reservation_id": plan.reservation_id,
            "resource_lease_ids": list(plan.resource_lease_ids),
            "ledger_event_ids": list(plan.ledger_event_ids),
            "dispatch_record_digest": sha256_json(plan.dispatch_record),
            "priority_source": self.steering.priority_source,
            "why_next_ref": self.steering.why_next_ref,
            "intent_capsule_ref": self.steering.capsule.capsule_id,
            "executor_canonical_mutation_allowed": False,
            "goal_completion_inference_allowed": False,
            "billing_authority": self.envelope.budget_authority,
            "claim_ceiling": plan.claim_ceiling,
        }


__all__ = [
    "LIVE_ORCHESTRATION_SCHEMA", "NO_NEW_BILLING_AUTHORITY_INVARIANT", "LiveDispatchCoordinator",
    "LiveDispatchPlan", "LiveOrchestrationError", "LiveSteeringBinding",
]
