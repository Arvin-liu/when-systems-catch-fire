import copy
import json
import unittest

from tools.validate_task150_step02_minimal_bounded_operation import ARTIFACT_PATH, validate


class Task150Step02MinimalBoundedOperationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_contract_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_operation_uses_existing_taxonomy_and_is_candidate(self):
        operation = self.document["operation"]
        self.assertEqual(operation["operation_id"], "visualization.render_derived_system_view")
        self.assertEqual(operation["current_status"], "CANDIDATE_NOT_CURRENT")
        self.assertEqual(operation["registry_entry_status"], "NOT_YET_REGISTERED_PENDING_STEP11")

    def test_flow_is_one_way_and_provider_neutral(self):
        operation = self.document["operation"]
        self.assertEqual(operation["allowed_flow"], "CANONICAL_SOURCE -> PROVIDER_ADAPTER -> DERIVED_ARTIFACT")
        self.assertTrue(operation["reverse_flow_forbidden"])
        self.assertEqual(self.document["provider_selection"]["provider_binding"], "UNBOUND_PROVIDER_SLOT_AT_STEP02")

    def test_read_only_and_fallback_boundaries_are_explicit(self):
        operation = self.document["operation"]
        self.assertEqual(operation["default_execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(operation["repository_mutation"]["permission"], "FORBIDDEN")
        self.assertTrue(self.document["failure_and_fallback"]["canonical_source_remains_usable"])
        self.assertFalse(self.document["installation_boundary"]["automatic_system_install"])

    def test_current_upgrade_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["operation"]["current_status"] = "CURRENT"
        self.assertTrue(validate(mutated))

    def test_topology_or_authority_upgrade_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["authority_boundary"]["provider_can_add_topology"] = True
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["authority_boundary"]["derived_artifact_can_update_canonical_source"] = True
        self.assertTrue(validate(mutated))

    def test_general_external_action_or_auth_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["operation"]["provider_invocation"]["unrelated_external_action"] = "ALLOWED"
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["authority_boundary"]["authenticated_channel_admission"] = "ADMITTED"
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
