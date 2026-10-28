import copy
import json
import unittest

from tools.validate_task150_step22_immutable_compatibility_envelope import (
    ARTIFACT_PATH,
    EXPECTED_PROVIDER_REVISION,
    EXPECTED_STEP21_HEAD,
    validate,
)


class Task150Step22ImmutableCompatibilityEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_compatibility_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_exact_commit_pin_is_bound(self):
        provider = self.document["provider"]
        self.assertEqual(provider["tested_immutable_ref"], EXPECTED_PROVIDER_REVISION)
        self.assertEqual(provider["checkout_revision"], EXPECTED_PROVIDER_REVISION)
        self.assertEqual(self.document["formal_previous_commit"], EXPECTED_STEP21_HEAD)
        self.assertEqual(provider["ref_kind"], "EXACT_COMMIT")

    def test_moving_ref_cannot_replace_exact_commit(self):
        mutated = copy.deepcopy(self.document)
        mutated["provider"]["tested_immutable_ref"] = "refs/heads/main"
        self.assertTrue(validate(mutated))

    def test_automatic_update_and_authority_are_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["provider"]["automatic_update"] = True
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["provider"]["architecture_authority"] = True
        self.assertTrue(validate(mutated))

    def test_fresh_commands_are_complete(self):
        recheck = self.document["compatibility_recheck"]
        self.assertEqual(recheck["typed_ir_validation"]["checks_passed"], 9)
        self.assertEqual(recheck["delivery"]["checks_passed"], 9)
        self.assertEqual(recheck["visual_check"]["required_containment_viewports"], 4)
        self.assertEqual(recheck["visual_check"]["required_capture_screenshots"], 4)

    def test_visual_failures_and_perceptual_state_are_fail_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["compatibility_recheck"]["visual_check"]["containment_failures"] = 1
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["compatibility_recheck"]["visual_check"]["visual_review"] = "ACCEPTED"
        self.assertTrue(validate(mutated))

    def test_current_registry_and_delta_remain_closed(self):
        boundary = self.document["admission_boundary"]
        self.assertFalse(boundary["current_capability"])
        self.assertFalse(boundary["registry_write"])
        self.assertEqual(boundary["registry_operation_count"], 19)
        self.assertEqual(boundary["delta_extension"], "EXPERIMENTAL_EXTENSION_DEFERRED")

    def test_provider_neutral_and_safety_boundaries_remain_closed(self):
        boundary = self.document["admission_boundary"]
        self.assertTrue(boundary["operation_definition_is_provider_neutral"])
        self.assertEqual(boundary["default_renderer"], "NOT_SELECTED")
        self.assertFalse(boundary["architecture_authority"])
        self.assertEqual(boundary["agent_reach"], "NO_CHANGE")
        self.assertEqual(boundary["authenticated_channel_admission"], "NO_CHANGE")
        self.assertEqual(boundary["live_external_invocation"], "OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(boundary["task151"], "FORBIDDEN")

    def test_future_versions_require_new_compatibility_check(self):
        policy = self.document["pin_policy"]
        self.assertFalse(policy["automatic_update"])
        self.assertTrue(policy["future_version_requires_compatibility_check"])
        self.assertTrue(policy["moving_main_is_not_compatibility_binding"])


if __name__ == "__main__":
    unittest.main()
