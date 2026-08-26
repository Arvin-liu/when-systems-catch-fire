from __future__ import annotations

import unittest

from agent_federation.task142_adversarial import CASES, run_matrix


class Task142AdversarialTests(unittest.TestCase):
    def test_all_required_negative_cases_reject(self) -> None:
        report = run_matrix()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["case_count"], 15)
        self.assertEqual(report["negative_case_count"], 15)
        self.assertFalse(report["live_process_started"])
        self.assertTrue(all(case["status"] == "PASS" for case in report["cases"]))

    def test_matrix_case_ids_are_unique(self) -> None:
        self.assertEqual(len(CASES), len({case[0] for case in CASES}))


if __name__ == "__main__":
    unittest.main()
