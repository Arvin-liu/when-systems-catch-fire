import copy
import json
import unittest

from tools.validate_task149_step13_native_agent_reach_routing import ARTIFACT_PATH, validate


class Task149Step13RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_same_abstract_operations_are_compared(self):
        operations = {entry["abstract_operation"] for entry in self.document["provider_comparisons"]}
        self.assertEqual(operations, {"read_public_github_repository", "search_public_github_repositories", "read_public_web_page"})
        self.assertFalse(self.document["upper_workflow_changed"])

    def test_native_paths_pass(self):
        for comparison in self.document["provider_comparisons"]:
            self.assertEqual(comparison["native_provider"]["status"], "PASS")
            self.assertEqual(comparison["native_provider"]["exit_code"], 0)

    def test_github_route_retains_auth_failure(self):
        for comparison in self.document["provider_comparisons"][:2]:
            routed = comparison["agent_reach_routed_provider"]
            self.assertEqual(routed["status"], "AUTH_REQUIRED")
            self.assertEqual(routed["exit_code"], 4)
            self.assertEqual(routed["result_count"], 0)

    def test_web_route_normalizes_without_hash_equality(self):
        comparison = self.document["provider_comparisons"][2]
        self.assertEqual(comparison["agent_reach_routed_provider"]["status"], "PASS")
        self.assertTrue(comparison["normalization"]["title_equal"])
        self.assertFalse(comparison["normalization"]["representation_hashes_equal"])

    def test_provenance_failure_and_dependency_dimensions_are_retained(self):
        for comparison in self.document["provider_comparisons"]:
            self.assertFalse(comparison["provider_switching_leaks_implementation_details_upward"])
            self.assertTrue(comparison["normalization"]["schema"])
            self.assertTrue(comparison["permission_difference"])
            self.assertTrue(comparison["dependency_difference"])

    def test_partial_swap_is_not_current_admission(self):
        self.assertEqual(self.document["provider_switching_experiment"]["provider_swap_result"], "PARTIAL")
        self.assertEqual(self.document["boundaries"]["current_integration"], "NOT_CURRENT_INTEGRATION")
        self.assertEqual(self.document["boundaries"]["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")

    def test_mutated_native_result_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["provider_comparisons"][0]["native_provider"]["status"] = "AUTH_REQUIRED"
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
