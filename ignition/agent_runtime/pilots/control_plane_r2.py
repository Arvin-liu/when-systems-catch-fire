"""Offline five-child adversarial pilot for OS Control Plane R2."""

from __future__ import annotations

from pathlib import Path
import tempfile
import threading
from typing import Any

from agent_runtime.concurrent_memory import ConcurrentOperationalMemoryStore, MemoryRecord
from agent_runtime.dispatch_reconciliation import DispatchEnvelope, DispatchError, DispatchProgress, DispatchReceipt, DurableDispatchStore
from agent_runtime.driver_console import build_driver_snapshot, render_driver_console
from agent_runtime.executor_health import ExecutorCapabilityLease, ExecutorHealthStore
from agent_runtime.policy_compiler import MonotonicPolicyCompiler
from agent_runtime.queue_control import QueueItem, WorkQueue
from agent_runtime.resource_arbitration import ResourceArbiter, ResourceConflict, ResourceIntent
from agent_runtime.scheduler import ConcurrentScheduler, SchedulerSpec, WorkResult, WorkUnit


class PilotClock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def _intent(intent_id: str, run_id: str, resource: str, kind: str) -> ResourceIntent:
    return ResourceIntent(intent_id, run_id, resource, kind, created_at="2026-08-17T00:00:00Z")


def _unit(run_id: str, resource: str, kind: str, *, priority: int = 0) -> WorkUnit:
    return WorkUnit(run_id=run_id, executor_id="reference", priority=priority, resource_intents=(_intent(f"intent-{run_id}", run_id, resource, kind),))


def _policy() -> dict[str, Any]:
    def source(ref: str, caps: tuple[str, ...] = ("read.files", "write.files")) -> dict[str, Any]:
        return {
            "policy_ref": ref, "allowed_capabilities": list(caps), "allowed_reads": ["workspace/input"],
            "allowed_writes": ["workspace/out/result"], "resource_intents": ["READ_SHARED", "WRITE_EXCLUSIVE"],
            "network_allowed": False, "device_allowed": False, "message_allowed": False,
            "remote_mutation_allowed": False, "approval_requirements": [], "forbidden_effects": [],
            "budget": {"max_actions": 10, "max_seconds": 30, "max_output_bytes": 1000},
            "expires_at": "2026-08-18T00:00:00Z",
        }

    values: dict[str, Any] = {
        "charter": source("charter"), "workspace_policy": source("workspace"), "agent_profile": source("profile"),
        "task_envelope": {**source("task", ("read.files",)), "requested_capabilities": ["read.files"], "requested_reads": ["workspace/input"], "requested_writes": ["workspace/out/result"], "requested_resource_intents": ["READ_SHARED"], "task_id": "pilot-task"},
        "pack_manifest": source("pack"), "executor_ceiling": source("executor"), "episode_budget": {**source("episode"), "budget": {"max_actions": 4, "max_seconds": 12, "max_output_bytes": 400}},
        "approval_state": {}, "route_ref": "reference", "policy_id": "pilot-policy",
    }
    return MonotonicPolicyCompiler().compile(**values).to_dict()


