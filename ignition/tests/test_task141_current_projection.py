from __future__ import annotations

import json
import unittest

from tools.build_task141_live_current_projection import build
from tools.validate_task141_current_projection import run_validation


class Task141CurrentProjectionTests(unittest.TestCase):
    def test_r3_projection_preserves_process_observation_semantics(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["counts"]["total_attempts"], 6)
        self.assertEqual(result["counts"]["validated_completion_count"], 0)
        self.assertEqual(result["dimensions"]["live_process_observation_status"], "OBSERVED")
        self.assertEqual(result["dimensions"]["inference_observation_status"], "NOT_OBSERVED")
        self.assertEqual(result["dimensions"]["validated_completion_status"], "NOT_VALIDATED")

    def test_two_r3_builds_are_byte_identical(self) -> None:
        first = json.dumps(build(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        second = json.dumps(build(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
