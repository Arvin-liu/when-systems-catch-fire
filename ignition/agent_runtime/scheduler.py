"""Bounded concurrent OS scheduler over typed work units.

The scheduler owns readiness, budgets, resource leases and terminal
translation.  It does not contain a model loop or an external tool runtime;
offline worker callables are fixtures/adapters supplied by the caller.
"""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
import json
from pathlib import Path
import threading
import time
from typing import Any, Callable, Mapping, Sequence

from agent_kernel.contracts import _id

from .control import _atomic_json, utc_now
from .event_ledger import EventLedger, EventLedgerError
from .resource_arbitration import IntentLease, ResourceArbiter, ResourceConflict, ResourceIntent


SCHEDULER_SCHEMA = "os-control-plane-bounded-scheduler-r1"
WORKER_TERMINAL = frozenset({"COMPLETED_VALIDATED", "FAILED", "CHECKPOINTED_RESUMABLE", "CANCELLED", "REQUIRES_RECONCILIATION"})
EPISODE_TERMINAL = frozenset({
    "COMPLETED_VALIDATED",
    "COMPLETED_WITH_INDEPENDENT_FAILURES",
    "COMPLETED_WITH_CANCELLATIONS",
    "COMPLETED_WITH_DEPENDENCY_BLOCKS",
    "FAILED_FAST",
    "BUDGET_EXHAUSTED",
    "BLOCKED_RESOURCE_CONFLICT",
    "BLOCKED_POLICY",
    "BLOCKED_NO_EXECUTOR",
    "CHECKPOINTED_RESUMABLE",
})


class SchedulerError(RuntimeError):
    """A scheduler contract or recovery failure."""


class SchedulerCorruptionError(SchedulerError):
    """Persisted scheduler state cannot be recovered safely."""


