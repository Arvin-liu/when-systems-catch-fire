#!/usr/bin/env python3
"""Offline adversarial gate for the OS Control Plane event ledger."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.event_ledger import EventLedger, LedgerCorruptionError, StaleWriterError


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="event-ledger-gate-") as temp:
        path = Path(temp) / "events.jsonl"
        ledger = EventLedger(path)
        ledger.append_event(aggregate_id="gate-episode", event_type="EPISODE_CREATED", payload={"status": "CREATED"}, event_id="gate-event-1", idempotency_key="gate-idem-1", occurred_at="2026-08-17T00:00:00Z")
        try:
            ledger.append_event(aggregate_id="gate-episode", event_type="RUN_READY", expected_version=0, payload={"status": "READY"})
        except StaleWriterError:
            stale_writer = True
        else:
            stale_writer = False
        snapshot = ledger.snapshot()
        ledger.append_event(aggregate_id="gate-episode", event_type="RUN_READY", expected_version=1, payload={"status": "READY"}, event_id="gate-event-2", idempotency_key="gate-idem-2", occurred_at="2026-08-17T00:00:01Z")
        replay = ledger.replay_snapshot()
        lines = path.read_text(encoding="utf-8").splitlines()
        lines[-1] = lines[-1].replace('"previous_event_hash":"', '"previous_event_hash":"' + "f" * 64, 1)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            ledger.audit()
        except LedgerCorruptionError:
            corruption_fail_closed = True
        else:
            corruption_fail_closed = False
        ok = stale_writer and replay["event_count"] == 2 and snapshot["captured_sequence"] == 1 and corruption_fail_closed
        print(f"EVENT_LEDGER_R1={'PASS' if ok else 'FAIL'}")
        print(f"CAS_STALE_WRITER={'REJECTED' if stale_writer else 'NOT_REJECTED'}")
        print(f"SNAPSHOT_TAIL_REPLAY={'PASS' if replay['event_count'] == 2 else 'FAIL'}")
        print(f"CORRUPTED_CHAIN={'FAIL_CLOSED' if corruption_fail_closed else 'ACCEPTED'}")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
