from __future__ import annotations

import unittest

from tools import validate_iteration_boundary_compatibility as audit


class IterationBoundaryCompatibilityTests(unittest.TestCase):
    def test_historical_compatibility_audit_passes(self) -> None:
        report = audit.build_report()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(len(report["historical_receipts"]), 7)

    def test_historical_receipts_are_not_reinterpreted_as_current(self) -> None:
        report = audit.build_report()
        self.assertTrue(all(row["historical"] for row in report["historical_receipts"]))
        self.assertTrue(all(not row["current_semantic_fields_present"] for row in report["historical_receipts"]))
        self.assertEqual(report["current_projection"]["formal_task_ordinal"], 133)
        self.assertEqual(report["current_projection"]["architecture_task_ordinal"], 129)


if __name__ == "__main__":
    unittest.main()
