from __future__ import annotations

import unittest

from tools.validate_task141_live_probe import run_validation


class Task141LiveProbeTests(unittest.TestCase):
    def test_no_live_attempt_keeps_validator_unstarted(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["attempt_count"], 0)
        self.assertEqual(result["live_dispatch_calls"], 0)
        self.assertEqual(result["validator_status"], "NOT_STARTED_NO_LIVE_ATTEMPT")


if __name__ == "__main__":
    unittest.main()
