from __future__ import annotations

import unittest

from agent_runtime.pilots.steering_adversarial_129 import run_adversarial_matrix


class SteeringAdversarialTests(unittest.TestCase):
    def test_matrix_is_complete_and_passes(self) -> None:
        result = run_adversarial_matrix()
        self.assertEqual(result["case_count"], 22)
        self.assertTrue(result["all_pass"])
        self.assertTrue(all(item["passed"] for item in result["cases"]))

    def test_high_risk_boundaries_have_expected_outcomes(self) -> None:
        cases = {item["case_id"]: item for item in run_adversarial_matrix()["cases"]}
        self.assertEqual(cases["run-pass-not-completion"]["observed_outcome"], "FAIL_CLOSED")
        self.assertEqual(cases["proposal-owner-escalation"]["observed_outcome"], "HUMAN_REVIEW")
        self.assertEqual(cases["executor-unavailable"]["observed_outcome"], "RECONCILIATION_REQUIRED")
        self.assertEqual(cases["telemetry-score-not-authority"]["observed_outcome"], "PASS_GUARD")


if __name__ == "__main__":
    unittest.main()
