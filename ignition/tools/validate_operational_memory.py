#!/usr/bin/env python3
"""Validate the operational-memory R1 store boundary with an offline fixture."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_runtime.memory import MemoryEntry, MemoryStoreError, OperationalMemoryStore  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="operational-memory-gate-") as temp:
        store = OperationalMemoryStore(Path(temp) / "memory.json")
        entry = store.append(MemoryEntry.create(
            memory_id="gate-memory-1",
            memory_type="PROCEDURAL",
            source_run_id="gate-run-1",
            summary="bounded offline procedure was validated",
            provenance_refs=("gate-run-1/trace.jsonl",),
            tags=("gate",),
            created_at="2026-08-16T00:00:00Z",
        ))
        capsule = store.export_capsule(max_entries=1, max_chars=1000)
        try:
            MemoryEntry.create(memory_id="gate-bad", memory_type="EPISODIC", source_run_id="gate-run-1", summary="raw prompt and access_token")
        except MemoryStoreError:
            rejected = True
        else:
            rejected = False
        result = {
            "status": "PASS" if rejected and capsule["bounded"] and store.show(entry.memory_id).integrity_sha256 == entry.integrity_sha256 else "FAIL",
            "schema": "operational-memory-r1",
            "integrity": store.audit()["status"],
            "capsule_bounded": capsule["bounded"],
            "forbidden_material_rejected": rejected,
            "claim_ceiling": capsule["claim_ceiling"],
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
