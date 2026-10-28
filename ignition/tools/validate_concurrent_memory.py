#!/usr/bin/env python3
"""Offline concurrent operational-memory R2 gate."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.concurrent_memory import ConcurrentOperationalMemoryStore, MemoryRecord


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="memory-r2-gate-") as temp:
        store = ConcurrentOperationalMemoryStore(Path(temp) / "memory.json")
        first = store.append(MemoryRecord.create(memory_id="gate-memory-1", semantic_key="gate-semantic", event_ref="gate-event-1", source_run_id="gate-run", summary="bounded concurrent memory fixture", created_at="2026-08-17T00:00:00Z"))
        capsule = store.export_capsule(max_entries=1, max_chars=1000)
        store.supersede(first.memory_id, MemoryRecord.create(memory_id="gate-memory-2", semantic_key="gate-semantic", event_ref="gate-event-2", source_run_id="gate-run", summary="revised bounded concurrent memory fixture", created_at="2026-08-17T00:00:01Z", supersedes="gate-memory-1"), expected_generation=1)
        stale = store.capsule_is_stale(capsule)
        projection = store.compact()
        passed = stale and projection["schema"] == "operational-memory-compaction-r2" and store.audit()["status"] == "PASS"
        print(f"CONCURRENT_OPERATIONAL_MEMORY_R2={'PASS' if passed else 'FAIL'}")
        print(f"CAS_GENERATION={store.audit()['generation']}")
        print(f"STALE_CAPSULE={'PASS' if stale else 'FAIL'}")
        print(f"DETERMINISTIC_COMPACTION={'PASS' if projection['schema'] == 'operational-memory-compaction-r2' else 'FAIL'}")
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
