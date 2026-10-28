import copy
import json
import unittest

from tools.validate_task150_step12_front_door_restraint import ARTIFACT_PATH, validate


class Task150Step12FrontDoorRestraintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_front_doors_are_unchanged(self):
        self.assertEqual(validate(self.document), [])
        formal = self.document["formal_observation"]
        self.assertEqual(formal["task150_front_door_changed_paths"], [])
        self.assertFalse(formal["task150_root_readme_added"])
        self.assertFalse(formal["task150_readme_en_added"])
        self.assertFalse(formal["task150_product_added"])

    def test_no_provider_homepage_or_current_claim_was_added(self):
        scan = self.document["claim_scan"]
        self.assertFalse(scan["task150_added_provider_homepage_claim"])
        self.assertFalse(scan["task150_added_current_provider_claim"])
        self.assertFalse(scan["task150_added_default_renderer_claim"])
        self.assertFalse(scan["task150_added_public_capability_claim"])

    def test_front_door_drift_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["formal_observation"]["task150_front_door_changed_paths"] = ["README.md"]
        self.assertTrue(validate(mutated))

    def test_homepage_claim_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["claim_scan"]["task150_added_provider_homepage_claim"] = True
        self.assertTrue(validate(mutated))

    def test_current_and_default_renderer_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["current_admission"], "NOT_ADMITTED")
        self.assertEqual(scope["default_renderer"], "NOT_SELECTED")
        mutated = copy.deepcopy(self.document)
        mutated["scope_freeze"]["default_renderer"] = "ARCHIFY"
        self.assertTrue(validate(mutated))

    def test_owner_acceptance_is_not_inferred(self):
        self.assertEqual(self.document["claim_scan"]["human_front_door_acceptance"], "NOT_INFERRED")
        mutated = copy.deepcopy(self.document)
        mutated["claim_scan"]["human_front_door_acceptance"] = "ACCEPTED"
        self.assertTrue(validate(mutated))

    def test_external_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")


if __name__ == "__main__":
    unittest.main()
