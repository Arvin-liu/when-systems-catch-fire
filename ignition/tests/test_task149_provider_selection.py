import copy
import json
import unittest

from tools.validate_task149_provider_selection import ARTIFACT_PATH, validate


class Task149ProviderSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_selection_policy_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_provider_local_must_use_rule_is_rejected(self):
        self.assertFalse(self.document["provider_local_policy_test"]["global_inheritance"])
        self.assertEqual(self.document["provider_local_policy_test"]["decision"], "REJECTED_PROVIDER_LOCAL_POLICY")

    def test_selection_authority_is_research_only_not_current_runtime_interface(self):
        self.assertEqual(self.document["research_scope"], "EXPERIMENTAL_PROVIDER_ADMISSION_RESEARCH_ONLY")
        self.assertEqual(self.document["runtime_interface_status"], "NOT_A_CURRENT_RUNTIME_PROVIDER_INTERFACE")

    def test_selection_does_not_hardcode_total_order(self):
        self.assertFalse(self.document["selection_procedure"]["total_order_hardcoded_by_task"])
        self.assertTrue(all(item["ordering"] == "CONTEXT_DEPENDENT" for item in self.document["selection_inputs"]))

    def test_user_choice_cannot_grant_permission(self):
        mutated = copy.deepcopy(self.document)
        mutated["candidate_decisions"][0]["permission_granted"] = True
        self.assertTrue(validate(mutated))

    def test_authenticated_selection_is_rejected(self):
        decision = next(item for item in self.document["candidate_decisions"] if item["operation"] == "read_authenticated_source")
        self.assertEqual(decision["selection_result"], "REJECTED_AUTHENTICATION_NOT_ADMITTED")
        self.assertFalse(decision["authenticated_channel_admitted"])


if __name__ == "__main__":
    unittest.main()
