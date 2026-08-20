from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.executor_admission import ExecutorAdmission, ExecutorAdmissionStore, ExecutorRouteDenied
from agent_runtime.revocation import CapabilityGrant, RevocationStore


class DurabilityExecutorAdmissionTests(unittest.TestCase):
    def record(self, *, grants: tuple[str, ...] = (), expires: float = 200.0) -> ExecutorAdmission:
        return ExecutorAdmission(
            executor_id="fixture.executor",
            adapter_family="fixture-adapter",
            observed_version="fixture-v1",
            conformance_epoch=1,
            declared_capabilities=("repo.read", "structured_progress"),
            permission_ceiling=("repo.read",),
            workspace_support=("LOCAL_FIXTURE",),
            handoff_semantics="OS_CANONICAL_BUNDLE_ONLY",
            recovery_semantics="IDEMPOTENCY_RECONCILIATION",
            health_lease_id="health-fixture-r1",
            health_status="HEALTHY",
            observed_at=100.0,
            health_expires_at=expires,
            privacy_boundary="LOCAL_FIXTURE_ONLY",
            conformance_receipt_ref="fixture/conformance/fixture-r1",
            capability_grant_ids=grants,
        )

    def test_admission_requires_current_epoch_and_routes_only_declared_scope(self) -> None:
        with tempfile.TemporaryDirectory(prefix="executor-admission-") as temp:
            store = ExecutorAdmissionStore(Path(temp) / "admission.json")
            store.admit(self.record(), expected_conformance_epoch=1, now=150)
            selected = store.route("fixture.executor", required_capabilities=("repo.read",), workspace="LOCAL_FIXTURE", observed_version="fixture-v1", conformance_epoch=1, now=150)
            self.assertEqual(selected.executor_id, "fixture.executor")
            with self.assertRaises(ExecutorRouteDenied):
                store.route("fixture.executor", required_capabilities=("repo.write",), now=150)

    def test_version_drift_removes_record_without_rerunning_vendor(self) -> None:
        with tempfile.TemporaryDirectory(prefix="executor-admission-") as temp:
            store = ExecutorAdmissionStore(Path(temp) / "admission.json")
            store.admit(self.record(), expected_conformance_epoch=1, now=150)
            with self.assertRaises(ExecutorRouteDenied):
                store.route("fixture.executor", observed_version="fixture-v2", now=150)
            self.assertEqual(store.get("fixture.executor").status, "REJECTED")
            self.assertEqual(store.routable_ids(now=150), ())

    def test_expired_health_lease_exits_pool(self) -> None:
        with tempfile.TemporaryDirectory(prefix="executor-admission-") as temp:
            store = ExecutorAdmissionStore(Path(temp) / "admission.json")
            store.admit(self.record(expires=200), expected_conformance_epoch=1, now=150)
            with self.assertRaises(ExecutorRouteDenied):
                store.route("fixture.executor", now=200)
            self.assertEqual(store.get("fixture.executor").status, "EXPIRED")

    def test_revoked_capability_exits_pool_and_reference_is_offline_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="executor-admission-") as temp:
            revocations = RevocationStore(Path(temp) / "revocations.jsonl")
            grant = CapabilityGrant("grant-fixture-r1", "principal-fixture", "namespace-fixture", "repo.read", "READ_ONLY", 300, "issuer-os", "a" * 64)
            revocations.register(grant, occurred_at=100)
            store = ExecutorAdmissionStore(Path(temp) / "admission.json")
            store.admit(self.record(grants=(grant.grant_id,)), expected_conformance_epoch=1, now=150)
            revocations.revoke(grant.grant_id, occurred_at=160)
            with self.assertRaises(ExecutorRouteDenied):
                store.route("fixture.executor", revocation_store=revocations, now=160)
            self.assertEqual(store.get("fixture.executor").status, "REVOKED")


if __name__ == "__main__":
    unittest.main()
