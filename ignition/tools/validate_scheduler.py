#!/usr/bin/env python3
"""Offline bounded-concurrency and DAG scheduler gate."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.resource_arbitration import ResourceIntent
from agent_runtime.scheduler import ConcurrentScheduler, SchedulerSpec, WorkResult, WorkUnit


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="scheduler-gate-") as temp:
        barrier = threading.Barrier(2)

        def worker(work: WorkUnit, _token: object) -> WorkResult:
            if work.run_id in {"a", "b"}:
                barrier.wait(timeout=2)
            return WorkResult("COMPLETED_VALIDATED", f"offline fixture {work.run_id} validated")

        units = tuple(
            WorkUnit(run_id=run_id, executor_id="reference", resource_intents=(ResourceIntent(f"intent-{run_id}", run_id, resource, "READ_SHARED", created_at="2026-08-17T00:00:00Z"),))
            for run_id, resource in (("a", "workspace:a"), ("b", "workspace:b"))
        )
        result = ConcurrentScheduler(Path(temp)).run(SchedulerSpec("gate-episode", 2, {"reference": 2}, 4, 10, 1000), units, worker)
        passed = result["terminal"]["state"] == "COMPLETED_VALIDATED" and result["max_concurrent_observed"] == 2 and result["event_ledger"]["status"] == "PASS"
        print(f"BOUNDED_CONCURRENT_SCHEDULER_R1={'PASS' if passed else 'FAIL'}")
        print(f"MAX_CONCURRENT_OBSERVED={result['max_concurrent_observed']}")
        print(f"DAG_TERMINAL={result['terminal']['state']}")
        print(f"EVENT_LEDGER={result['event_ledger']['status']}")
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
