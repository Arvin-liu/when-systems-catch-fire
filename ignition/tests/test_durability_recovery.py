from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.durability import CanonicalSnapshotStore, SnapshotChainStore
from agent_runtime.dispatch_reconciliation import DispatchEnvelope, DurableDispatchStore
from agent_runtime.event_ledger import EventLedger
from agent_runtime.recovery import FAULT_POINTS, RECOVERY_PHASES, RecoveryBlocked, RecoveryFaultInjected, RecoveryFaultMatrix, RecoveryOrchestrator


class DurabilityRecoveryTests(unittest.TestCase):
    def make_ledger(self, root: Path) -> tuple[EventLedger, SnapshotChainStore]:
        ledger = EventLedger(root / "events.jsonl")
        ledger.append_event(aggregate_id="episode-a", event_type="EPISODE_CREATED", payload={"status": "CREATED"}, event_id="event-episode-created", idempotency_key="idem-episode-created", occurred_at="2026-08-20T00:00:00Z")
        ledger.append_event(aggregate_id="run-a", event_type="RUN_READY", payload={"status": "PENDING"}, event_id="event-run-ready", idempotency_key="idem-run-ready", occurred_at="2026-08-20T00:00:01Z")
        chain = SnapshotChainStore(root / "snapshots")
        snapshot = CanonicalSnapshotStore(root / "snapshot.json").create(ledger, snapshot_id="snapshot-a", namespace_scope="workspace-a", advisory_soft_governance_versions=("esi-r0:ADVISORY_ONLY",))
        chain.write(snapshot)
        ledger.append_event(aggregate_id="run-a", event_type="RUN_STARTED", payload={"status": "RUNNING"}, event_id="event-run-started", idempotency_key="idem-run-started", occurred_at="2026-08-20T00:00:02Z")
        return ledger, chain

    def test_recovery_runs_all_phases_and_exposes_open_obligation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-") as temp:
            root = Path(temp)
            ledger, chain = self.make_ledger(root)
            dispatch = DurableDispatchStore(root / "dispatch.json")
            dispatch.create(DispatchEnvelope("dispatch-a", "task-a", "executor-a", "idempotency-a", "a" * 64, "EXTERNAL_SIDE_EFFECT", 1, 30))
            dispatch.mark_sent("dispatch-a")
            dispatch.timeout("dispatch-a", reason="fixture crash after dispatch")
            result = RecoveryOrchestrator(ledger=ledger, snapshot_chain=chain, namespace_scope="workspace-a", namespace_state={"namespace": "workspace-a"}, policy_state={"deny_by_default": True}, pack_state={"active": ["knowledge.r0@1.0.0"]}, dispatch_store=dispatch).run()
            self.assertEqual(tuple(item["name"] for item in result["phases"]), RECOVERY_PHASES)
            self.assertEqual(result["phase_count"], 11)
            self.assertEqual(result["status"], "RECOVERED_WITH_OPEN_OBLIGATIONS")
            self.assertEqual(result["uncertain_dispatch_refs"], ["dispatch-a"])
            self.assertEqual(result["exactly_once"], "NOT_CLAIMED")
            self.assertEqual(result["delivery_semantics"], "AT_LEAST_ONCE_WITH_IDEMPOTENCY_AND_RECONCILIATION")

    def test_tampered_latest_snapshot_falls_back_to_trusted_prefix(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-") as temp:
            root = Path(temp)
            ledger, chain = self.make_ledger(root)
            second = CanonicalSnapshotStore(root / "snapshot-b.json").create(ledger, snapshot_id="snapshot-b", namespace_scope="workspace-a")
            second_path = chain.write(second)
            second_data = second_path.read_text(encoding="utf-8").replace(second.snapshot_id, "tampered-snapshot")
            second_path.write_text(second_data, encoding="utf-8")
            result = RecoveryOrchestrator(ledger=ledger, snapshot_chain=chain, namespace_scope="workspace-a").run()
            self.assertEqual(result["snapshot"]["id"], "snapshot-a")

    def test_missing_migration_blocks_and_fault_matrix_is_offline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-") as temp:
            root = Path(temp)
            ledger, chain = self.make_ledger(root)
            with self.assertRaises(RecoveryBlocked):
                RecoveryOrchestrator(ledger=ledger, snapshot_chain=chain, namespace_scope="workspace-a", current_schema_epoch="old-epoch", target_schema_epoch="new-epoch").run()
            matrix = RecoveryFaultMatrix.simulate()
            self.assertEqual(set(matrix), set(FAULT_POINTS))
            self.assertTrue(all(item["external_invocation"] == "NOT_RUN" for item in matrix.values()))

    def test_injected_recovery_fault_does_not_change_normal_restart_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="recovery-") as temp:
            root = Path(temp)
            ledger, chain = self.make_ledger(root)
            with self.assertRaises(RecoveryFaultInjected):
                RecoveryOrchestrator(ledger=ledger, snapshot_chain=chain, namespace_scope="workspace-a").run(fault_at="DURING_MEMORY_UPDATE")
            result = RecoveryOrchestrator(ledger=ledger, snapshot_chain=chain, namespace_scope="workspace-a").run()
            self.assertEqual(result["status"], "RECOVERED_LOCAL_CONTINUITY")


if __name__ == "__main__":
    unittest.main()
