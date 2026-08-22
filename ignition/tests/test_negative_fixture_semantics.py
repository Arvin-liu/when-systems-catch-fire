from __future__ import annotations

import unittest

from tools.validate_negative_fixture_semantics import run_audit


class NegativeFixtureSemanticsTests(unittest.TestCase):
    def test_declared_negative_fixture_audit_passes_without_suite_error(self) -> None:
        report = run_audit()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["failed_targets"], [])
        self.assertGreaterEqual(report["target_count"], 10)
        self.assertGreaterEqual(report["tests_run"], 40)
        self.assertEqual(report["contract"]["negative_fixture_unittest_failures_allowed"], 0)
        self.assertEqual(report["contract"]["negative_fixture_unittest_errors_allowed"], 0)
        self.assertEqual(report["contract"]["negative_fixture_unittest_skips_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
