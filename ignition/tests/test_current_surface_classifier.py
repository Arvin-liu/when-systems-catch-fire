from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools import classify_current_surface as classifier


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data/operations/iterations/130/fixtures/current-surface-classifier-fixtures-r1.json"


class CurrentSurfaceClassifierTests(unittest.TestCase):
    def test_fixtures_classify_current_and_historical_boundaries(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for row in fixture["fixtures"]:
            with self.subTest(row=row["id"]):
                classifications = classifier.classify_text(row["text"], row["id"])
                self.assertTrue(classifications)
                self.assertEqual(classifications[-1]["classification"], row["expected_classification"])

    def test_real_surfaces_have_no_unterminated_blocks(self) -> None:
        result = classifier.report()
        self.assertFalse([
            row for surface in result["surfaces"] for row in surface["classifications"]
            if row["classification"] == "UNTERMINATED_GENERATED_BLOCK"
        ])


if __name__ == "__main__":
    unittest.main()
