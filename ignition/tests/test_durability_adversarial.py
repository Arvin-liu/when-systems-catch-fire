from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_runtime.adversarial import ADVERSARIAL_SCHEMA, AdversarialCase, AdversarialMatrix, AdversarialMatrixError, REQUIRED_CASE_IDS


ROOT = Path(__file__).resolve().parents[1]


class DurabilityAdversarialTests(unittest.TestCase):
    def test_matrix_covers_all_required_cases_and_runs_offline(self) -> None:
        data = json.loads((ROOT / "data/operations/durability/adversarial-matrix-r1.json").read_text(encoding="utf-8"))
        matrix = AdversarialMatrix.from_dict(data)
        summary = matrix.validate()
        result = matrix.run_offline()
        self.assertEqual(data["schema_version"], ADVERSARIAL_SCHEMA)
        self.assertEqual(summary["case_count"], len(REQUIRED_CASE_IDS))
        self.assertEqual(len(result["cases"]), len(REQUIRED_CASE_IDS))
        self.assertTrue(all(item["external_invocation"] == "NOT_RUN" for item in result["cases"]))
        self.assertTrue(all(item["guard_status"] in {"FAIL_CLOSED", "RECONCILIATION_REQUIRED", "RESTART_AND_REPLAY"} for item in result["cases"]))

    def test_missing_case_and_escalatory_outcome_fail_closed(self) -> None:
        data = json.loads((ROOT / "data/operations/durability/adversarial-matrix-r1.json").read_text(encoding="utf-8"))
        data["cases"] = data["cases"][:-1]
        with self.assertRaises(AdversarialMatrixError):
            AdversarialMatrix.from_dict(data).validate()
        with self.assertRaises(AdversarialMatrixError):
            AdversarialCase("bad-case", "boundary", "mutation", "SUCCESS", "fixture", "local fixture only")


if __name__ == "__main__":
    unittest.main()
