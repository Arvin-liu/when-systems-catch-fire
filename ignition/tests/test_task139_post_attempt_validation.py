from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent_federation.live_current_projection import validate_projection


class Task139PostAttemptValidationTests(unittest.TestCase):
    def test_current_projection_retains_exact_incomplete_attempt_without_completion(self) -> None:
        root = Path(__file__).resolve().parents[1]
        projection = validate_projection(json.loads((root / "data/operations/iterations/139/live-current-projection-r1.json").read_text(encoding="utf-8")))
        latest = projection["latest_attempt_per_executor"]["external.codex"]
        self.assertEqual(latest["task_id"], "IGNITION-20260825-139")
        self.assertEqual(latest["dispatch_id"], "dispatch-139-live-02")
        self.assertEqual(latest["attempt_id"], "attempt-139-live-02")
        self.assertEqual(latest["state"], "OBSERVATION_INCOMPLETE")
        self.assertEqual(projection["counts"]["validated_completion_count"], 0)
        self.assertEqual(projection["obligation"]["state"], "OPEN")
        self.assertEqual(projection["next_eligible_action"]["action"], "RECONCILE_UNRECOVERED_ATTEMPTS")


if __name__ == "__main__":
    unittest.main()
