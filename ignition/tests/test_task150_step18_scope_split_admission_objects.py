import copy
import json
import unittest

from tools.validate_task150_step18_scope_split_admission_objects import ARTIFACT_PATH, validate


class Task150Step18ScopeSplitAdmissionObjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_scope_split_contract_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_base_operation_keeps_provider_neutral_id(self):
        base = self.document["base_operation"]
        self.assertEqual(base["operation_id"], "visualization.render_derived_system_view")
        self.assertEqual(base["status"], "CURRENT_BOUNDED_CANDIDATE")
        self.assertTrue(base["provider_binding"]["operation_definition_is_provider_neutral"])

    def test_delta_is_separate_and_deferred(self):
        delta = self.document["delta_extension"]
        self.assertEqual(delta["status"], "EXPERIMENTAL_EXTENSION_DEFERRED")
        self.assertEqual(delta["gate"]["result"], "FAIL_DEFERRED")
        self.assertFalse(delta["promotion_guard"]["delta_failure_can_pollute_base"])
        self.assertFalse(delta["promotion_guard"]["base_pass_promotes_delta"])

    def test_historical_defer_and_draft_closeout_are_preserved(self):
        historical = self.document["historical_preservation"]
        self.assertEqual(historical["step14_result"], "DEFER")
        self.assertEqual(historical["step15_result"], "TASK150_STEP15_DRAFT_PR_OWNER_REVIEW_STOP")
        self.assertTrue(historical["historical_receipts_immutable"])

    def test_aesthetic_endorsement_is_neither_required_nor_claimed(self):
        boundary = self.document["aesthetic_boundary"]
        self.assertEqual(boundary["owner_aesthetic_endorsement"], "NOT_GRANTED")
        self.assertFalse(boundary["owner_aesthetic_endorsement_required_for_base"])
        self.assertFalse(boundary["owner_rejected_visual"])
        self.assertFalse(boundary["owner_visual_accepted"])

    def test_combined_gate_cannot_be_restored(self):
        mutated = copy.deepcopy(self.document)
        mutated["gate_topology"]["delta_failure_cannot_pollute_base"] = False
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["delta_extension"]["promotion_guard"]["base_pass_promotes_delta"] = True
        self.assertTrue(validate(mutated))

    def test_registry_and_lifecycle_boundaries_remain_closed(self):
        registry = self.document["registry_boundary"]
        self.assertEqual(registry["operation_count_after"], 19)
        self.assertFalse(registry["registry_write_in_step18"])
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["default_renderer"], "NOT_SELECTED")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["task151"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
