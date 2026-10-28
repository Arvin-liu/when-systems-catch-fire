from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.executor_health import ExecutorCapabilityLease, ExecutorHealthError, ExecutorHealthStore


def lease(executor_id: str = "reference-a", *, now: float = 100.0, status: str = "HEALTHY", ttl: float = 10.0) -> ExecutorCapabilityLease:
    return ExecutorCapabilityLease(
        executor_id=executor_id, family="reference", adapter_version="r2-fixture", observed_version="fixture-1",
        capability_tokens=("repo.read", "structured_progress"), permission_ceiling=("repo.read",),
        workspace_modes=("isolated",), supports_progress=True, supports_cancel=True, supports_resume=True,
        supports_handoff=False, max_concurrency=2, status=status, observed_at=now, expires_at=now + ttl,
        probe_kind="OFFLINE_FIXTURE", evidence_refs=(f"evidence-{executor_id}",),
    )


class ExecutorHealthTests(unittest.TestCase):
    def test_expiry_is_stale_and_fresh_observation_restores_route(self) -> None:
        clock = [100.0]
        with tempfile.TemporaryDirectory(prefix="executor-health-") as temp:
            store = ExecutorHealthStore(Path(temp) / "health.json", clock=lambda: clock[0])
            store.observe(lease())
            self.assertTrue(store.usable("reference-a", required_capabilities=("repo.read",), workspace_mode="isolated"))
            clock[0] = 111.0
            self.assertFalse(store.usable("reference-a", required_capabilities=("repo.read",)))
            self.assertEqual(store.get("reference-a").status, "STALE")
            store.observe(lease(now=111.0))
            self.assertTrue(store.usable("reference-a", required_capabilities=("repo.read",)))

    def test_capability_permission_workspace_and_concurrency_ceiling(self) -> None:
        with tempfile.TemporaryDirectory(prefix="executor-health-") as temp:
            store = ExecutorHealthStore(Path(temp) / "health.json", clock=lambda: 100.0)
            store.observe(lease())
            self.assertFalse(store.usable("reference-a", required_capabilities=("repo.write",)))
            self.assertFalse(store.usable("reference-a", required_permissions=("repo.write",)))
            self.assertFalse(store.usable("reference-a", workspace_mode="shared"))
            self.assertFalse(store.usable("reference-a", required_concurrency=3))

    def test_failures_cooldown_and_digest_tamper_fail_closed(self) -> None:
        clock = [100.0]
        with tempfile.TemporaryDirectory(prefix="executor-health-") as temp:
            path = Path(temp) / "health.json"
            store = ExecutorHealthStore(path, clock=lambda: clock[0])
            store.observe(lease())
            degraded = store.record_failure("reference-a", "fixture timeout", cooldown_seconds=1)
            self.assertEqual(degraded.status, "DEGRADED")
            self.assertFalse(store.usable("reference-a"))
            self.assertTrue(store.usable("reference-a", allow_degraded=True, now=102.0))
            store.record_failure("reference-a", "fixture timeout 2", cooldown_seconds=1)
            store.record_failure("reference-a", "fixture timeout 3", cooldown_seconds=1)
            self.assertEqual(store.get("reference-a").status, "UNSAFE_TO_PROBE")
            raw = __import__("json").loads(path.read_text())
            raw["leases"][0]["max_concurrency"] = 99
            path.write_text(__import__("json").dumps(raw))
            with self.assertRaises(ExecutorHealthError):
                store.get("reference-a")


if __name__ == "__main__":
    unittest.main()
