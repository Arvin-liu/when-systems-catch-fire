import copy
import json
import unittest

from tools.validate_task149_step09_agent_reach_channel_matrix import ARTIFACT_PATH, validate


class Task149Step09AgentReachChannelMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_public_and_authenticated_are_separate(self):
        public = {entry["capability_id"] for entry in self.document["capabilities"] if entry["scope"] == "PUBLIC_NO_AUTH_CANDIDATE"}
        authenticated = {entry["capability_id"] for entry in self.document["capabilities"] if entry["scope"] == "AUTHENTICATED_SESSION_BEARING"}
        self.assertTrue({"read_public_web_page", "read_rss_atom", "read_public_v2ex"}.issubset(public))
        self.assertEqual(authenticated, {"read_twitter_x", "read_reddit", "read_xiaohongshu", "read_instagram", "read_facebook", "read_authenticated_linkedin", "read_authenticated_xueqiu"})

    def test_github_is_auth_required_even_for_public_target(self):
        github = [entry for entry in self.document["capabilities"] if entry["channel"] == "github"]
        self.assertEqual({entry["status"] for entry in github}, {"AUTH_REQUIRED"})

    def test_zero_auth_statuses_are_channel_specific(self):
        statuses = {entry["capability_id"]: entry["status"] for entry in self.document["capabilities"]}
        self.assertEqual(statuses["read_public_web_page"], "AVAILABLE_READ_ONLY")
        self.assertEqual(statuses["read_rss_atom"], "AVAILABLE_READ_ONLY")
        self.assertEqual(statuses["search_public_web"], "ENVIRONMENT_MISSING")
        self.assertEqual(statuses["read_public_youtube_metadata_or_transcript"], "ENVIRONMENT_MISSING")

    def test_authenticated_capabilities_fail_closed(self):
        for entry in self.document["capabilities"]:
            if entry["scope"] == "AUTHENTICATED_SESSION_BEARING":
                self.assertIn(entry["status"], {"AUTH_REQUIRED", "OWNER_APPROVAL_REQUIRED"})
        self.assertEqual(self.document["boundaries"]["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")

    def test_provider_local_policy_is_not_inherited(self):
        self.assertTrue(all(entry["provider_local_policy_inherited"] is False for entry in self.document["capabilities"]))

    def test_mutated_auth_status_fails(self):
        mutated = copy.deepcopy(self.document)
        next(entry for entry in mutated["capabilities"] if entry["capability_id"] == "read_twitter_x")["status"] = "AVAILABLE_READ_ONLY"
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
