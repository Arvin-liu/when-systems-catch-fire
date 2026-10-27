import copy
import json
import unittest

from tools.validate_task149_step14_authenticated_channel_fail_closed import ARTIFACT_PATH, validate


class Task149Step14AuthFailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_all_required_channels_are_fixtures(self):
        self.assertEqual({f["channel"] for f in self.document["fixtures"]}, {"twitter", "reddit", "xiaohongshu", "instagram", "facebook"})
        self.assertTrue(self.document["automated_regression"]["enabled"])

    def test_every_fixture_rejects_without_call(self):
        for fixture in self.document["fixtures"]:
            self.assertEqual(fixture["expected_status"], "AUTH_REQUIRED")
            self.assertEqual(fixture["actual_action"], "REJECT_WITHOUT_CALL")

    def test_no_implicit_login_or_cookie_path(self):
        for fixture in self.document["fixtures"]:
            self.assertFalse(fixture["browser_login_invoked"])
            self.assertFalse(fixture["cookie_read"])
            self.assertFalse(fixture["cookie_imported"])
            self.assertFalse(fixture["authenticated_mcp_started"])
            self.assertFalse(fixture["existing_login_state_used"])

    def test_global_forbidden_authority_is_closed(self):
        self.assertFalse(self.document["forbidden_implicit_authority"]["automatic_browser_login"])
        self.assertFalse(self.document["forbidden_implicit_authority"]["automatic_chrome_cookie_read"])
        self.assertFalse(self.document["forbidden_implicit_authority"]["existing_login_state_is_implicit_authorization"])

    def test_no_real_authenticated_calls(self):
        self.assertTrue(self.document["fixture_only"])
        self.assertEqual(self.document["real_authenticated_calls"], 0)
        self.assertFalse(self.document["current_explicit_credential_admission"])

    def test_mutated_fixture_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["fixtures"][0]["expected_status"] = "OWNER_APPROVAL_REQUIRED"
        self.assertTrue(validate(mutated))

    def test_authenticated_boundary_is_closed(self):
        self.assertEqual(self.document["boundaries"]["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")


if __name__ == "__main__":
    unittest.main()
