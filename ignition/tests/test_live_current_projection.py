from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_federation.live_current_projection import (
    LIVE_CURRENT_PROJECTION_SCHEMA,
    LiveCurrentProjectionError,
    build_live_current_projection,
    validate_projection,
)


class LiveCurrentProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self._temporary_directory = tempfile.TemporaryDirectory(prefix="live-current-projection-")
        self.ledger_path = Path(self._temporary_directory.name) / "live-attempt-ledger.jsonl"
        shutil.copy2(
            self.repo_root / "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl",
            self.ledger_path,
        )

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def test_projection_has_current_ledger_derived_counts_and_latest_attempt(self) -> None:
        projection = build_live_current_projection(self.ledger_path)
        self.assertEqual(projection["counts"]["total_attempts"], 6)
        self.assertEqual(projection["counts"]["validated_completion_count"], 0)
        self.assertEqual(projection["counts"]["unreconciled_count"], 3)
        self.assertEqual(projection["counts"]["observation_incomplete_count"], 2)
        self.assertEqual(projection["per_executor"]["external.codex"]["attempt_count"], 5)
        self.assertEqual(
            projection["latest_attempt_per_executor"]["external.codex"]["state"],
            "MALFORMED_RESULT",
        )
        self.assertIsNone(projection["latest_validated_completion"])
        self.assertEqual(projection["obligation"]["state"], "OPEN")
        self.assertEqual(
            projection["obligation"]["unreconciled_attempt_ids"],
            ["live-hermes-136-initial", "attempt-138-live-02", "attempt-139-live-02"],
        )
        self.assertEqual(projection["next_eligible_action"]["status"], "BLOCKED_UNTIL_RECONCILIATION")
        self.assertEqual(projection["current_live_ceiling"], "LIVE_EXTERNAL_INVOCATION_OPEN_NO_VALIDATED_COMPLETION")

    def test_two_builds_are_byte_identical_and_tampering_fails(self) -> None:
        first = build_live_current_projection(self.ledger_path)
        second = build_live_current_projection(self.ledger_path)
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
        tampered = copy.deepcopy(first)
        tampered["counts"]["unreconciled_count"] = 0
        with self.assertRaises(LiveCurrentProjectionError):
            validate_projection(tampered)

    def test_rendered_projection_round_trips_through_validator(self) -> None:
        projection = build_live_current_projection(self.ledger_path)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "projection.json"
            path.write_text(json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_projection(loaded)["projection_digest"], projection["projection_digest"])

    def test_r3_separates_process_observation_from_validated_completion(self) -> None:
        projection = build_live_current_projection(
            self.ledger_path,
            projection_schema=LIVE_CURRENT_PROJECTION_SCHEMA,
            reconciliation_events_path=self.repo_root / "ignition/data/operations/iterations/140/live-reconciliation-events-r1.jsonl",
            observation_events_path=self.repo_root / "ignition/data/operations/iterations/140/live-observation-events-r1.jsonl",
        )
        self.assertEqual(projection["schema_version"], "live-current-projection-r3")
        self.assertEqual(projection["live_state_dimensions"]["live_dispatch_observation_status"], "OBSERVED")
        self.assertEqual(projection["live_state_dimensions"]["live_process_observation_status"], "OBSERVED")
        self.assertEqual(projection["live_state_dimensions"]["inference_observation_status"], "NOT_OBSERVED")
        self.assertEqual(projection["live_state_dimensions"]["validated_completion_status"], "NOT_VALIDATED")
        self.assertEqual(projection["current_live_ceiling"], "LIVE_EXTERNAL_PROCESS_OBSERVED_NO_VALIDATED_COMPLETION")
        self.assertNotEqual(projection["current_live_ceiling"], "LIVE_EXTERNAL_INVOCATION_NOT_OBSERVED")
        self.assertEqual(validate_projection(projection)["projection_digest"], projection["projection_digest"])


if __name__ == "__main__":
    unittest.main()
