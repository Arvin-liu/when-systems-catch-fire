import copy
import json
import unittest

from tools.validate_task150_step08_provider_failure_fallback import ARTIFACT_PATH, simulated_result, validate


class Task150Step08ProviderFailureFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_matrix_and_preservation_pass(self):
        self.assertEqual(validate(self.document), [])
        self.assertEqual(len(self.document["cases"]), 7)

    def test_unavailable_results_are_typed(self):
        self.assertEqual(simulated_result("archify-command-unavailable"), "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT")
        self.assertEqual(simulated_result("node-unavailable"), "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT")

    def test_provider_failures_do_not_poison_canonical_inputs(self):
        preservation = self.document["canonical_preservation"]
        self.assertTrue(preservation["architecture_preserved"])
        self.assertTrue(preservation["last_known_map_preserved"])
        self.assertEqual(preservation["architecture_before_sha256"], preservation["architecture_after_sha256"])
        self.assertEqual(preservation["last_known_map_before_sha256"], preservation["last_known_map_after_sha256"])

    def test_all_non_discovery_failures_are_bounded(self):
        for case in self.document["cases"][2:]:
            self.assertEqual(case["observed"], "BOUNDED_PROVIDER_FAILURE")

    def test_missing_case_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["cases"].pop()
        self.assertTrue(validate(mutated))

    def test_implicit_substitution_and_system_mutation_are_closed(self):
        injection = self.document["failure_injection"]
        self.assertFalse(injection["real_provider_process_started"])
        self.assertFalse(injection["system_mutation"])
        self.assertFalse(injection["implicit_substitution"])
        mutated = copy.deepcopy(self.document)
        mutated["failure_injection"]["implicit_substitution"] = True
        self.assertTrue(validate(mutated))

    def test_current_auth_and_live_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["current_admission"], "NOT_ADMITTED")
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")


if __name__ == "__main__":
    unittest.main()
