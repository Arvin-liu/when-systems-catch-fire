import copy
import json
import unittest

from tools.validate_task150_step05_visual_review import ARTIFACT_PATH, validate


class Task150Step05VisualReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes_and_files_are_bound(self):
        self.assertEqual(validate(self.document), [])
        self.assertEqual(len(self.document["evidence_files"]), 12)

    def test_automated_and_manual_layers_are_separate(self):
        automated = self.document["automated_review"]
        agent = self.document["agent_visual_inspection"]
        self.assertEqual(automated["standalone_visual_review"], "pending")
        self.assertEqual(automated["delta_visual_check"], "FAIL_UPSTREAM_WRAPPER")
        self.assertEqual(agent["status"], "STANDALONE_PASS_WITH_LIMITS_DELTA_BLOCKED")

    def test_owner_acceptance_cannot_be_auto_promoted(self):
        mutated = copy.deepcopy(self.document)
        mutated["owner_visual_acceptance"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_delta_three_panel_readability_remains_blocked(self):
        checks = self.document["agent_visual_inspection"]["checks"]
        self.assertEqual(checks["delta_three_panel_readability"], "NOT_ACCEPTED_UPSTREAM_WRAPPER_OVERFLOW_AND_THEME_RESOLUTION")
        mutated = copy.deepcopy(self.document)
        mutated["agent_visual_inspection"]["checks"]["delta_three_panel_readability"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_visual_evidence_digests_are_not_optional(self):
        mutated = copy.deepcopy(self.document)
        mutated["evidence_files"][0]["sha256"] = "0" * 64
        self.assertTrue(validate(mutated))

    def test_browser_policy_fallback_is_explicit(self):
        inspection = self.document["agent_visual_inspection"]
        self.assertEqual(inspection["method"], "LOCAL_PNG_INSPECTION_AFTER_BROWSER_FILE_URL_POLICY_BLOCK")
        self.assertEqual(inspection["browser_observation"], "IN_APP_BROWSER_REJECTED_LOCAL_FILE_URL; NO_POLICY_BYPASS")

    def test_scope_and_current_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["installation"], "NO_INSTALL_OR_AUTO_UPGRADE")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["current_admission"], "NOT_ADMITTED")


if __name__ == "__main__":
    unittest.main()
