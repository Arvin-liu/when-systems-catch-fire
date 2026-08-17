#!/usr/bin/env python3
"""Offline queue/backpressure/priority/deadline/cancel gate."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.queue_control import QueueAdmissionError, QueueItem, WorkQueue


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="queue-gate-") as temp:
        queue = WorkQueue(Path(temp) / "queue.json", max_depth=2, aging_seconds=10)
        queue.enqueue(QueueItem("q-low", "run-low", "profile", "project", 0, 100.0, required_capabilities=("repo.read",)))
        queue.enqueue(QueueItem("q-high", "run-high", "profile", "project", 10, 100.0, required_capabilities=("repo.read",)))
        try:
            queue.enqueue(QueueItem("q-overflow", "run-overflow", "profile", "project", 1, 100.0, required_capabilities=("repo.read",)))
            backpressure = False
        except QueueAdmissionError as exc:
            backpressure = exc.state == "REJECTED_BACKPRESSURE"
        selected = queue.admit_next(now=100.0)
        priority = selected is not None and selected.queue_id == "q-high"
        dispatched = queue.dispatch(selected.queue_id) if selected is not None else None
        cancel = queue.cancel(dispatched.queue_id).state == "CANCEL_REQUESTED_REQUIRES_RECONCILIATION" if dispatched else False
        passed = priority and cancel and backpressure and queue.audit()["status"] == "PASS"
        print(f"QUEUE_CONTROL_R1={'PASS' if passed else 'FAIL'}")
        print(f"PRIORITY_SELECTION={'PASS' if priority else 'FAIL'}")
        print(f"POST_DISPATCH_CANCEL={'PASS' if cancel else 'FAIL'}")
        print(f"BACKPRESSURE={'PASS' if backpressure else 'FAIL'}")
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
