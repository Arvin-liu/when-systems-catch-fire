from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from agent_federation.live_attempt_ledger import LiveAttemptLedger
from agent_federation.live_current_projection import build_live_current_projection
from agent_federation.live_reconciliation import derive_reconciliation_state
from agent_federation.live_reconciliation_events import LiveReconciliationEventError, LiveReconciliationEventDuplicateError, LiveReconciliationEventLedger


class LiveReconciliationEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.ledger_path = self.root / "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl"
        self.records = LiveAttemptLedger(self.ledger_path).records()

    def make_event(self, index: int, observation: str, recovery: str, reason: str) -> dict:
        record = self.records[index]
        state = derive_reconciliation_state({
            "task_id": record["task_id"],
            "attempt_id": record["attempt_id"],
            "prior_record_hash": record["record_hash"],
            "prior_process_state": record["process"]["state"],
            "process_observation": observation,
            "evidence_recovery_status": recovery,
            "evidence_refs": [f"fixture://reconciliation/{index}"],
            "terminal_reason": reason,
        })
        return {
            "event_type": "RECONCILIATION_STATE_RECORDED",
            "task_id": record["task_id"],
            "dispatch_id": record["dispatch_id"],
            "attempt_id": record["attempt_id"],
            "executor_id": record["executor_id"],
            "prior_record_hash": record["record_hash"],
            "reconciliation_state": state,
            "claim_ceiling": "Canonical reconciliation event only; external effect remains UNKNOWN.",
        }

    def test_event_ledger_is_append_only_and_chain_bound(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reconciliation-events-") as directory:
            ledger = LiveReconciliationEventLedger(Path(directory) / "events.jsonl")
            first = ledger.append(self.make_event(0, "UNKNOWN", "EXHAUSTED", "timeout evidence exhausted"))
            second = ledger.append(self.make_event(3, "LIVE_PROCESS_OBSERVED_OUTCOME_UNKNOWN", "EXHAUSTED", "capture evidence exhausted"))
            self.assertEqual(first["sequence"], 0)
            self.assertEqual(second["sequence"], 1)
            self.assertEqual(second["previous_event_hash"], first["event_hash"])
            self.assertEqual(ledger.audit()["record_count"], 2)
            with self.assertRaises(LiveReconciliationEventDuplicateError):
                ledger.append(self.make_event(0, "UNKNOWN", "EXHAUSTED", "duplicate"))

    def test_projection_consumes_only_exactly_bound_overlay_events(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reconciliation-projection-") as directory:
            event_path = Path(directory) / "events.jsonl"
            ledger = LiveReconciliationEventLedger(event_path)
            ledger.append(self.make_event(0, "UNKNOWN", "EXHAUSTED", "timeout evidence exhausted"))
            ledger.append(self.make_event(3, "LIVE_PROCESS_OBSERVED_OUTCOME_UNKNOWN", "EXHAUSTED", "capture evidence exhausted"))
            ledger.append(self.make_event(4, "NO_LIVE_PROCESS_OBSERVED", "CONCLUSIVE", "zero live dispatch calls"))
            projection = build_live_current_projection(
                self.ledger_path,
                reconciliation_events_path=event_path,
            )
            self.assertEqual(projection["counts"]["total_attempts"], 5)
            self.assertEqual(projection["counts"]["unreconciled_count"], 0)
            self.assertEqual(projection["next_eligible_action"]["action"], "RUN_DYNAMIC_EXECUTOR_ADMISSION")
            self.assertEqual(projection["source_ledger"]["reconciliation_events"]["event_count"], 3)
            statuses = {row["attempt_id"]: row["reconciliation_status"] for row in projection["attempts"]}
            self.assertEqual(statuses["live-hermes-136-initial"], "TERMINAL_UNRECOVERABLE_EFFECT_UNKNOWN")
            self.assertEqual(statuses["attempt-138-live-02"], "TERMINAL_UNRECOVERABLE_OBSERVATION_INCOMPLETE")
            self.assertEqual(statuses["attempt-139-live-02"], "CLOSED_NO_LIVE_DISPATCH")

    def test_event_state_cannot_be_rebound_to_another_record(self) -> None:
        event = self.make_event(0, "UNKNOWN", "EXHAUSTED", "timeout evidence exhausted")
        tampered = copy.deepcopy(event)
        tampered["prior_record_hash"] = self.records[3]["record_hash"]
        with tempfile.TemporaryDirectory(prefix="reconciliation-rebind-") as directory:
            ledger = LiveReconciliationEventLedger(Path(directory) / "events.jsonl")
            with self.assertRaises(LiveReconciliationEventError):
                ledger.append(tampered)


if __name__ == "__main__":
    unittest.main()
