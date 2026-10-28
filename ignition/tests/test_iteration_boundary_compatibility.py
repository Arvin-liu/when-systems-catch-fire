from __future__ import annotations

import unittest

from tools import validate_iteration_boundary_compatibility as audit
from tools import task_identity


class IterationBoundaryCompatibilityTests(unittest.TestCase):
    def test_historical_compatibility_audit_passes(self) -> None:
        report = audit.build_report()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(len(report["historical_receipts"]), 10)

    def test_historical_receipts_are_not_reinterpreted_as_current(self) -> None:
        report = audit.build_report()
        self.assertTrue(all(row["historical"] for row in report["historical_receipts"]))
        self.assertTrue(all(row["current_semantic_fields_present"] is False for row in report["historical_receipts"] if row["task_ordinal_from_id"] < 133))
        self.assertTrue(any(row["task_id"] == "IGNITION-20260822-133" and row["current_semantic_fields_present"] for row in report["historical_receipts"]))
        identity = audit.load_json(audit.ROOT / "data/operations/current-task-lineage-status.json")["task_identity"]
        self.assertEqual(report["current_projection"]["formal_task_ordinal"], task_identity.parse_task_id(identity["current_formal_task"])["ordinal"])
        self.assertEqual(report["current_projection"]["architecture_task_ordinal"], task_identity.parse_task_id(identity["latest_architecture_changing_task"])["ordinal"])


if __name__ == "__main__":
    unittest.main()
