from __future__ import annotations

import copy
import unittest

from tools import validate_release_fault_matrix as matrix


class ReleaseFaultMatrixTests(unittest.TestCase):
    def test_fault_matrix_is_complete(self) -> None:
        self.assertEqual(matrix.validate(), [])

    def test_missing_fault_case_is_rejected(self) -> None:
        document = copy.deepcopy(matrix.load_json(matrix.FIXTURE_PATH))
        document["matrix"] = document["matrix"][:-1]
        self.assertTrue(matrix.validate(document))

    def test_historical_not_published_is_classified_allowed(self) -> None:
        rows = matrix.load_json(matrix.FIXTURE_PATH)["matrix"]
        row = next(item for item in rows if item["case_id"] == "historical-not-published-token")
        self.assertEqual(row["expected_outcome"], "HISTORICAL_ALLOWED")


if __name__ == "__main__":
    unittest.main()
