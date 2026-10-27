from __future__ import annotations

import unittest

from tools.validate_task140_adversarial_matrix import run_matrix


class Task140AdversarialMatrixTests(unittest.TestCase):
    def test_required_negative_and_positive_cases_are_fail_closed(self) -> None:
        report = run_matrix()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["case_count"], 20)
        self.assertEqual(report["negative_case_count"], 17)
        self.assertEqual(report["positive_case_count"], 3)
        self.assertEqual(report["live_processes_started"], 0)
        self.assertTrue(all(case["status"] == "PASS" for case in report["cases"]), report)


if __name__ == "__main__":
    unittest.main()
