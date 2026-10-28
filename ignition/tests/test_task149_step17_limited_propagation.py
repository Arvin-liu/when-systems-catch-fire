import copy
import json
import unittest

from tools.validate_task149_step17_limited_propagation import ARTIFACT_PATH, validate


class Task149Step17LimitedPropagationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_recorded_step17_propagation_passes(self):
        self.assertEqual([], validate(self.document))

    def test_missing_registered_surface_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["surface_decisions"] = [
            item for item in mutated["surface_decisions"] if item["surface_id"] != "human.readme"
        ]
        self.assertTrue(any("exactly the synchronization registry" in error for error in validate(mutated)))

    def test_readme_change_cannot_be_hidden_as_no_change(self):
        mutated = copy.deepcopy(self.document)
        next(item for item in mutated["surface_decisions"] if item["surface_id"] == "human.readme")["decision"] = "CHANGE"
        errors = validate(mutated)
        self.assertTrue(any("human.readme must remain NO_CHANGE_WITH_REASON" in error for error in errors), errors)

    def test_nonimpact_proof_scope_is_fail_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["front_door_nonimpact_proof"]["scope"] = "CURRENT"
        errors = validate(mutated)
        self.assertTrue(any("DRAFT_BRANCH_ONLY" in error for error in errors), errors)

    def test_state_changelog_must_be_the_only_registered_change(self):
        mutated = copy.deepcopy(self.document)
        next(item for item in mutated["surface_decisions"] if item["surface_id"] == "release.state_changelog")["decision"] = "NO_CHANGE_WITH_REASON"
        errors = validate(mutated)
        self.assertTrue(any("release.state_changelog must be the only changed" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
