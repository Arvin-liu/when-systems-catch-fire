import copy
import json
import unittest

from tools.validate_task150_step13_adversarial import ARTIFACT_PATH, SAFE_VALUES, evaluate_mutation, validate


class Task150Step13AdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_all_adversarial_cases_pass_fail_closed(self):
        self.assertEqual(validate(self.document), [])
        self.assertEqual(len(self.document["cases"]), 10)
        self.assertTrue(all(case["observed_result"] == "REJECTED" for case in self.document["cases"]))

    def test_safe_baseline_is_admissible_only_as_frozen_non_current_state(self):
        self.assertEqual(evaluate_mutation({}), [])
        self.assertEqual(self.document["safe_baseline"], SAFE_VALUES)

    def test_current_promotion_is_rejected(self):
        case = next(case for case in self.document["cases"] if case["id"] == "promote_current_provider")
        self.assertTrue(evaluate_mutation(case["mutation"]))

    def test_authority_and_permission_escalations_are_rejected(self):
        ids = {"provider_becomes_ignition_authority", "provider_capability_becomes_permission", "provider_output_becomes_external_truth", "provider_policy_becomes_global_policy", "adapter_pass_becomes_current_capability"}
        cases = [case for case in self.document["cases"] if case["id"] in ids]
        self.assertEqual(len(cases), 5)
        self.assertTrue(all(evaluate_mutation(case["mutation"]) for case in cases))

    def test_auth_live_homepage_and_topology_escalations_are_rejected(self):
        ids = {"authenticated_channel_admission", "live_external_invocation_change", "provider_homepage_claim", "topology_mutation"}
        cases = [case for case in self.document["cases"] if case["id"] in ids]
        self.assertEqual(len(cases), 4)
        self.assertTrue(all(evaluate_mutation(case["mutation"]) for case in cases))

    def test_unknown_mutation_fails_closed(self):
        self.assertTrue(evaluate_mutation({"unrecognized_authority": True}))

    def test_safe_value_mutation_is_not_treated_as_adversarial(self):
        self.assertEqual(evaluate_mutation({"current_admission": "NOT_ADMITTED"}), [])
        mutated = copy.deepcopy(self.document)
        mutated["cases"][0]["mutation"] = {"current_admission": "NOT_ADMITTED"}
        self.assertTrue(validate(mutated))

    def test_fixture_execution_has_no_side_effects(self):
        execution = self.document["fixture_execution"]
        self.assertFalse(execution["provider_process_started"])
        self.assertFalse(execution["credentials_or_sessions_accessed"])
        self.assertFalse(execution["system_or_repository_mutation"])


if __name__ == "__main__":
    unittest.main()
