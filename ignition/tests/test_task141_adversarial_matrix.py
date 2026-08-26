from __future__ import annotations

import unittest

from tools.validate_task141_adversarial_matrix_receipt import run_validation


class Task141AdversarialMatrixTests(unittest.TestCase):
    def test_22_case_matrix_is_deterministic_and_clean(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["case_count"], 22)
        self.assertEqual(result["negative_case_count"], 17)
        self.assertEqual(result["positive_case_count"], 5)
        self.assertEqual(result["live_processes_started"], 0)


if __name__ == "__main__":
    unittest.main()
