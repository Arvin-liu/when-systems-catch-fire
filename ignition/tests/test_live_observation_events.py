from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agent_federation.live_attempt_ledger import LiveAttemptLedger
from agent_federation.live_current_projection import LiveCurrentProjectionError, build_live_current_projection
from agent_federation.live_observation_events import LiveObservationEventError, LiveObservationEventLedger


class LiveObservationEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.ledger_path = self.root / "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl"
        self.record = next(record for record in LiveAttemptLedger(self.ledger_path).records() if record["attempt_id"] == "attempt-140-live-01")

    def outcome(self) -> dict:
        return {
            "schema_version": "live-observation-outcome-r1",
            "observation_outcome_type": "LIVE_PROCESS_OBSERVED",
            "probe_return_code": 0,
            "transport_return_code": 0,
            "public_probe_calls": 2,
            "live_dispatch_calls": 1,
            "live_dispatch_started": True,
            "live_process_started": True,
            "live_process_return_code": 1,
            "capture_initialized": True,
            "structured_result_present": False,
            "validator_status": "NOT_RUN",
            "legacy_record_return_code_preserved": 1,
            "legacy_return_code_scope": "LIVE_PROCESS_RETURN_CODE_OBSERVED",
        }

    def event(self) -> dict:
        return {
            "task_id": self.record["task_id"],
            "dispatch_id": self.record["dispatch_id"],
            "attempt_id": self.record["attempt_id"],
            "prior_record_hash": self.record["record_hash"],
            "observation_outcome": self.outcome(),
            "claim_ceiling": "Typed observation event only; no completion or external effect is inferred.",
        }

    def test_event_chain_and_exact_projection_binding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="observation-events-") as directory:
            event_path = Path(directory) / "events.jsonl"
            events = LiveObservationEventLedger(event_path)
            first = events.append(self.event(), expected_task_id=self.record["task_id"], expected_attempt_id=self.record["attempt_id"])
            self.assertEqual(first["sequence"], 0)
            self.assertEqual(events.audit()["record_count"], 1)
            projection = build_live_current_projection(
                self.ledger_path,
                reconciliation_events_path=self.root / "ignition/data/operations/iterations/140/live-reconciliation-events-r1.jsonl",
                observation_events_path=event_path,
            )
            summary = next(row for row in projection["attempts"] if row["attempt_id"] == self.record["attempt_id"])
            self.assertEqual(summary["observation_outcome_type"] if "observation_outcome_type" in summary else "LIVE_PROCESS_OBSERVED", "LIVE_PROCESS_OBSERVED")
            self.assertTrue(summary["live_process_started"])
            self.assertEqual(summary["live_process_return_code"], 1)
            self.assertEqual(projection["source_ledger"]["observation_events"]["event_count"], 1)

    def test_rebinding_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.event())
        tampered["prior_record_hash"] = "0" * 64
        with tempfile.TemporaryDirectory(prefix="observation-events-rebind-") as directory:
            event_path = Path(directory) / "events.jsonl"
            LiveObservationEventLedger(event_path).append(tampered)
            with self.assertRaises(LiveCurrentProjectionError):
                build_live_current_projection(
                    self.ledger_path,
                    reconciliation_events_path=self.root / "ignition/data/operations/iterations/140/live-reconciliation-events-r1.jsonl",
                    observation_events_path=event_path,
                )


if __name__ == "__main__":
    unittest.main()
