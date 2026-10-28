from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_runtime.event_ledger import (
    DuplicateEventError,
    EventLedger,
    EventLedgerError,
    LedgerCorruptionError,
    SnapshotMismatchError,
    StaleWriterError,
)


class EventLedgerTests(unittest.TestCase):
    def test_cas_chain_duplicate_and_deterministic_replay(self) -> None:
        with tempfile.TemporaryDirectory(prefix="event-ledger-") as temp:
            path = Path(temp) / "events.jsonl"
            ledger = EventLedger(path)
            first = ledger.append_event(
                aggregate_id="episode-1", event_type="EPISODE_CREATED",
                payload={"status": "CREATED", "state_patch": {"policy": "FAIL_FAST"}},
                event_id="event-1", idempotency_key="idem-1", occurred_at="2026-08-17T00:00:00Z",
            )
            ledger.append_event(
                aggregate_id="episode-1", event_type="RUN_READY", expected_version=1,
                payload={"status": "READY", "run_id": "run-1"},
                event_id="event-2", idempotency_key="idem-2", occurred_at="2026-08-17T00:00:01Z",
            )
            with self.assertRaises(StaleWriterError):
                ledger.append_event(aggregate_id="episode-1", event_type="RUN_STARTED", expected_version=0, payload={})
            with self.assertRaises(DuplicateEventError):
                ledger.append_event(aggregate_id="episode-1", event_type="RUN_STARTED", expected_version=2, payload={}, event_id="event-2", idempotency_key="idem-3")
            state_a = ledger.replay()
            state_b = ledger.replay()
            self.assertEqual(state_a, state_b)
            self.assertEqual(state_a["aggregates"]["episode-1"]["version"], 2)
            self.assertEqual(first.previous_event_hash, "0" * 64)
            self.assertEqual(ledger.audit()["status"], "PASS")

    def test_snapshot_tail_replay_and_corrupt_chain_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="event-ledger-snapshot-") as temp:
            path = Path(temp) / "events.jsonl"
            ledger = EventLedger(path)
            ledger.append_event(aggregate_id="run-1", event_type="RUN_READY", payload={"status": "READY"}, event_id="event-1", idempotency_key="idem-1", occurred_at="2026-08-17T00:00:00Z")
            ledger.snapshot()
            ledger.append_event(aggregate_id="run-1", event_type="RUN_STARTED", expected_version=1, payload={"status": "RUNNING"}, event_id="event-2", idempotency_key="idem-2", occurred_at="2026-08-17T00:00:01Z")
            self.assertEqual(ledger.replay_snapshot()["aggregates"]["run-1"]["status"], "RUNNING")
            lines = path.read_text(encoding="utf-8").splitlines()
            broken = json.loads(lines[1])
            broken["previous_event_hash"] = "f" * 64
            path.write_text("\n".join([lines[0], json.dumps(broken, sort_keys=True)]) + "\n", encoding="utf-8")
            with self.assertRaises(LedgerCorruptionError):
                ledger.audit()

    def test_snapshot_mismatch_and_forbidden_public_material(self) -> None:
        with tempfile.TemporaryDirectory(prefix="event-ledger-boundary-") as temp:
            ledger = EventLedger(Path(temp) / "events.jsonl")
            ledger.append_event(aggregate_id="run-1", event_type="RUN_READY", payload={"status": "READY"}, event_id="event-1", idempotency_key="idem-1", occurred_at="2026-08-17T00:00:00Z")
            snapshot = ledger.snapshot()
            snapshot["captured_head_hash"] = "f" * 64
            Path(temp, "bad-snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")
            with self.assertRaises(SnapshotMismatchError):
                ledger.replay_snapshot(Path(temp, "bad-snapshot.json"))
            with self.assertRaises(EventLedgerError):
                ledger.append_event(aggregate_id="run-1", event_type="RUN_STARTED", expected_version=1, payload={"raw_prompt": "private"})


if __name__ == "__main__":
    unittest.main()
