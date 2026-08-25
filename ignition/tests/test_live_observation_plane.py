from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from agent_federation.live_attempt_ledger import LiveAttemptLedger, LiveAttemptLedgerError, validate_record
from agent_federation.live_current_projection import build_live_current_projection, validate_projection
from agent_federation.live_observation_plane import LiveObservationOutcomeError, derive_observation_outcome, validate_observation_outcome


class LiveObservationPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.ledger_path = self.repo_root / "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl"
        self.records = LiveAttemptLedger(self.ledger_path).records()

    def test_task139_probe_zero_is_not_a_live_process_exit_code(self) -> None:
        outcome = derive_observation_outcome(self.records[-1])
        self.assertEqual(outcome["observation_outcome_type"], "PRE_INFERENCE_NO_LIVE_PROCESS")
        self.assertEqual(outcome["probe_return_code"], 0)
        self.assertEqual(outcome["transport_return_code"], 0)
        self.assertEqual(outcome["public_probe_calls"], 2)
        self.assertEqual(outcome["live_dispatch_calls"], 0)
        self.assertFalse(outcome["live_process_started"])
        self.assertIsNone(outcome["live_process_return_code"])
        self.assertEqual(outcome["legacy_return_code_scope"], "PUBLIC_PROBE_TRANSPORT_VALUE_ONLY")

    def test_typed_projection_has_no_unscoped_return_code(self) -> None:
        projection = build_live_current_projection(self.ledger_path)
        validate_projection(projection)
        summary = projection["attempts"][-1]
        self.assertNotIn("return_code", summary)
        self.assertEqual(summary["probe_return_code"], 0)
        self.assertEqual(summary["transport_return_code"], 0)
        self.assertIsNone(summary["live_process_return_code"])
        self.assertEqual(summary["legacy_record_return_code_preserved"], 0)
        self.assertEqual(summary["legacy_return_code_scope"], "PUBLIC_PROBE_TRANSPORT_VALUE_ONLY")
        self.assertEqual(projection["schema_version"], "live-current-projection-r2")

    def test_historical_r1_projection_remains_valid(self) -> None:
        path = self.repo_root / "ignition/data/operations/iterations/139/live-current-projection-r1.json"
        historical = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_projection(historical)["projection_digest"], historical["projection_digest"])

    def test_process_return_code_cannot_be_added_without_process_observation(self) -> None:
        candidate = derive_observation_outcome(self.records[-1])
        candidate["live_process_return_code"] = 0
        with self.assertRaises(LiveObservationOutcomeError):
            validate_observation_outcome(candidate)

    def test_explicit_typed_outcome_is_ledger_validated(self) -> None:
        candidate = copy.deepcopy(self.records[-1])
        candidate["observation_typing"] = derive_observation_outcome(candidate)
        self.assertIn("observation_typing", validate_record(candidate, check_hash=False))
        candidate["observation_typing"]["live_process_started"] = True
        with self.assertRaises(LiveAttemptLedgerError):
            validate_record(candidate, check_hash=False)


if __name__ == "__main__":
    unittest.main()
