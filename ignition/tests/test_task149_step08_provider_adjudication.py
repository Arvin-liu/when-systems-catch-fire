import copy
import json
import unittest

from tools.validate_task149_step08_provider_adjudication import ARTIFACT_PATH, validate


class Task149Step08ProviderAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_required_comparisons_are_present(self):
        operations = {entry["abstract_operation"] for entry in self.document["provider_comparisons"]}
        self.assertEqual(operations, {"read_public_github_repository", "search_public_github_repositories", "read_public_web_page"})

    def test_github_auth_failure_is_not_promoted_to_success(self):
        github = [entry for entry in self.document["provider_comparisons"] if entry["abstract_operation"] == "read_public_github_repository"][0]
        routed = github["agent_reach_routed_provider"]
        self.assertEqual(routed["status"], "AUTH_REQUIRED")
        self.assertEqual(routed["exit_code"], 4)
        self.assertEqual(routed["result_count"], 0)

    def test_public_web_route_normalizes_with_provenance(self):
        web = [entry for entry in self.document["provider_comparisons"] if entry["abstract_operation"] == "read_public_web_page"][0]
        self.assertEqual(web["agent_reach_routed_provider"]["status"], "AVAILABLE_READ_ONLY")
        self.assertTrue(web["agent_reach_routed_provider"]["provenance"]["raw_output_bound"])
        self.assertTrue(web["normalization"]["title_equal"])
        self.assertFalse(web["normalization"]["content_hashes_equal"])

    def test_adjudication_does_not_admit_current_or_authenticated(self):
        self.assertEqual(self.document["admission_recommendation"]["archify"], "FIT_WITH_LIMITS")
        self.assertEqual(self.document["admission_recommendation"]["agent_reach_public"], "FIT_WITH_LIMITS")
        self.assertEqual(self.document["admission_recommendation"]["agent_reach_authenticated"], "DEFER")
        self.assertTrue(self.document["admission_recommendation"]["future_candidate_only"])
        self.assertEqual(self.document["boundaries"]["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")

    def test_mutated_authority_boundary_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["boundaries"]["provider_output_is_external_truth"] = True
        self.assertTrue(validate(mutated))

    def test_mutated_provider_swap_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["provider_switching_experiment"]["upper_workflow_change"] = True
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
