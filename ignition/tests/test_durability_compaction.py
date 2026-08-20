from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.durability import CompactionPolicy, DurabilityCompactor, SnapshotChainStore
from agent_runtime.event_ledger import EventLedger


class DurabilityCompactionTests(unittest.TestCase):
    def test_lineage_is_unchanged_and_multiple_snapshot_chain_replays(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durability-compaction-") as temp:
            root = Path(temp)
            ledger = EventLedger(root / "events.jsonl")
            ledger.append_event(aggregate_id="episode", event_type="EPISODE_CREATED", payload={"status": "CREATED"}, idempotency_key="compact-1")
            chain = SnapshotChainStore(root / "snapshots")
            compactor = DurabilityCompactor(chain)
            first, receipt = compactor.compact(ledger, compaction_id="compact-a", snapshot_id="snap-a", outstanding_reconciliation_refs=("reconcile-uncertain",), external_pointer_digests=("a" * 64,), derived_cache_entries=("c1", "c2", "c3"), advisory_artifacts=("a1", "a2", "a3"))
            self.assertTrue(receipt.event_lineage_preserved)
            self.assertEqual(receipt.derived_cache_prune_candidates, 1)
            self.assertEqual(receipt.advisory_artifact_prune_candidates, 1)
            before = [event.event_hash for event in ledger.events()]
            ledger.append_event(aggregate_id="episode", event_type="RUN_STARTED", payload={"status": "RUNNING"}, expected_version=1, idempotency_key="compact-2")
            second, _ = compactor.compact(ledger, compaction_id="compact-b", snapshot_id="snap-b", policy=CompactionPolicy(snapshot_interval_events=1))
            after = [event.event_hash for event in ledger.events()]
            self.assertEqual(after[:len(before)], before)
            self.assertEqual(second.ledger_end_sequence, 2)
            restored, selected, _ = chain.restore_with_fallback(ledger)
            self.assertEqual(selected.snapshot_id, "snap-b")
            self.assertEqual(restored, ledger.replay())

    def test_tampered_latest_snapshot_falls_back_to_old_prefix(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durability-compaction-") as temp:
            root = Path(temp)
            ledger = EventLedger(root / "events.jsonl")
            ledger.append_event(aggregate_id="episode", event_type="EPISODE_CREATED", payload={"status": "CREATED"}, idempotency_key="fallback-1")
            chain = SnapshotChainStore(root / "snapshots")
            compactor = DurabilityCompactor(chain)
            compactor.compact(ledger, compaction_id="fallback-a", snapshot_id="snap-old")
            ledger.append_event(aggregate_id="episode", event_type="RUN_STARTED", payload={"status": "RUNNING"}, expected_version=1, idempotency_key="fallback-2")
            compactor.compact(ledger, compaction_id="fallback-b", snapshot_id="snap-new")
            latest = root / "snapshots/snap-new.json"
            raw = latest.read_text(encoding="utf-8").replace('"captured_head_hash":', '"captured_head_hash": "' + '0' * 64 + '", "ignored":')
            latest.write_text(raw, encoding="utf-8")
            restored, selected, _ = chain.restore_with_fallback(ledger)
            self.assertEqual(selected.snapshot_id, "snap-old")
            self.assertEqual(restored, ledger.replay())

    def test_policy_rejects_lineage_deletion(self) -> None:
        with self.assertRaises(Exception):
            CompactionPolicy(preserve_event_lineage=False)


if __name__ == "__main__":
    unittest.main()
