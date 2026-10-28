from __future__ import annotations

import unittest

from tools.validate_residual_adversarial_matrix import run_matrix


class ResidualDeltaAdversarialMatrixTests(unittest.TestCase):
    def test_all_eighteen_cases_pass_the_declared_outcome(self) -> None:
        result = run_matrix()
        self.assertEqual(result["case_count"], 18)
        self.assertEqual(result["passed"], 18)


if __name__ == "__main__":
    unittest.main()