@dataclass(frozen=True)
class WorkResult:
    status: str
    summary: str
    output_bytes: int = 0
    checkpoint_ref: str | None = None

    def __post_init__(self) -> None:
        if self.status not in WORKER_TERMINAL:
            raise SchedulerError(f"unknown worker result status: {self.status}")
        if not isinstance(self.summary, str) or not self.summary.strip():
            raise SchedulerError("worker result summary must be a public non-empty string")
        if any(marker in self.summary.casefold() for marker in ("prompt", "chain-of-thought", "hidden reasoning", "access_token")):
            raise SchedulerError("worker result contains forbidden private material")
        if not isinstance(self.output_bytes, int) or self.output_bytes < 0:
            raise SchedulerError("output_bytes must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "summary": self.summary, "output_bytes": self.output_bytes, "checkpoint_ref": self.checkpoint_ref}

    @classmethod
    def from_value(cls, value: Any) -> "WorkResult":
        if isinstance(value, WorkResult):
            return value
        if not isinstance(value, Mapping):
            raise SchedulerError("worker must return WorkResult or mapping")
        return cls(status=value.get("status"), summary=value.get("summary", "worker returned a typed result"), output_bytes=value.get("output_bytes", 0), checkpoint_ref=value.get("checkpoint_ref"))


@dataclass(frozen=True)
class WorkUnit:
    run_id: str
    depends_on: tuple[str, ...] = ()
    executor_id: str = "reference"
    resource_intents: tuple[ResourceIntent, ...] = ()
    action_cost: int = 1
    output_budget: int = 0
    priority: int = 0
    deadline_epoch: float | None = None
    retry_limit: int = 0
    policy_digest: str | None = None

    def __post_init__(self) -> None:
        _id(self.run_id, "run_id")
        if len(set(self.depends_on)) != len(self.depends_on) or self.run_id in self.depends_on:
            raise SchedulerError("work-unit dependencies must be unique and cannot self-reference")
        for dependency in self.depends_on:
            _id(dependency, "dependency")
        _id(self.executor_id, "executor_id")
        if not self.resource_intents:
            raise SchedulerError("every work unit must declare at least one resource intent")
        if tuple(intent.canonical_key for intent in self.resource_intents) != tuple(sorted(intent.canonical_key for intent in self.resource_intents)):
            raise SchedulerError("work-unit resource intents must be canonical ordered")
        if not isinstance(self.action_cost, int) or self.action_cost <= 0:
            raise SchedulerError("action_cost must be positive")
        if not isinstance(self.output_budget, int) or self.output_budget < 0:
            raise SchedulerError("output_budget must be non-negative")
        if not isinstance(self.priority, int) or self.priority < 0:
            raise SchedulerError("priority must be non-negative")
        if self.deadline_epoch is not None and (not isinstance(self.deadline_epoch, (int, float)) or self.deadline_epoch <= 0):
            raise SchedulerError("deadline_epoch must be positive")
        if not isinstance(self.retry_limit, int) or not 0 <= self.retry_limit <= 3:
            raise SchedulerError("retry_limit must be between 0 and 3")
        if self.policy_digest is not None and (len(self.policy_digest) != 64 or any(char not in "0123456789abcdef" for char in self.policy_digest)):
            raise SchedulerError("policy_digest must be a SHA-256 digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "depends_on": list(self.depends_on),
            "executor_id": self.executor_id,
            "resource_intents": [intent.to_dict() for intent in self.resource_intents],
            "action_cost": self.action_cost,
            "output_budget": self.output_budget,
            "priority": self.priority,
            "deadline_epoch": self.deadline_epoch,
            "retry_limit": self.retry_limit,
            "policy_digest": self.policy_digest,
        }


@dataclass(frozen=True)
class SchedulerSpec:
    episode_id: str
    max_parallel_runs: int
    executor_concurrency: Mapping[str, int]
    max_actions: int
    max_seconds: float
    max_output_bytes: int
    policy: str = "CONTINUE_INDEPENDENT"

    def __post_init__(self) -> None:
        _id(self.episode_id, "episode_id")
        if not isinstance(self.max_parallel_runs, int) or self.max_parallel_runs <= 0:
            raise SchedulerError("max_parallel_runs must be positive")
        if not isinstance(self.max_actions, int) or self.max_actions <= 0:
            raise SchedulerError("max_actions must be positive")
        if not isinstance(self.max_seconds, (int, float)) or self.max_seconds <= 0:
            raise SchedulerError("max_seconds must be positive")
        if not isinstance(self.max_output_bytes, int) or self.max_output_bytes <= 0:
            raise SchedulerError("max_output_bytes must be positive")
        if self.policy not in {"FAIL_FAST", "CONTINUE_INDEPENDENT"}:
            raise SchedulerError("unknown scheduler policy")
        for executor, limit in self.executor_concurrency.items():
            _id(executor, "executor_id")
            if not isinstance(limit, int) or limit <= 0:
                raise SchedulerError("executor concurrency limits must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEDULER_SCHEMA,
            "episode_id": self.episode_id,
            "max_parallel_runs": self.max_parallel_runs,
            "executor_concurrency": dict(self.executor_concurrency),
            "max_actions": self.max_actions,
            "max_seconds": self.max_seconds,
            "max_output_bytes": self.max_output_bytes,
            "policy": self.policy,
        }


class CancellationToken:
    """Cooperative cancellation boundary for offline workers."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise SchedulerError("worker observed cancellation")


class ConcurrentScheduler:
    """Run a validated DAG with bounded real thread concurrency."""

    def __init__(
        self,
        state_dir: str | Path,
        *,
        ledger: EventLedger | None = None,
        arbiter: ResourceArbiter | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "scheduler-state.json"
        self.ledger = ledger or EventLedger(self.state_dir / "events.jsonl")
        self.arbiter = arbiter or ResourceArbiter(self.state_dir / "resources.json", clock=clock)
        self.clock = clock or time.time
        self._event_sequence = 0

    def _validate_graph(self, units: Sequence[WorkUnit]) -> dict[str, WorkUnit]:
        by_id = {unit.run_id: unit for unit in units}
        if len(by_id) != len(units) or not units:
            raise SchedulerError("work-unit ids must be unique and non-empty")
        for unit in units:
            unknown = sorted(set(unit.depends_on) - set(by_id))
            if unknown:
                raise SchedulerError(f"unknown dependencies for {unit.run_id}: {unknown}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(run_id: str) -> None:
            if run_id in visiting:
                raise SchedulerError("work-unit graph contains a cycle")
            if run_id in visited:
                return
            visiting.add(run_id)
            for dependency in by_id[run_id].depends_on:
                visit(dependency)
            visiting.remove(run_id)
            visited.add(run_id)

        for run_id in sorted(by_id):
            visit(run_id)
        return by_id

    def _emit(self, aggregate_id: str, event_type: str, payload: Mapping[str, Any]) -> None:
        self._event_sequence += 1
        self.ledger.append_event(
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=dict(payload),
            event_id=f"scheduler-event-{self._event_sequence:06d}",
            idempotency_key=f"scheduler-idem-{self._event_sequence:06d}",
            actor_ref="os-scheduler-r1",
            occurred_at=utc_now(),
        )

    def _persist(self, spec: SchedulerSpec, units: Mapping[str, WorkUnit], state: Mapping[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        _atomic_json(self.state_path, {"schema": SCHEDULER_SCHEMA, "spec": spec.to_dict(), "units": {key: value.to_dict() for key, value in units.items()}, "state": state})

    def _initial_state(self, units: Mapping[str, WorkUnit]) -> dict[str, Any]:
        return {
            "episode_id": None,
            "phase": "RUN",
            "terminal": None,
            "started_at_epoch": self.clock(),
            "children": {
                run_id: {
                    "run_id": run_id,
                    "status": "PENDING",
                    "attempt": 0,
                    "retry_count": 0,
                    "terminal_summary": None,
                    "blocked_reason": None,
                    "executor_id": unit.executor_id,
                    "history": [],
                }
                for run_id, unit in units.items()
            },
            "budget_usage": {"actions": 0, "elapsed_seconds": 0.0, "output_bytes": 0},
            "dispatch_order": [],
            "max_concurrent_observed": 0,
        }

    def _ready(self, unit: WorkUnit, state: Mapping[str, Any]) -> bool:
        children = state["children"]
        return children[unit.run_id]["status"] in {"PENDING", "READY"} and all(children[item]["status"] == "COMPLETED_VALIDATED" for item in unit.depends_on)

    def _dependency_block(self, unit: WorkUnit, state: dict[str, Any]) -> None:
        children = state["children"]
        failed = [dependency for dependency in unit.depends_on if children[dependency]["status"] in {"FAILED", "BLOCKED_DEPENDENCY", "CANCELLED_BEFORE_DISPATCH", "REQUIRES_RECONCILIATION"}]
        if failed and children[unit.run_id]["status"] in {"PENDING", "READY"}:
            children[unit.run_id].update(status="BLOCKED_DEPENDENCY", blocked_reason=f"prerequisite not validated: {', '.join(failed)}", terminal_summary="dependency did not reach COMPLETED_VALIDATED")

    def _rollup(self, state: dict[str, Any], spec: SchedulerSpec) -> None:
        statuses = [item["status"] for item in state["children"].values()]
        if any(status == "CHECKPOINTED_RESUMABLE" for status in statuses):
            terminal = "CHECKPOINTED_RESUMABLE"
        elif any(status == "BLOCKED_POLICY" for status in statuses):
            terminal = "BLOCKED_POLICY"
        elif any(status == "BLOCKED_NO_EXECUTOR" for status in statuses):
            terminal = "BLOCKED_NO_EXECUTOR"
        elif any(status == "BLOCKED_RESOURCE_CONFLICT" for status in statuses):
            terminal = "BLOCKED_RESOURCE_CONFLICT"
        elif any(status == "BLOCKED_DEPENDENCY" for status in statuses):
            terminal = "COMPLETED_WITH_DEPENDENCY_BLOCKS"
        elif any(status in {"CANCELLED_BEFORE_DISPATCH", "EXPIRED_BEFORE_DISPATCH"} for status in statuses):
            terminal = "COMPLETED_WITH_CANCELLATIONS"
        elif any(status in {"FAILED", "CANCEL_REQUESTED_REQUIRES_RECONCILIATION", "REQUIRES_RECONCILIATION"} for status in statuses):
            terminal = "FAILED_FAST" if spec.policy == "FAIL_FAST" else "COMPLETED_WITH_INDEPENDENT_FAILURES"
        elif all(status == "COMPLETED_VALIDATED" for status in statuses):
            terminal = "COMPLETED_VALIDATED"
        else:
            return
        state["phase"] = "STOP"
        state["terminal"] = {"state": terminal, "summary": f"bounded scheduler stopped with child states: {', '.join(sorted(set(statuses)))}", "recorded_at": utc_now()}

    def run(
        self,
        spec: SchedulerSpec,
        units: Sequence[WorkUnit],
        worker: Callable[[WorkUnit, CancellationToken], WorkResult | Mapping[str, Any]],
        *,
        policy_check: Callable[[WorkUnit], bool] | None = None,
        cancel_runs: Sequence[str] = (),
        resume: bool = False,
    ) -> dict[str, Any]:
        by_id = self._validate_graph(units)
        if not callable(worker):
            raise SchedulerError("worker must be callable")
        cancelled = set(cancel_runs)
        if not cancelled.issubset(by_id):
            raise SchedulerError("cancel_runs contains an unknown run")
        if resume and self.state_path.exists():
            try:
                stored = json.loads(self.state_path.read_text(encoding="utf-8"))
                if stored.get("schema") != SCHEDULER_SCHEMA or stored.get("spec", {}).get("episode_id") != spec.episode_id:
                    raise SchedulerCorruptionError("scheduler recovery identity mismatch")
                state = stored["state"]
                if set(state.get("children", {})) != set(by_id):
                    raise SchedulerCorruptionError("scheduler recovery work-unit set mismatch")
                self._event_sequence = int(self.ledger.audit().get("event_count", 0))
                state["terminal"] = None
                state["phase"] = "RUN"
                for child in state["children"].values():
                    if child["status"] == "CHECKPOINTED_RESUMABLE":
                        child["status"] = "PENDING"
                        child["blocked_reason"] = "explicit resume requested"
            except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
                raise SchedulerCorruptionError("scheduler state is unreadable") from exc
        else:
            state = self._initial_state(by_id)
            state["episode_id"] = spec.episode_id
            self._emit(spec.episode_id, "EPISODE_CREATED", {"status": "CREATED", "state_patch": {"max_parallel_runs": spec.max_parallel_runs}})
            for run_id in sorted(by_id):
                self._emit(run_id, "RUN_READY", {"status": "PENDING"})
        futures: dict[Future[WorkResult], tuple[WorkUnit, tuple[IntentLease, ...], CancellationToken]] = {}
        active_by_executor: dict[str, int] = {}
        executor = ThreadPoolExecutor(max_workers=spec.max_parallel_runs, thread_name_prefix="ignition-r2")
        try:
            while state["terminal"] is None:
                now = self.clock()
                state["budget_usage"]["elapsed_seconds"] = max(0.0, now - float(state["started_at_epoch"]))
                if state["budget_usage"]["elapsed_seconds"] > spec.max_seconds:
                    for item in state["children"].values():
                        if item["status"] in {"PENDING", "READY"}:
                            item.update(status="EXPIRED_BEFORE_DISPATCH", blocked_reason="episode deadline/budget elapsed")
                    state["terminal"] = {"state": "BUDGET_EXHAUSTED", "summary": "episode time budget expired before all ready runs dispatched", "recorded_at": utc_now()}
                    break
                for unit in by_id.values():
                    self._dependency_block(unit, state)
                ready = [unit for unit in by_id.values() if self._ready(unit, state)]
                ready.sort(key=lambda unit: (-unit.priority, unit.run_id))
                skipped: set[str] = set()
                dispatched = False
                while len(futures) < spec.max_parallel_runs and ready:
                    selected: WorkUnit | None = None
                    for unit in ready:
                        child = state["children"][unit.run_id]
                        if unit.run_id in skipped:
                            continue
                        if unit.run_id in cancelled:
                            child.update(status="CANCELLED_BEFORE_DISPATCH", terminal_summary="cancel was requested before dispatch")
                            self._emit(unit.run_id, "CANCELLATION_REQUESTED", {"status": "CANCELLED_BEFORE_DISPATCH"})
                            skipped.add(unit.run_id)
                            continue
                        if unit.deadline_epoch is not None and now >= unit.deadline_epoch:
                            child.update(status="EXPIRED_BEFORE_DISPATCH", terminal_summary="deadline expired before dispatch")
                            self._emit(unit.run_id, "DEADLINE_EXPIRED", {"status": "EXPIRED_BEFORE_DISPATCH"})
                            skipped.add(unit.run_id)
                            continue
                        if policy_check is not None and not policy_check(unit):
                            child.update(status="BLOCKED_POLICY", blocked_reason="effective policy check denied dispatch", terminal_summary="policy denied dispatch")
                            self._emit(unit.run_id, "ROUTE_REJECTED", {"status": "BLOCKED_POLICY"})
                            skipped.add(unit.run_id)
                            continue
                        limit = spec.executor_concurrency.get(unit.executor_id)
                        if limit is None:
                            child.update(status="BLOCKED_NO_EXECUTOR", blocked_reason=f"no concurrency lease for executor {unit.executor_id}", terminal_summary="no executor slot is available")
                            self._emit(unit.run_id, "ROUTE_REJECTED", {"status": "BLOCKED_NO_EXECUTOR"})
                            skipped.add(unit.run_id)
                            continue
                        if active_by_executor.get(unit.executor_id, 0) >= limit:
                            skipped.add(unit.run_id)
                            continue
                        if state["budget_usage"]["actions"] + unit.action_cost > spec.max_actions:
                            child.update(status="BUDGET_BLOCKED", blocked_reason="global action budget prevents dispatch", terminal_summary="budget prevented dispatch")
                            skipped.add(unit.run_id)
                            continue
                        try:
                            leases = self.arbiter.acquire_many(unit.resource_intents, now=now)
                        except ResourceConflict as conflict:
                            child.update(status="READY", blocked_reason=conflict.reason, terminal_summary="resource intent is waiting for a compatible lease")
                            skipped.add(unit.run_id)
                            continue
                        selected = unit
                        ready = [candidate for candidate in ready if candidate.run_id != unit.run_id]
                        break
                    if selected is None:
                        break
                    unit = selected
                    token = CancellationToken()
                    state["children"][unit.run_id].update(status="RUNNING", blocked_reason=None, attempt=state["children"][unit.run_id]["attempt"] + 1)
                    state["dispatch_order"].append(unit.run_id)
                    state["budget_usage"]["actions"] += unit.action_cost
                    active_by_executor[unit.executor_id] = active_by_executor.get(unit.executor_id, 0) + 1
                    self._emit(unit.run_id, "RUN_LEASED", {"status": "LEASED", "executor_id": unit.executor_id})
                    self._emit(unit.run_id, "RUN_STARTED", {"status": "RUNNING", "executor_id": unit.executor_id})
                    future = executor.submit(worker, unit, token)
                    futures[future] = (unit, leases, token)
                    state["max_concurrent_observed"] = max(state["max_concurrent_observed"], len(futures))
                    dispatched = True
                self._persist(spec, by_id, state)
                if futures:
                    done, _ = wait(tuple(futures), return_when=FIRST_COMPLETED)
                    for future in done:
                        unit, leases, token = futures.pop(future)
                        try:
                            result = WorkResult.from_value(future.result())
                        except Exception as exc:
                            result = WorkResult(status="FAILED", summary=f"worker failed closed: {type(exc).__name__}")
                        finally:
                            for lease in leases:
                                self.arbiter.release(lease.lease_id)
                            active_by_executor[unit.executor_id] = max(0, active_by_executor.get(unit.executor_id, 1) - 1)
                        child = state["children"][unit.run_id]
                        child["history"].append({"attempt": child["attempt"], "status": result.status, "summary": result.summary, "recorded_at": utc_now()})
                        child["terminal_summary"] = result.summary
                        state["budget_usage"]["output_bytes"] += result.output_bytes
                        if state["budget_usage"]["output_bytes"] > spec.max_output_bytes:
                            child["status"] = "FAILED"
                            child["blocked_reason"] = "global output budget exceeded"
                            result = WorkResult(status="FAILED", summary="global output budget exceeded", output_bytes=0)
                        elif result.status == "FAILED" and child["retry_count"] < unit.retry_limit:
                            child["retry_count"] += 1
                            child["status"] = "PENDING"
                            child["terminal_summary"] = f"bounded retry {child['retry_count']} scheduled after failure"
                        elif result.status == "CANCELLED":
                            child["status"] = "CANCEL_REQUESTED_REQUIRES_RECONCILIATION"
                        elif result.status == "CHECKPOINTED_RESUMABLE":
                            child["status"] = "CHECKPOINTED_RESUMABLE"
                        elif result.status == "COMPLETED_VALIDATED":
                            child["status"] = "COMPLETED_VALIDATED"
                        else:
                            child["status"] = result.status
                        event_type = "RUN_TERMINAL" if child["status"] in WORKER_TERMINAL else "RUN_CHECKPOINTED"
                        self._emit(unit.run_id, event_type, {"status": child["status"], "summary": child["terminal_summary"]})
                        if child["status"] == "CHECKPOINTED_RESUMABLE":
                            state["terminal"] = {"state": "CHECKPOINTED_RESUMABLE", "summary": "worker checkpoint requires an explicit resume", "recorded_at": utc_now()}
                        if child["status"] in {"FAILED", "CANCEL_REQUESTED_REQUIRES_RECONCILIATION", "REQUIRES_RECONCILIATION"} and spec.policy == "FAIL_FAST":
                            for remaining in state["children"].values():
                                if remaining["status"] in {"PENDING", "READY"}:
                                    remaining["status"] = "BLOCKED_DEPENDENCY"
                            state["terminal"] = {"state": "FAILED_FAST", "summary": f"child {unit.run_id} failed under fail-fast policy", "recorded_at": utc_now()}
                            break
                elif not dispatched:
                    unresolved = [item for item in state["children"].values() if item["status"] in {"PENDING", "READY", "BUDGET_BLOCKED"}]
                    if unresolved:
                        if any(item["status"] == "BUDGET_BLOCKED" for item in unresolved):
                            state["terminal"] = {"state": "BUDGET_EXHAUSTED", "summary": "global action budget prevents remaining ready runs", "recorded_at": utc_now()}
                        elif any(item.get("blocked_reason") == "RESOURCE_CONFLICT" for item in unresolved):
                            state["terminal"] = {"state": "BLOCKED_RESOURCE_CONFLICT", "summary": "no ready run can acquire its declared resource intent", "recorded_at": utc_now()}
                        else:
                            state["terminal"] = {"state": "BLOCKED_NO_EXECUTOR", "summary": "no dispatchable executor slot remains", "recorded_at": utc_now()}
                    else:
                        self._rollup(state, spec)
            if state["terminal"] is None:
                self._rollup(state, spec)
            self._persist(spec, by_id, state)
            self.ledger.snapshot()
            return {"schema": SCHEDULER_SCHEMA, **state, "event_ledger": self.ledger.audit(), "resource_arbiter": self.arbiter.audit()}
        finally:
            executor.shutdown(wait=True)


__all__ = ["CancellationToken", "ConcurrentScheduler", "EPISODE_TERMINAL", "SCHEDULER_SCHEMA", "SchedulerError", "SchedulerSpec", "WorkResult", "WorkUnit"]
