from __future__ import annotations

from pathlib import Path
import tempfile
import threading
import unittest

from agent_runtime.concurrent_memory import ConcurrentOperationalMemoryStore, MemoryCASConflict, MemoryDuplicateConflict, MemoryRecord, MemoryR2Error


def record(memory_id: str, *, semantic: str = "ops-procedure", event: str | None = None, summary: str = "bounded operational summary", supersedes: str | None = None) -> MemoryRecord:
    return MemoryRecord(memory_id=memory_id, semantic_key=semantic, event_ref=event or f"event-{memory_id}", source_run_id="run-memory", summary=summary, tags=("r2",), provenance_refs=(f"trace-{memory_id}",), created_at="2026-08-17T00:00:00Z", supersedes=supersedes)


class ConcurrentMemoryTests(unittest.TestCase):
    def test_concurrent_append_cas_and_duplicate_suppression(self) -> None:
        with tempfile.TemporaryDirectory(prefix="memory-r2-") as temp:
            path = Path(temp) / "memory.json"
            store = ConcurrentOperationalMemoryStore(path)
            barrier = threading.Barrier(2)
            results: list[MemoryRecord] = []

            def append_one(value: MemoryRecord) -> None:
                barrier.wait(timeout=2)
                results.append(store.append(value))

            threads = [threading.Thread(target=append_one, args=(record("memory-a", semantic="ops-a"),)), threading.Thread(target=append_one, args=(record("memory-b", semantic="ops-b"),))]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=3)
            self.assertEqual(len(results), 2)
            self.assertEqual(store.audit()["generation"], 2)
            duplicate = store.append(record("memory-retry", semantic="ops-a", event="event-retry"))
            self.assertEqual(duplicate.memory_id, "memory-a")
            with self.assertRaises(MemoryDuplicateConflict):
                store.append(record("memory-other", semantic="ops-a", event="event-other", summary="different content"))
            with self.assertRaises(MemoryCASConflict):
                store.append(record("memory-c", semantic="ops-c"), expected_generation=0)

    def test_atomic_supersede_tombstone_and_stale_capsule(self) -> None:
        with tempfile.TemporaryDirectory(prefix="memory-r2-") as temp:
            store = ConcurrentOperationalMemoryStore(Path(temp) / "memory.json")
            first = store.append(record("memory-1"))
            capsule = store.export_capsule()
            replacement = store.supersede("memory-1", record("memory-2", event="event-2", summary="revised bounded summary", semantic="ops-procedure", supersedes="memory-1"), expected_generation=1)
            self.assertEqual(store.show(first.memory_id).state, "SUPERSEDED")
            self.assertTrue(store.capsule_is_stale(capsule))
            self.assertEqual(store.tombstone(replacement.memory_id, reason="owner requested removal").state, "TOMBSTONED")
            self.assertEqual(store.query(), [])
            with self.assertRaises(MemoryCASConflict):
                store.tombstone(first.memory_id, reason="stale writer", expected_generation=1)

    def test_compaction_is_deterministic_and_tamper_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="memory-r2-") as temp:
            path = Path(temp) / "memory.json"
            store = ConcurrentOperationalMemoryStore(path)
            store.append(record("memory-1", semantic="ops-a"))
            store.append(record("memory-2", semantic="ops-b"))
            projection_a = store.compact()
            projection_b = store.compact()
            self.assertEqual(projection_a, projection_b)
            raw = __import__("json").loads(path.read_text())
            raw["records"][0]["summary"] = "tampered"
            path.write_text(__import__("json").dumps(raw))
            with self.assertRaises(MemoryR2Error):
                store.audit()


if __name__ == "__main__":
    unittest.main()
