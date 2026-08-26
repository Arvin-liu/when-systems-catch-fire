from __future__ import annotations

import unittest

from tools.validate_task141_structured_result_repair import run_validation


class Task141StructuredResultRepairTests(unittest.TestCase):
    def test_strict_contract_and_fake_matrix_are_closed(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["failures"], 0)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["skips"], 0)
        self.assertFalse(result["strict_additional_properties"])


if __name__ == "__main__":
    unittest.main()
