import unittest

from agent_federation.live_fault_matrix import CASE_SPECS, run_fault_matrix


class LiveFaultMatrixTests(unittest.TestCase):
    def test_all_required_fault_dimensions_are_exercised_and_fail_closed(self):
        report = run_fault_matrix()
        self.assertEqual(report["case_count"], 27)
        self.assertTrue(report["all_fail_closed"])
        self.assertEqual(len({item["case_id"] for item in report["cases"]}), 27)
        self.assertEqual(tuple(item[0] for item in CASE_SPECS), tuple(item["case_id"] for item in report["cases"]))

    def test_unknown_effect_and_completion_forgery_do_not_become_success(self):
        report = {item["case_id"]: item for item in run_fault_matrix()["cases"]}
        self.assertEqual(report["timeout_effect_unknown"]["observed"], "REQUIRES_RECONCILIATION_NO_RETRY")
        self.assertEqual(report["executor_pass_goal_completion"]["observed"], "OS_VALIDATION_REQUIRED")
        self.assertEqual(report["billing_provider_mutation_request"]["observed"], "COST_AUTHORITY_REJECTED")


if __name__ == "__main__":
    unittest.main()