def run_pilot() -> dict[str, Any]:
    """Run only disposable in-process fixtures and return public evidence."""

    clock = PilotClock()
    with tempfile.TemporaryDirectory(prefix="control-plane-r2-pilot-") as temp:
        root = Path(temp)
        queue = WorkQueue(root / "queue.json", max_depth=8, aging_seconds=10, clock=clock)
        for run_id, priority in (("pilot-a", 5), ("pilot-b", 4), ("pilot-c", 3), ("pilot-d", 2), ("pilot-e", 1)):
            queue.enqueue(QueueItem(f"queue-{run_id}", run_id, "pilot-profile", "pilot-project", priority, 100.0, required_capabilities=("repo.read",)))
        cancelled_queue = queue.cancel("queue-pilot-e", reason="adversarial cancel before dispatch")
        queue.enqueue(QueueItem("queue-deadline", "pilot-deadline", "pilot-profile", "pilot-project", 0, 100.0, deadline_epoch=100.0, required_capabilities=("repo.read",)))
        expired_queue = queue.expire(now=100.0)

        health = ExecutorHealthStore(root / "health.json", clock=clock)
        health.observe(ExecutorCapabilityLease("reference", "reference", "r2-fixture", "fixture-1", ("repo.read",), ("repo.read",), ("isolated",), True, True, True, False, 2, "HEALTHY", 100.0, 200.0, "OFFLINE_FIXTURE", evidence_refs=("pilot-reference",)))
        health.observe(ExecutorCapabilityLease("stale-fixture", "fixture", "r2-fixture", "fixture-1", ("repo.read",), ("repo.read",), ("isolated",), True, False, False, False, 1, "HEALTHY", 90.0, 99.0, "OFFLINE_FIXTURE", evidence_refs=("pilot-stale",)))
        route_candidates = health.route_candidates(now=100.0, required_capabilities=("repo.read",), required_permissions=("repo.read",), workspace_mode="isolated")

        main_starts: list[str] = []
        start_barrier = threading.Barrier(2)

        def main_worker(work: WorkUnit, _token: object) -> WorkResult:
            main_starts.append(work.run_id)
            if work.run_id in {"pilot-a", "pilot-b"}:
                start_barrier.wait(timeout=2)
            return WorkResult("COMPLETED_VALIDATED", f"offline child {work.run_id} reached bounded fixture validation")

        main_units = (_unit("pilot-a", "workspace:shared", "READ_SHARED", priority=5), _unit("pilot-b", "workspace:independent", "READ_SHARED", priority=4), _unit("pilot-c", "workspace:shared", "WRITE_EXCLUSIVE", priority=3), _unit("pilot-e", "workspace:cancelled", "READ_SHARED", priority=1))
        main_result = ConcurrentScheduler(root / "main", clock=clock).run(SchedulerSpec("pilot-episode", 2, {"reference": 2}, 8, 10, 10000), main_units, main_worker, cancel_runs=("pilot-e",))

        conflict_arbiter = ResourceArbiter(root / "conflict.json", clock=clock)
        holder = conflict_arbiter.acquire(_intent("holder", "holder", "workspace:adversarial", "WRITE_EXCLUSIVE"), now=100.0)
        try:
            try:
                conflict_arbiter.acquire(_intent("waiter", "waiter", "workspace:adversarial", "WRITE_EXCLUSIVE"), now=100.0)
            except ResourceConflict:
                conflict_observed = True
            else:
                conflict_observed = False
        finally:
            conflict_arbiter.release(holder.lease_id)

        checkpoint_calls = {"count": 0}

        def checkpoint_worker(_work: WorkUnit, _token: object) -> WorkResult:
            checkpoint_calls["count"] += 1
            if checkpoint_calls["count"] == 1:
                return WorkResult("CHECKPOINTED_RESUMABLE", "offline crash boundary persisted checkpoint")
            return WorkResult("COMPLETED_VALIDATED", "offline resume reached bounded validation")

        checkpoint_units = (_unit("pilot-d", "workspace:checkpoint", "WRITE_EXCLUSIVE"),)
        checkpoint_first = ConcurrentScheduler(root / "checkpoint", clock=clock).run(SchedulerSpec("pilot-checkpoint", 1, {"reference": 1}, 3, 10, 1000), checkpoint_units, checkpoint_worker)
        checkpoint_resumed = ConcurrentScheduler(root / "checkpoint", clock=clock).run(SchedulerSpec("pilot-checkpoint", 1, {"reference": 1}, 3, 10, 1000), checkpoint_units, checkpoint_worker, resume=True)

        dispatch = DurableDispatchStore(root / "dispatch.json", clock=clock)
        dispatch_record = dispatch.create(DispatchEnvelope("pilot-external-e", "pilot-e", "reference", "pilot-e-idempotency", "a" * 64, "EXTERNAL_SIDE_EFFECT", 100.0, 5.0))
        dispatch.mark_sent(dispatch_record.dispatch_id)
        dispatch.acknowledge(dispatch_record.dispatch_id, accepted=True, ack_ref="pilot-ack")
        dispatch.append_progress(DispatchProgress(dispatch_record.dispatch_id, dispatch_record.task_id, dispatch_record.executor_id, dispatch_record.idempotency_key, 1, "RUNNING", "offline external fixture running"))
        dispatch_claim = DispatchReceipt(dispatch_record.dispatch_id, dispatch_record.task_id, dispatch_record.executor_id, dispatch_record.idempotency_key, 2, "COMPLETED", "offline executor completion claim", "b" * 64, 103.0)
        dispatch.record_receipt(dispatch_claim)
        receipt_before_validation = dispatch.get(dispatch_record.dispatch_id).state == "RECEIPT_RECORDED"
        forged_receipt_rejected = False
        try:
            DispatchReceipt(dispatch_record.dispatch_id, dispatch_record.task_id, dispatch_record.executor_id, dispatch_record.idempotency_key, 3, "COMPLETED", "tampered receipt", "b" * 64, 103.0, receipt_digest="f" * 64)
        except DispatchError:
            forged_receipt_rejected = True
        dispatch_final = dispatch.validate_receipt(dispatch_record.dispatch_id, validation_ref="pilot-negative-validation", passed=False)

        memory = ConcurrentOperationalMemoryStore(root / "memory.json")
        memory_barrier = threading.Barrier(2)

        def memory_writer(memory_id: str, semantic: str) -> None:
            memory_barrier.wait(timeout=2)
            memory.append(MemoryRecord.create(memory_id=memory_id, semantic_key=semantic, event_ref=f"event-{memory_id}", source_run_id="pilot-memory", summary=f"bounded operational {memory_id}", tags=("pilot",), created_at="2026-08-17T00:00:00Z"))

        writers = (threading.Thread(target=memory_writer, args=("memory-a", "pilot-a")), threading.Thread(target=memory_writer, args=("memory-b", "pilot-b")))
        for writer in writers:
            writer.start()
        for writer in writers:
            writer.join(timeout=3)
        capsule = memory.export_capsule(max_entries=2, max_chars=2000)
        memory.append(MemoryRecord.create(memory_id="memory-c", semantic_key="pilot-c", event_ref="event-memory-c", source_run_id="pilot-memory", summary="bounded operational memory c", tags=("pilot",), created_at="2026-08-17T00:00:01Z"))
        memory_stale = memory.capsule_is_stale(capsule)
        memory_projection = memory.compact()

        policy = _policy()
        console_sources = {
            "scheduler": main_result,
            "queue": {**queue.audit()},
            "health": health.audit(now=100.0),
            "resources": conflict_arbiter.audit(),
            "dispatch": dispatch.audit(),
            "memory": {**memory.audit(), "capsule_stale": memory_stale},
            "policy": policy,
        }
        console_snapshot = build_driver_snapshot(console_sources)
        children = {
            "pilot-a": {"status": main_result["children"]["pilot-a"]["status"], "evidence": "actual bounded concurrent worker"},
            "pilot-b": {"status": main_result["children"]["pilot-b"]["status"], "evidence": "actual bounded concurrent worker"},
            "pilot-c": {"status": main_result["children"]["pilot-c"]["status"], "evidence": "conflicting writer waited for resource lease"},
            "pilot-d": {"status": checkpoint_resumed["children"]["pilot-d"]["status"], "evidence": "checkpoint then explicit resume"},
            "pilot-e": {"status": main_result["children"]["pilot-e"]["status"], "evidence": "cancelled before dispatch; forged external claim separately rejected by OS validation"},
        }
        all_children_valid = all(item["status"] in {"COMPLETED_VALIDATED", "CANCELLED_BEFORE_DISPATCH"} for item in children.values())
        passed = all_children_valid and main_result["terminal"]["state"] == "COMPLETED_WITH_CANCELLATIONS" and checkpoint_first["terminal"]["state"] == "CHECKPOINTED_RESUMABLE" and checkpoint_resumed["terminal"]["state"] == "COMPLETED_VALIDATED" and main_result["max_concurrent_observed"] == 2 and conflict_observed and cancelled_queue.state == "CANCELLED_BEFORE_DISPATCH" and bool(expired_queue) and route_candidates and route_candidates[0].executor_id == "reference" and receipt_before_validation and forged_receipt_rejected and dispatch_final.state == "FAILED_VALIDATION" and memory_stale and memory_projection["schema"] == "operational-memory-compaction-r2"
        return {
            "schema": "os-control-plane-r2-pilot-r1", "task_id": "IGNITION-20260817-124", "mode": "OFFLINE_DISPOSABLE_FIXTURES_ONLY", "status": "PASS" if passed else "FAIL",
            "children": children,
            "scheduler": {"terminal": main_result["terminal"], "max_concurrent_observed": main_result["max_concurrent_observed"], "dispatch_order": main_result["dispatch_order"], "checkpoint_first": checkpoint_first["terminal"], "checkpoint_resumed": checkpoint_resumed["terminal"]},
            "queue": {"audit": queue.audit(), "cancelled_before_dispatch": cancelled_queue.state, "expired_count": len(expired_queue)},
            "health": {"audit": health.audit(now=100.0), "route_candidates": [item.executor_id for item in route_candidates], "stale_executor_routed": False},
            "resources": {"audit": conflict_arbiter.audit(), "conflict_observed": conflict_observed},
            "dispatch": {"audit": dispatch.audit(), "receipt_before_validation": receipt_before_validation, "forged_receipt_rejected": forged_receipt_rejected, "final_state": dispatch_final.state},
            "memory": {"audit": memory.audit(), "capsule_stale": memory_stale, "compaction_schema": memory_projection["schema"]},
            "adversarial": {"concurrent_children": main_result["max_concurrent_observed"] == 2, "resource_conflict_fail_closed": conflict_observed, "stale_executor_not_routed": route_candidates[0].executor_id == "reference", "crash_checkpoint_resume": checkpoint_first["terminal"]["state"] == "CHECKPOINTED_RESUMABLE" and checkpoint_resumed["terminal"]["state"] == "COMPLETED_VALIDATED", "cancel_before_dispatch": cancelled_queue.state == "CANCELLED_BEFORE_DISPATCH", "deadline_expired": bool(expired_queue), "forged_completion_not_accepted": forged_receipt_rejected and dispatch_final.state == "FAILED_VALIDATION", "stale_capsule": memory_stale},
            "driver_console": {"snapshot": console_snapshot, "human": render_driver_console(console_snapshot)},
            "claim_ceiling": "Offline evidence of bounded Control Plane coordination only; no live executor, external side-effect success, general Agent capability, truth, Owner acceptance or epistemic acceptance is established.",
        }


__all__ = ["run_pilot"]
