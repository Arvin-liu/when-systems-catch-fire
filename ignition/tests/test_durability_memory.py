from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_runtime.durable_memory import DurableMemoryError, DurableMemoryRecord, DurableOperationalMemoryStore, MemoryNamespaceDenied, MemorySnapshotIntegrityError


class DurabilityMemoryTests(unittest.TestCase):
    def record(self, memory_id: str, namespace: str = "namespace-a", *, semantic: str | None = None) -> DurableMemoryRecord:
        return DurableMemoryRecord.create(memory_id=memory_id, namespace_id=namespace, memory_scope=f"scope-{namespace}", semantic_key=semantic or memory_id, source_event_ref=f"event-{memory_id}", source_run_id=f"run-{namespace}", summary=f"bounded operational summary {memory_id}", tags=("fixture",), provenance_refs=(f"receipt-{memory_id}",), created_at="2026-08-20T00:00:00Z")

    def test_append_supersede_expire_forget_and_tombstone_replay(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durable-memory-") as temp:
            store = DurableOperationalMemoryStore(Path(temp) / "memory.jsonl")
            store.append(self.record("memory-a"), occurred_at=1)
            replacement = DurableMemoryRecord.create(memory_id="memory-b", namespace_id="namespace-a", memory_scope="scope-namespace-a", semantic_key="memory-a", source_event_ref="event-memory-b", source_run_id="run-namespace-a", summary="bounded operational summary memory-b", tags=("fixture",), provenance_refs=("receipt-memory-b",), created_at="2026-08-20T00:00:00Z", supersedes="memory-a")
            store.supersede("memory-a", replacement, namespace_id="namespace-a", occurred_at=2)
            store.expire("memory-b", namespace_id="namespace-a", occurred_at=3)
            store.append(self.record("memory-c"), occurred_at=4)
            store.forget("memory-c", namespace_id="namespace-a", occurred_at=5)
            store.append(self.record("memory-d"), occurred_at=6)
            store.tombstone("memory-d", namespace_id="namespace-a", occurred_at=7)
            replay = store.replay()
            self.assertEqual(replay["records"]["memory-a"].state, "SUPERSEDED")
            self.assertEqual(replay["records"]["memory-b"].state, "EXPIRED")
            self.assertEqual(replay["records"]["memory-c"].state, "FORGOTTEN")
            self.assertEqual(replay["records"]["memory-d"].state, "TOMBSTONED")
            self.assertEqual(len(store.events()), 7)

    def test_cross_namespace_query_and_mutation_are_denied(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durable-memory-") as temp:
            store = DurableOperationalMemoryStore(Path(temp) / "memory.jsonl")
            store.append(self.record("memory-a", "namespace-a"), occurred_at=1)
            self.assertEqual(store.query(namespace_id="namespace-b"), [])
            with self.assertRaises(MemoryNamespaceDenied):
                store.expire("memory-a", namespace_id="namespace-b", occurred_at=2)

    def test_hidden_content_is_rejected_and_soft_context_stays_pointer_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durable-memory-") as temp:
            store = DurableOperationalMemoryStore(Path(temp) / "memory.jsonl")
            with self.assertRaises(DurableMemoryError):
                store.append(self.record("memory-safe").__class__.create(memory_id="memory-hidden", namespace_id="namespace-a", memory_scope="scope-a", semantic_key="hidden", source_event_ref="event-hidden", source_run_id="run-a", summary="contains hidden reasoning"), occurred_at=1)
            pointer = store.expose_soft_context(pointer_ref="soft-ref-a", source_namespace_id="namespace-a", target_namespace_id="namespace-b", occurred_at=2)
            self.assertEqual(pointer["status"], "ADVISORY_ONLY")
            self.assertEqual(store.replay()["records"], {})
            self.assertEqual(store.replay()["soft_context_exposures"][0]["claim_ceiling"], "SOFT_CONTEXT_POINTER_NOT_TRUTH_OR_AUTHORITY")

    def test_partial_event_and_tampered_snapshot_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="durable-memory-") as temp:
            path = Path(temp) / "memory.jsonl"
            store = DurableOperationalMemoryStore(path)
            store.append(self.record("memory-a"), occurred_at=1)
            with path.open("a", encoding="utf-8") as handle:
                handle.write("{\"partial\":true")
            with self.assertRaises(DurableMemoryError):
                store.replay()

            clean_path = Path(temp) / "clean.jsonl"
            clean = DurableOperationalMemoryStore(clean_path)
            clean.append(self.record("memory-a"), occurred_at=1)
            snapshot = clean.snapshot(namespace_id="namespace-a", persist=False)
            tampered = dict(snapshot)
            tampered["records"] = []
            with self.assertRaises(MemorySnapshotIntegrityError):
                DurableOperationalMemoryStore.restore_snapshot(tampered, namespace_id="namespace-a")
            restored = DurableOperationalMemoryStore.restore_snapshot(snapshot, namespace_id="namespace-a")
            self.assertEqual(restored["records"][0].memory_id, "memory-a")


if __name__ == "__main__":
    unittest.main()
