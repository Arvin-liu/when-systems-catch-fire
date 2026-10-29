from __future__ import annotations

import json
import unittest

from tools import validate_iteration_ordinal_matrix as matrix


class IterationOrdinalMatrixTests(unittest.TestCase):
    def test_matrix_has_exactly_fifteen_cases(self) -> None:
        fixture = matrix.load_json(matrix.FIXTURE_PATH)
        self.assertEqual(len(fixture["cases"]), 15)

    def test_matrix_is_pass(self) -> None:
        report = matrix.build_report()
        self.assertEqual(report["status"], "PASS", report)
        self.assertTrue(all(row["result"] == "PASS" for row in report["results"]), report)

    def test_historical_cases_are_positive(self) -> None:
        report = matrix.build_report()
        by_id = {row["case_id"]: row for row in report["results"]}
        self.assertEqual(by_id["historical-old-130-allowed"]["actual"], "PASS")
        self.assertEqual(by_id["append-only-changelog-history-allowed"]["actual"], "PASS")


if __name__ == "__main__":
    unittest.main()
