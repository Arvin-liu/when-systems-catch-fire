import copy
import json
import unittest

from tools.validate_task149_step12_zero_auth_acquisition_smoke import ARTIFACT_PATH, validate


class Task149Step12ZeroAuthSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_public_read_successes_are_bounded(self):
        operations = {entry["operation_id"]: entry for entry in self.document["operations"]}
        self.assertEqual(operations["web_public_page_read"]["status"], "PASS")
        self.assertEqual(operations["rss_public_feed_read"]["returned_result_count"], 20)
        self.assertEqual(operations["bilibili_public_search"]["returned_result_count"], 12)
        self.assertEqual(operations["v2ex_public_hot_topics_read"]["returned_result_count"], 9)

    def test_github_and_exa_failures_are_not_pass(self):
        operations = {entry["operation_id"]: entry for entry in self.document["operations"]}
        self.assertEqual(operations["github_public_repository_read"]["status"], "AUTH_REQUIRED")
        self.assertEqual(operations["github_public_repository_search"]["status"], "AUTH_REQUIRED")
        self.assertEqual(operations["public_semantic_search"]["status"], "ENVIRONMENT_MISSING")

    def test_video_is_metadata_only(self):
        operation = next(entry for entry in self.document["operations"] if entry["operation_id"] == "youtube_public_metadata_read")
        self.assertEqual(operation["status"], "PASS_WITH_LIMITS")
        self.assertEqual(operation["returned_result_count"], 1)
        self.assertIn("transcript", operation["failure_reason"])

    def test_every_operation_has_provenance_and_hash(self):
        for operation in self.document["operations"]:
            self.assertEqual(operation["selected_provider"], "agent-reach")
            self.assertEqual(len(operation["bounded_content_hash"]), 64)
            self.assertFalse(operation["provenance"]["external_truth_claimed"])

    def test_no_authenticated_or_write_side_effects(self):
        self.assertFalse(self.document["authenticated_calls_attempted"])
        for operation in self.document["operations"]:
            self.assertFalse(operation["authenticated_call"])
            self.assertTrue(operation["side_effects"]["read_only"])
            self.assertFalse(operation["side_effects"]["external_write"])
            self.assertFalse(operation["side_effects"]["credential_or_cookie_access"])

    def test_environment_missing_is_valid_but_not_success(self):
        self.assertTrue(self.document["summary"]["environment_missing_is_valid_result"])
        mutated = copy.deepcopy(self.document)
        mutated["operations"][5]["status"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_authenticated_boundary_is_closed(self):
        self.assertEqual(self.document["boundaries"]["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")


if __name__ == "__main__":
    unittest.main()
