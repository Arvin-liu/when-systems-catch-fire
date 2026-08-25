import unittest

from agent_federation.live_capture_fault_matrix import CASE_SPECS, run_capture_fault_matrix


class LiveCaptureFaultMatrixTests(unittest.TestCase):
    def test_all_required_capture_faults_are_deterministic_and_fail_closed(self) -> None:
        report = run_capture_fault_matrix()
        self.assertEqual(report["case_count"], 16)
        self.assertTrue(report["all_fail_closed"])
        self.assertEqual(len({item["case_id"] for item in report["cases"]}), 16)
        self.assertEqual(tuple(item[0] for item in CASE_SPECS), tuple(item["case_id"] for item in report["cases"]))

    def test_context_loss_and_incomplete_capture_have_distinct_outcomes(self) -> None:
        report = {item["case_id"]: item for item in run_capture_fault_matrix()["cases"]}
        self.assertEqual(report["context_unavailable_capsule_complete"]["observed"], "CONTEXT_LOST_CAPTURE_COMPLETE")
        self.assertEqual(report["context_unavailable_capsule_incomplete"]["observed"], "TRUNCATED_REQUIRES_RECONCILIATION")
        self.assertEqual(report["secret_marker_output"]["observed"], "SECRET_REJECTED_AND_CONTEXT_REDACTED")


if __name__ == "__main__":
    unittest.main()
