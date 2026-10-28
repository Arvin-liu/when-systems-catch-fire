import copy
import json
import unittest

from tools.validate_task149_step16_final_report import ARTIFACT_PATH, validate


class Task149Step16FinalReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_report_title_and_human_receipt_are_bound(self):
        self.assertEqual(self.document["report_title"], "External Capability Provider Adapter Spikes R0")
        self.assertEqual(len(self.document["human_report_sha256"]), 64)

    def test_archify_recommendation_and_limits(self):
        recommendation = self.document["recommendations"]["archify"]
        self.assertEqual(recommendation["recommendation"], "CONTINUE_EXPERIMENT")
        self.assertEqual(recommendation["future_role"], "derived visualization provider")
        self.assertTrue(recommendation["known_limits"])
        self.assertEqual(recommendation["artifact_bytes"], 753375)

    def test_agent_reach_public_and_authenticated_are_separate(self):
        public = self.document["recommendations"]["agent_reach_public"]
        authenticated = self.document["recommendations"]["agent_reach_authenticated"]
        self.assertEqual(public["recommendation"], "CONTINUE_EXPERIMENT")
        self.assertEqual(authenticated["recommendation"], "DEFER")
        self.assertEqual(authenticated["authenticated_calls"], 0)
        self.assertEqual(public["channel_matrix"]["doctor_channels"], 15)

    def test_channel_matrix_retains_bounded_failures(self):
        matrix = self.document["recommendations"]["agent_reach_public"]["channel_matrix"]
        self.assertIn("github read", matrix["auth_required"])
        self.assertIn("Exa public search", matrix["environment_missing"])
        self.assertTrue(matrix["doctor_success_is_not_acquisition_success"])

    def test_overall_status_is_candidate_not_current(self):
        self.assertEqual(self.document["overall_status"], "PROVIDER_ADMISSION_CANDIDATE")
        self.assertEqual(self.document["boundaries"]["current_integration"], "NOT_CURRENT_INTEGRATION")
        self.assertEqual(self.document["boundaries"]["production_readiness"], "NOT_PRODUCTION_READY")

    def test_claim_boundaries_are_closed(self):
        boundaries = self.document["boundaries"]
        self.assertFalse(boundaries["external_provider_is_ignition_authority"])
        self.assertFalse(boundaries["provider_output_is_external_truth"])
        self.assertFalse(boundaries["provider_local_policy_is_ignition_global_policy"])
        self.assertEqual(boundaries["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")

    def test_live_invocation_and_next_action(self):
        self.assertEqual(self.document["test_summary"]["external_live_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(self.document["exact_next_action"], "AWAIT_OWNER_PROVIDER_ADAPTER_REVIEW")

    def test_mutated_recommendation_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["recommendations"]["agent_reach_authenticated"]["recommendation"] = "CONTINUE_EXPERIMENT"
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
