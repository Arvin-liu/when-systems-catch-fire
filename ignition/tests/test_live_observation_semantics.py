from __future__ import annotations

import unittest

from tools.validate_live_observation_semantics import run_semantic_gate


class LiveObservationSemanticGateTests(unittest.TestCase):
    def test_required_twelve_fixtures_pass_with_expected_fail_closed_statuses(self) -> None:
        report = run_semantic_gate()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["case_count"], 12)
        self.assertTrue(all(case["status"] == "PASS" for case in report["cases"]), report)
        self.assertEqual(
            {case["case_id"] for case in report["cases"]},
            {
                "ledger-says-happened-current-says-forbidden",
                "incomplete-capsule-current-says-success",
                "exit-zero-without-validator",
                "validated-completion-exact-binding",
                "historical-narrative-preserved",
                "duplicate-attempt-overwrite",
                "raw-private-output-formal-ledger",
                "context-lost-capsule-complete",
                "context-lost-capsule-absent",
                "plain-gh-promoted-to-agent",
                "reasoner-runtime-closes-agent-obligation",
                "soft-governance-raises-authority",
            },
        )


if __name__ == "__main__":
    unittest.main()
