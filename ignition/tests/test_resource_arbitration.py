from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.resource_arbitration import DeadlockPreventionError, ResourceArbiter, ResourceConflict, ResourceIntent


def intent(intent_id: str, run_id: str, resource: str, kind: str, *, priority: int = 0, ttl: float = 10.0) -> ResourceIntent:
    return ResourceIntent(intent_id=intent_id, run_id=run_id, resource=resource, intent_type=kind, priority=priority, created_at="2026-08-17T00:00:00Z", ttl_seconds=ttl)


class ResourceArbitrationTests(unittest.TestCase):
    def test_shared_reads_and_conflicting_write_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="resource-arbiter-") as temp:
            arbiter = ResourceArbiter(Path(temp) / "resources.json", clock=lambda: 100.0)
            first = arbiter.acquire(intent("read-1", "run-1", "workspace:src/*", "READ_SHARED"), now=100.0)
            second = arbiter.acquire(intent("read-2", "run-2", "workspace:src/a.py", "READ_SHARED"), now=100.0)
            with self.assertRaises(ResourceConflict) as error:
                arbiter.acquire(intent("write-1", "run-3", "workspace:src/a.py", "WRITE_EXCLUSIVE", priority=2), now=100.0)
            self.assertEqual(error.exception.reason, "RESOURCE_CONFLICT")
            self.assertEqual(len(error.exception.blockers), 2)
            arbiter.release(first.lease_id)
            arbiter.release(second.lease_id)
            granted = arbiter.acquire(intent("write-1", "run-3", "workspace:src/a.py", "WRITE_EXCLUSIVE", priority=2), now=100.0)
            self.assertEqual(granted.status, "ACTIVE")

    def test_atomic_multi_resource_and_deadlock_prevention(self) -> None:
        with tempfile.TemporaryDirectory(prefix="resource-atomic-") as temp:
            arbiter = ResourceArbiter(Path(temp) / "resources.json", clock=lambda: 10.0)
            requests = (intent("a", "run-a", "repository:main", "WRITE_EXCLUSIVE"), intent("b", "run-a", "workspace:out", "WRITE_EXCLUSIVE"))
            leases = arbiter.acquire_many(requests, now=10.0)
            self.assertEqual(len(leases), 2)
            with self.assertRaises(DeadlockPreventionError):
                arbiter.acquire_many(tuple(reversed(requests)), now=10.0)
            with self.assertRaises(ResourceConflict):
                arbiter.acquire_many((intent("d", "run-c", "workspace:new", "WRITE_EXCLUSIVE"), intent("c", "run-c", "workspace:out/file", "WRITE_EXCLUSIVE")), now=10.0)
            self.assertEqual(len(arbiter.active(now=10.0)), 2)

    def test_unknown_side_effect_expiry_and_waiting_order(self) -> None:
        with tempfile.TemporaryDirectory(prefix="resource-unknown-") as temp:
            arbiter = ResourceArbiter(Path(temp) / "resources.json", clock=lambda: 20.0)
            lease = arbiter.acquire(intent("unknown", "run-1", "external:account/channel", "UNKNOWN_SIDE_EFFECT", ttl=2), now=20.0)
            with self.assertRaises(ResourceConflict) as error:
                arbiter.acquire(intent("append", "run-2", "external:account/channel", "APPEND_SHARED", priority=1), now=20.0)
            self.assertEqual(error.exception.reason, "UNKNOWN_SIDE_EFFECT_SERIALIZATION")
            self.assertEqual(arbiter.waiting()[0]["intent_id"], "append")
            expired = arbiter.reap_expired(now=23.0)
            self.assertEqual([item.lease_id for item in expired], [lease.lease_id])
            self.assertEqual(arbiter.acquire(intent("append-2", "run-2", "external:account/channel", "APPEND_SHARED"), now=23.0).status, "ACTIVE")


if __name__ == "__main__":
    unittest.main()
