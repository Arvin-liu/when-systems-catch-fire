from __future__ import annotations

import unittest

from tools import validate_release_state_model as model


class ReleaseStateModelTests(unittest.TestCase):
    def test_static_model_is_valid(self) -> None:
        self.assertEqual(model.validate(), [])

    def test_authority_domains_are_separate(self) -> None:
        document = model.load_json(model.MODEL_PATH)
        domains = document["state_domains"]
        self.assertEqual(domains["content_owned"]["authority_class"], "FORMAL_COMMIT_CONTENT")
        self.assertEqual(domains["ref_observed_publication"]["authority_class"], "REMOTE_GIT_REF_OBSERVATION")
        self.assertEqual(domains["publication_witness"]["authority_class"], "CONTROL_REPOSITORY_RECEIPT")
        self.assertNotIn("PUBLISHED", domains["content_owned"]["states"])

    def test_runtime_transitions_cannot_create_formal_commit(self) -> None:
        document = model.load_json(model.MODEL_PATH)
        for transition in document["transition_rules"]:
            if transition["to_domain"] != "content_owned":
                self.assertFalse(transition["creates_formal_commit"], transition["transition_id"])

    def test_mutating_ref_authority_fails_closed(self) -> None:
        document = model.load_json(model.MODEL_PATH)
        document["state_domains"]["ref_observed_publication"]["authority_class"] = "FORMAL_COMMIT_CONTENT"
        self.assertTrue(any("ref_observed_publication authority" in error for error in model.validate(document)))


if __name__ == "__main__":
    unittest.main()
