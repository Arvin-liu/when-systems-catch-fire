import copy
import json
import unittest

from tools.validate_task150_step23_candidate_registry_admission import (
    ARTIFACT_PATH,
    REGISTRY_PATH,
    validate,
)


class Task150Step23CandidateRegistryAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_candidate_registry_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_exactly_one_provider_neutral_operation_was_added(self):
        operation_ids = [row["operation_id"] for row in self.registry["operations"]]
        self.assertEqual(len(operation_ids), 20)
        self.assertEqual(operation_ids, sorted(operation_ids))
        self.assertIn("visualization.render_derived_system_view", operation_ids)
        self.assertFalse(any("archify" in operation_id.lower() for operation_id in operation_ids))
        self.assertFalse(any("delta" in operation_id.lower() for operation_id in operation_ids))

    def test_new_operation_is_current_bounded_read_only(self):
        operation = next(row for row in self.registry["operations"] if row["operation_id"] == "visualization.render_derived_system_view")
        self.assertEqual(operation["current_status"], "CURRENT_BOUNDED")
        self.assertEqual(operation["ai_callability"], "PUBLIC_BOUNDED")
        self.assertEqual(operation["default_execution_mode"], "READ_ONLY_RUN")
        self.assertIsNone(operation["pack_binding"])
        self.assertEqual(operation["repository_mutation_permission"], "FORBIDDEN")
        self.assertEqual(operation["external_action_permission"], "FORBIDDEN")

    def test_entry_remains_candidate_until_lifecycle_completion(self):
        boundary = self.document["admission_boundary"]
        self.assertTrue(boundary["entry_is_candidate_only_until_ready_merge_and_current_lifecycle"])
        self.assertFalse(boundary["formal_ready"])
        self.assertFalse(boundary["merged_to_main"])
        self.assertFalse(boundary["current_on_main"])

    def test_mutating_operation_status_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["operation"]["current_status"] = "CURRENT"
        self.assertTrue(validate(mutated))

    def test_mutating_registry_count_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["registry"]["operation_count_after"] = 19
        self.assertTrue(validate(mutated))

    def test_side_effect_and_scope_boundaries_remain_closed(self):
        operation = self.document["operation"]
        self.assertEqual(operation["default_execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(operation["repository_mutation_permission"], "FORBIDDEN")
        self.assertEqual(operation["external_action_permission"], "FORBIDDEN")
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")
        self.assertEqual(scope["authenticated_channel_admission"], "NO_CHANGE")
        self.assertEqual(scope["live_external_invocation"], "OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["task151"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
