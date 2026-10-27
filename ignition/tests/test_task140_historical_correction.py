from __future__ import annotations

import unittest

from tools.validate_task140_historical_correction import run_validation


class Task140HistoricalCorrectionTests(unittest.TestCase):
    def test_task140_history_is_preserved_and_task141_overlay_is_additive(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["history_rewritten"])
        self.assertEqual(result["root_cause_status"], "ROOT_CAUSE_NOT_RECOVERABLE_FROM_TASK140_FORMAL_EVIDENCE")
        self.assertEqual(result["inference_correction_status"], "NOT_OBSERVED")


if __name__ == "__main__":
    unittest.main()
