import copy
import json
import unittest

from tools.validate_task150_step26_front_door_and_sync_surface_restraint import (
    ARTIFACT_PATH,
    EXPECTED_ALLOWED_STATEMENT,
    EXPECTED_README_AFTER_SHA,
    EXPECTED_README_BEFORE_SHA,
    EXPECTED_SYNC_SHA,
    validate,
)


class Task150Step26FrontDoorAndSyncSurfaceRestraintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_front_door_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_sync_registry_and_homepage_digests_are_pinned(self):
        self.assertEqual(self.document["synchronization_registry"]["sha256"], EXPECTED_SYNC_SHA)
        self.assertEqual(self.document["homepage"]["before_sha256"], EXPECTED_README_BEFORE_SHA)
        self.assertEqual(self.document["homepage"]["after_sha256"], EXPECTED_README_AFTER_SHA)

    def test_capability_addition_changes_only_homepage_usage_entry(self):
        decisions = self.document["surface_decisions"]
        self.assertEqual(len(decisions), 21)
        self.assertEqual([row["surface_id"] for row in decisions if row["decision"] == "CHANGE"], ["human.readme"])
        self.assertEqual(sum(row["decision"] == "NO_CHANGE_WITH_REASON" for row in decisions), 20)
        self.assertEqual(self.document["homepage"]["allowed_statement"], EXPECTED_ALLOWED_STATEMENT)

    def test_archify_brand_and_authority_claims_are_forbidden(self):
        public = self.document["public_expression"]
        self.assertEqual(public["homepage_default"], "NO_ARCHIFY_BRAND_PROMOTION")
        self.assertEqual(public["forbidden_claim_matches"], [])
        self.assertFalse(public["architecture_authority"])
        self.assertFalse(public["external_truth"])

    def test_tampered_surface_scope_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["surface_decisions"][1]["decision"] = "CHANGE"
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["homepage"]["allowed_statement"] = "Archify 是点火官方 renderer"
        self.assertTrue(validate(mutated))

    def test_no_delta_renderer_or_aesthetic_upgrade(self):
        self.assertEqual(self.document["scope_freeze"]["architecture_delta"], "EXPERIMENTAL_EXTENSION_DEFERRED")
        self.assertEqual(self.document["validation"]["default_renderer"], "NOT_SELECTED")
        self.assertEqual(self.document["public_expression"]["owner_aesthetic_endorsement"], "NOT_GRANTED_NOT_CLAIMED")

    def test_agent_auth_live_and_successor_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")
        self.assertEqual(scope["authenticated_channel_admission"], "NO_CHANGE")
        self.assertEqual(scope["live_external_invocation"], "OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["task151"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
