import copy
import json
import unittest

from tools.validate_task149_provider_contract import ARTIFACT_PATH, validate


class Task149ProviderContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_contract_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_provider_output_cannot_be_architecture_truth(self):
        mutated = copy.deepcopy(self.document)
        mutated["provider_records"][0]["trust_boundary"]["provider_output_is_not_architecture_truth"] = False
        self.assertTrue(validate(mutated))

    def test_provider_local_policy_is_not_inherited(self):
        for record in self.document["provider_records"]:
            self.assertFalse(record["provider_local_policy_not_inherited"]["inherited"])

    def test_contract_is_research_only_not_current_runtime_interface(self):
        self.assertEqual(self.document["research_scope"], "EXPERIMENTAL_PROVIDER_ADMISSION_RESEARCH_ONLY")
        self.assertEqual(self.document["runtime_interface_status"], "NOT_A_CURRENT_RUNTIME_PROVIDER_INTERFACE")

    def test_future_provider_id_is_not_the_contract(self):
        mutated = copy.deepcopy(self.document)
        mutated["provider_records"][0]["provider_id"] = "future-provider"
        errors = validate(mutated)
        self.assertTrue(any("archify" in error for error in errors))

    def test_no_current_or_authenticated_admission(self):
        for record in self.document["provider_records"]:
            self.assertEqual(record["current_integration"]["status"], "NOT_CURRENT_INTEGRATION")
            self.assertEqual(record["authentication_requirement"]["authenticated_channel_admission"], "NOT_GRANTED")


if __name__ == "__main__":
    unittest.main()
