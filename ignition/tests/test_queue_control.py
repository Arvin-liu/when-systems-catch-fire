from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.queue_control import QueueAdmissionError, QueueItem, QueueNotDispatchable, WorkQueue


def item(queue_id: str, *, priority: int = 0, now: float = 100.0, profile: str = "profile-a", project: str = "project-a", deadline: float | None = None, not_before: float = 0.0) -> QueueItem:
    return QueueItem(queue_id, f"run-{queue_id}", profile, project, priority, now, deadline, not_before, required_capabilities=("repo.read",))


class QueueControlTests(unittest.TestCase):
    def test_priority_fifo_and_aging(self) -> None:
        with tempfile.TemporaryDirectory(prefix="queue-control-") as temp:
            queue = WorkQueue(Path(temp) / "queue.json", max_depth=5, aging_seconds=10, clock=lambda: 100.0)
            queue.enqueue(item("low", priority=0, now=99.0))
            queue.enqueue(item("high", priority=5))
            queue.enqueue(item("high-2", priority=5))
            first = queue.admit_next(now=100.0)
            second = queue.admit_next(now=100.0)
            self.assertEqual(first.queue_id, "high")
            self.assertEqual(second.queue_id, "high-2")
            aged = queue.admit_next(now=100.0)
            self.assertEqual(aged.queue_id, "low")

    def test_backpressure_and_profile_quota_are_durable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="queue-control-") as temp:
            queue = WorkQueue(Path(temp) / "queue.json", max_depth=1)
            queue.enqueue(item("one"))
            with self.assertRaises(QueueAdmissionError) as depth:
                queue.enqueue(item("two"))
            self.assertEqual(depth.exception.state, "REJECTED_BACKPRESSURE")
            quota_queue = WorkQueue(Path(temp) / "quota.json", max_depth=3, profile_limits={"profile-a": 1})
            quota_queue.enqueue(item("quota-one"))
            with self.assertRaises(QueueAdmissionError) as quota:
                quota_queue.enqueue(item("quota-two"))
            self.assertEqual(quota.exception.state, "REJECTED_QUOTA")
            self.assertGreaterEqual(queue.audit()["backpressure_events"], 1)

    def test_cancel_deadline_pause_and_dispatch_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="queue-control-") as temp:
            queue = WorkQueue(Path(temp) / "queue.json", max_depth=5)
            queue.enqueue(item("cancel"))
            self.assertEqual(queue.cancel("cancel").state, "CANCELLED_BEFORE_DISPATCH")
            queue.enqueue(item("expired", deadline=100.0))
            self.assertIsNone(queue.admit_next(now=100.0))
            self.assertEqual(queue.get("expired").state, "EXPIRED_BEFORE_DISPATCH")
            queue.enqueue(item("paused"))
            queue.pause()
            self.assertIsNone(queue.admit_next(now=100.0))
            queue.resume()
            admitted = queue.admit_next(now=100.0)
            self.assertEqual(queue.dispatch(admitted.queue_id).state, "DISPATCHED")
            self.assertEqual(queue.cancel(admitted.queue_id).state, "CANCEL_REQUESTED_REQUIRES_RECONCILIATION")
            with self.assertRaises(QueueNotDispatchable):
                queue.dispatch(admitted.queue_id)


if __name__ == "__main__":
    unittest.main()
