from __future__ import annotations

from pathlib import Path
import tempfile
import threading
import time
import unittest

from agent_runtime.resource_arbitration import ResourceIntent
from agent_runtime.scheduler import ConcurrentScheduler, SchedulerError, SchedulerSpec, WorkResult, WorkUnit


def unit(run_id: str, resource: str, *, depends_on: tuple[str, ...] = (), executor: str = "reference", kind: str = "WRITE_EXCLUSIVE", priority: int = 0, retry_limit: int = 0) -> WorkUnit:
    return WorkUnit(run_id=run_id, depends_on=depends_on, executor_id=executor, resource_intents=(ResourceIntent(f"intent-{run_id}", run_id, resource, kind, priority=priority, created_at="2026-08-17T00:00:00Z"),), retry_limit=retry_limit)


def spec(*, max_parallel: int = 2, policy: str = "CONTINUE_INDEPENDENT", max_actions: int = 8) -> SchedulerSpec:
    return SchedulerSpec(episode_id="episode-scheduler-test", max_parallel_runs=max_parallel, executor_concurrency={"reference": max_parallel, "external-fixture": 1}, max_actions=max_actions, max_seconds=10, max_output_bytes=10000, policy=policy)


class SchedulerTests(unittest.TestCase):
    def test_two_disjoint_ready_runs_actually_overlap_and_dag_waits(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scheduler-concurrent-") as temp:
            barrier = threading.Barrier(2)
            started: list[str] = []

            def worker(work: WorkUnit, _token: object) -> WorkResult:
                started.append(work.run_id)
                if work.run_id in {"audit-a", "audit-b"}:
                    barrier.wait(timeout=2)
                return WorkResult("COMPLETED_VALIDATED", f"validated {work.run_id}")

            units = (unit("audit-a", "workspace:a"), unit("audit-b", "workspace:b"), unit("repair", "workspace:repair", depends_on=("audit-a", "audit-b")))
            result = ConcurrentScheduler(Path(temp)).run(spec(), units, worker)
            self.assertEqual(result["terminal"]["state"], "COMPLETED_VALIDATED")
            self.assertGreaterEqual(result["max_concurrent_observed"], 2)
            self.assertEqual(set(started[:2]), {"audit-a", "audit-b"})
            self.assertEqual(result["dispatch_order"][-1], "repair")

    def test_conflicting_writes_serialize_and_independent_failure_continues(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scheduler-conflict-") as temp:
            active = 0
            max_active = 0
            lock = threading.Lock()

            def worker(work: WorkUnit, _token: object) -> WorkResult:
                nonlocal active, max_active
                with lock:
                    active += 1
                    max_active = max(max_active, active)
                time.sleep(0.02)
                with lock:
                    active -= 1
                if work.run_id == "bad":
                    return WorkResult("FAILED", "fixture failure")
                return WorkResult("COMPLETED_VALIDATED", "validated")

            units = (unit("bad", "workspace:shared"), unit("conflicting", "workspace:shared"), unit("independent", "workspace:other"))
            result = ConcurrentScheduler(Path(temp)).run(spec(), units, worker)
            self.assertEqual(result["terminal"]["state"], "COMPLETED_WITH_INDEPENDENT_FAILURES")
            self.assertEqual(max_active, 2)
            self.assertNotEqual(result["dispatch_order"].index("bad"), result["dispatch_order"].index("conflicting"))
            self.assertEqual(result["children"]["independent"]["status"], "COMPLETED_VALIDATED")

    def test_policy_budget_cancel_and_restart_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scheduler-stop-") as temp:
            units = (unit("cancelled", "workspace:cancel"), unit("over-budget", "workspace:budget"))
            result = ConcurrentScheduler(Path(temp)).run(spec(max_parallel=1, max_actions=1), units, lambda work, token: WorkResult("COMPLETED_VALIDATED", "validated"), cancel_runs=("cancelled",))
            self.assertIn(result["children"]["cancelled"]["status"], {"CANCELLED_BEFORE_DISPATCH", "COMPLETED_VALIDATED"})
            self.assertIn(result["terminal"]["state"], {"BUDGET_EXHAUSTED", "COMPLETED_VALIDATED", "COMPLETED_WITH_CANCELLATIONS"})

            checkpoint_dir = Path(temp) / "checkpoint"
            calls = {"count": 0}

            def checkpoint_worker(_work: WorkUnit, _token: object) -> WorkResult:
                calls["count"] += 1
                return WorkResult("CHECKPOINTED_RESUMABLE", "checkpoint persisted") if calls["count"] == 1 else WorkResult("COMPLETED_VALIDATED", "resumed and validated")

            checkpoint_units = (unit("checkpoint", "workspace:checkpoint"),)
            first = ConcurrentScheduler(checkpoint_dir).run(spec(max_parallel=1), checkpoint_units, checkpoint_worker)
            self.assertEqual(first["terminal"]["state"], "CHECKPOINTED_RESUMABLE")
            second = ConcurrentScheduler(checkpoint_dir).run(spec(max_parallel=1), checkpoint_units, checkpoint_worker, resume=True)
            self.assertEqual(second["terminal"]["state"], "COMPLETED_VALIDATED")

    def test_cycle_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scheduler-cycle-") as temp:
            with self.assertRaises(SchedulerError):
                ConcurrentScheduler(Path(temp)).run(
                    spec(),
                    (unit("a", "workspace:a", depends_on=("b",)), unit("b", "workspace:b", depends_on=("a",))),
                    lambda _work, _token: WorkResult("COMPLETED_VALIDATED", "validated"),
                )


if __name__ == "__main__":
    unittest.main()
