from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_runtime.event_ledger import EventLedger
from agent_runtime.steering import SteeringDurabilityAdapter, SteeringState, SteeringValidationError


class SteeringDurabilityTests(unittest.TestCase):
    def state(self, suffix: str = "1") -> SteeringState:
        return SteeringState(intents=({"intent_id": f"intent-{suffix}", "status": "ACTIVE"},), goals=({"goal_id": f"goal-{suffix}", "status": "ACTIVE"},), commitments=({"commitment_id": f"commitment-{suffix}", "status": "ACCEPTED"},), provenance_events=({"event": "OWNER_AUTHORITY_RECORDED"},), unresolved_refs=("reconcile-1",))

    def test_append_snapshot_tail_replay_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = EventLedger(root / "events.jsonl")
            adapter = SteeringDurabilityAdapter()
            first = self.state()
            adapter.append_state(ledger, first, occurred_at="2026-08-21T12:00:00+08:00")
            snapshot = adapter.snapshot(ledger, str(root / "snapshot.json"), snapshot_id="snapshot-1")
            second = self.state("2")
            adapter.append_state(ledger, second, expected_version=1, occurred_at="2026-08-21T12:01:00+08:00")
            self.assertEqual(adapter.replay(ledger).digest(), second.digest())
            self.assertEqual(adapter.restore(ledger, snapshot=snapshot).digest(), second.digest())

    def test_migration_is_explicit_and_does_not_rewrite_lineage(self) -> None:
        result = SteeringDurabilityAdapter().migrate(self.state(), migration_id="migration-1", from_epoch="steering-r1", to_epoch="steering-r2", event_lineage=("event-1",))
        self.assertEqual(result.receipt.status, "DRY_RUN")
        self.assertFalse(result.receipt.events_rewritten)

    def test_private_fields_are_rejected(self) -> None:
        with self.assertRaises(SteeringValidationError):
            SteeringState(intents=({"prompt_body": "forbidden"},))


if __name__ == "__main__":
    unittest.main()
