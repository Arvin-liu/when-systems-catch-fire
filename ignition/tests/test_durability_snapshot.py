from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from agent_runtime.durability import CanonicalSnapshot, CanonicalSnapshotStore, SnapshotIntegrityError, SnapshotNamespaceError
from agent_runtime.event_ledger import EventLedger


class DurabilitySnapshotTests(unittest.TestCase):
    def _ledger(self, root: Path) -> EventLedger:
        ledger = EventLedger(root / "events.jsonl")
        ledger.append_event(aggregate_id="episode-a", event_type="EPISODE_CREATED", payload={"status": "CREATED"}, idempotency_key="idem-a")
        ledger.append_event(aggregate_id="run-a", event_type="RUN_STARTED", payload={"status": "RUNNING", "state_patch": {"namespace": "workspace-a"}}, idempotency_key="idem-b")
        return ledger

    def test_snapshot_plus_tail_is_genesis_equivalent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durability-snapshot-") as temp:
            root = Path(temp)
            ledger = self._ledger(root)
            store = CanonicalSnapshotStore(root / "snapshot.json")
            snapshot = store.create(ledger, snapshot_id="snap-001", namespace_scope="workspace-a", active_pack_versions=("knowledge.r0@1",), outstanding_reconciliation_refs=("reconcile-1",), advisory_soft_governance_versions=("esi-r0:ADVISORY_ONLY",))
            store.write(snapshot)
            ledger.append_event(aggregate_id="run-a", event_type="RUN_TERMINAL", payload={"status": "COMPLETED_VALIDATED"}, expected_version=1, idempotency_key="idem-c")
            restored = store.restore(ledger, namespace_scope="workspace-a")
            self.assertEqual(restored, ledger.replay())
            audit = store.audit(ledger, namespace_scope="workspace-a")
            self.assertTrue(audit["replay_equivalent"])
            self.assertEqual(audit["tail_events"], 1)

    def test_tampered_snapshot_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durability-snapshot-") as temp:
            root = Path(temp)
            ledger = self._ledger(root)
            store = CanonicalSnapshotStore(root / "snapshot.json")
            data = store.create(ledger, snapshot_id="snap-002").to_dict()
            data["state"]["tampered"] = True
            with self.assertRaises(SnapshotIntegrityError):
                CanonicalSnapshot.from_dict(data)

    def test_wrong_namespace_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durability-snapshot-") as temp:
            root = Path(temp)
            ledger = self._ledger(root)
            store = CanonicalSnapshotStore(root / "snapshot.json")
            store.write(store.create(ledger, snapshot_id="snap-003", namespace_scope="workspace-a"))
            with self.assertRaises(SnapshotNamespaceError):
                store.restore(ledger, namespace_scope="workspace-b")

    def test_partial_snapshot_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durability-snapshot-") as temp:
            root = Path(temp)
            ledger = self._ledger(root)
            store = CanonicalSnapshotStore(root / "snapshot.json")
            data = store.create(ledger, snapshot_id="snap-004").to_dict()
            del data["event_hash_chain_sha256"]
            store.path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(SnapshotIntegrityError):
                store.read()


if __name__ == "__main__":
    unittest.main()
