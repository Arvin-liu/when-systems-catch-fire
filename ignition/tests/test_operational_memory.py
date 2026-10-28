from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout

from agent_runtime.cli import main as cli_main
from agent_runtime.memory import MemoryEntry, MemoryStoreError, OperationalMemoryStore


class OperationalMemoryR1Tests(unittest.TestCase):
    def entry(self, memory_id: str, *, memory_type: str = "EPISODIC", summary: str = "bounded run summary", **kwargs: object) -> MemoryEntry:
        tags = kwargs.pop("tags", ("nightshift",))
        return MemoryEntry.create(
            memory_id=memory_id,
            memory_type=memory_type,
            source_run_id="run-1",
            summary=summary,
            provenance_refs=("run-1/trace.jsonl",),
            tags=tags,
            created_at="2026-08-16T00:00:00Z",
            **kwargs,
        )

    def test_append_query_integrity_and_typed_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="operational-memory-") as temp:
            store = OperationalMemoryStore(Path(temp) / "memory.json")
            stored = store.append(self.entry("memory-1", memory_type="PACK_USAGE", owner_feedback_refs=("owner:feedback-1",)))
            self.assertEqual(stored.integrity_sha256, store.show("memory-1").integrity_sha256)
            self.assertEqual([item.memory_id for item in store.query(memory_type="PACK_USAGE", tag="nightshift")], ["memory-1"])
            self.assertEqual(store.audit()["status"], "PASS")

    def test_hidden_prompt_and_secret_material_are_rejected(self) -> None:
        with self.assertRaises(MemoryStoreError):
            self.entry("bad-secret", summary="access_token=should-never-be-stored")
        with self.assertRaises(MemoryStoreError):
            self.entry("bad-prompt", summary="raw prompt text copied from a provider")

    def test_supersede_keeps_lineage_and_active_query_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="operational-memory-") as temp:
            store = OperationalMemoryStore(Path(temp) / "memory.json")
            store.append(self.entry("memory-1", memory_type="PROCEDURAL"))
            replacement = self.entry("memory-2", memory_type="PROCEDURAL", summary="new bounded procedure", supersedes="memory-1")
            store.supersede("memory-1", replacement)
            self.assertEqual([item.memory_id for item in store.query()], ["memory-2"])
            self.assertEqual(store.show("memory-1").supersession_state, "SUPERSEDED")
            self.assertEqual(len(store.query(active_only=False)), 2)

    def test_forget_redacts_body_and_keeps_tombstone_audit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="operational-memory-") as temp:
            path = Path(temp) / "memory.json"
            store = OperationalMemoryStore(path)
            store.append(self.entry("memory-1", summary="bounded failure summary", owner_feedback_refs=("owner:feedback-1",)))
            result = store.forget("memory-1", reason="owner requested removal")
            self.assertEqual(result["status"], "FORGOTTEN")
            redacted = store.show("memory-1")
            self.assertEqual(redacted.summary, "[REDACTED_OPERATIONAL_MEMORY]")
            self.assertEqual(redacted.provenance_refs, ())
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(raw["tombstones"]), 1)
            self.assertNotIn("bounded failure summary", path.read_text(encoding="utf-8"))

    def test_expiry_and_bounded_context_capsule(self) -> None:
        with tempfile.TemporaryDirectory(prefix="operational-memory-") as temp:
            store = OperationalMemoryStore(Path(temp) / "memory.json")
            store.append(self.entry("memory-1", expires_at="2026-08-15T00:00:00Z"))
            expired = store.expire(now="2026-08-16T00:00:00Z")
            self.assertEqual(expired[0]["status"], "EXPIRED")
            store.append(self.entry("memory-2", summary="a" * 500, tags=("capsule",)))
            capsule = store.export_capsule(max_entries=1, max_chars=500, tags=("capsule",))
            self.assertTrue(capsule["bounded"])
            self.assertLessEqual(capsule["entry_count"], 1)
            self.assertIn("not knowledge truth", capsule["claim_ceiling"])

    def test_cli_memory_add_query_export_and_forget(self) -> None:
        with tempfile.TemporaryDirectory(prefix="operational-memory-cli-") as temp:
            store_path = str(Path(temp) / "memory.json")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(cli_main([
                    "memory", "add", "--store", store_path, "--memory-id", "memory-cli",
                    "--memory-type", "APPROVAL", "--source-run-id", "run-cli",
                    "--summary", "approval was explicitly denied", "--tag", "approval", "--json",
                ]), 0)
            self.assertEqual(json.loads(output.getvalue())["memory_id"], "memory-cli")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(cli_main(["memory", "query", "--store", store_path, "--tag", "approval", "--json"]), 0)
            self.assertEqual(len(json.loads(output.getvalue())), 1)
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(cli_main(["memory", "export", "--store", store_path, "--max-entries", "1", "--json"]), 0)
            self.assertTrue(json.loads(output.getvalue())["bounded"])
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(cli_main(["memory", "forget", "--store", store_path, "--memory-id", "memory-cli", "--json"]), 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "FORGOTTEN")


if __name__ == "__main__":
    unittest.main()
