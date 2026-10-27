import copy
import json
import unittest

from tools.validate_task149_step11_agent_reach_health_capability_probe import ARTIFACT_PATH, validate


class Task149Step11AgentReachHealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_all_doctor_channels_and_capabilities_are_explicit(self):
        self.assertEqual(len(self.document["channel_health"]), 15)
        self.assertEqual(len(self.document["capability_detection"]), 17)
        self.assertTrue(all(entry["declared_backends"] and entry["detected_backends"] for entry in self.document["channel_health"]))

    def test_health_is_not_acquisition(self):
        self.assertTrue(self.document["doctor_evidence"]["doctor_success_is_not_acquisition_success"])
        self.assertTrue(self.document["health_semantics"]["detected_backend_is_not_invocation_success"])

    def test_authenticated_capabilities_fail_closed(self):
        auth_ids = {"read_twitter_x", "read_reddit", "read_xiaohongshu", "read_instagram", "read_facebook", "read_authenticated_linkedin", "read_authenticated_xueqiu"}
        records = {entry["capability_id"]: entry for entry in self.document["capability_detection"]}
        self.assertTrue(all(records[key]["status"] in {"AUTH_REQUIRED", "OWNER_APPROVAL_REQUIRED"} for key in auth_ids))

    def test_public_statuses_keep_environment_reasons(self):
        records = {entry["channel"]: entry for entry in self.document["channel_health"]}
        self.assertEqual(records["web"]["acquisition_status"], "AVAILABLE_READ_ONLY")
        self.assertEqual(records["exa_search"]["acquisition_status"], "ENVIRONMENT_MISSING")
        self.assertEqual(records["github"]["acquisition_status"], "AUTH_REQUIRED")

    def test_safety_and_boundaries_are_closed(self):
        safety = self.document["safety_evidence"]
        self.assertEqual(safety["credential_content_access"], "NONE")
        self.assertFalse(safety["cookie_or_session_access"])
        self.assertFalse(safety["system_install"])
        self.assertEqual(self.document["boundaries"]["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")

    def test_mutated_health_status_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["channel_health"][0]["acquisition_status"] = "AVAILABLE_READ_ONLY"
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
