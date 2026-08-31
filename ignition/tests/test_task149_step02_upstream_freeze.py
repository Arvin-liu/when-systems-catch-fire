import copy
import json
import unittest

from tools.validate_task149_step02_upstream_freeze import ARTIFACT_PATH, validate


class Task149Step02UpstreamFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_freeze_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_archify_revision_drift_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["upstreams"][0]["observed_main_sha"] = "0" * 40
        self.assertTrue(any("Archify" in error for error in validate(mutated)))

    def test_provider_local_policy_is_not_global_policy(self):
        self.assertEqual(self.document["selection_and_admission_boundary"]["provider_local_policy_inheritance"], "FORBIDDEN")

    def test_pinned_agent_reach_dependency_blocker_is_not_hidden(self):
        health = self.document["upstreams"][1]["health"]
        self.assertEqual(health["pinned_source_status"], "BLOCKED_DEPENDENCY")
        self.assertFalse(health["pinned_source_install_performed"])


if __name__ == "__main__":
    unittest.main()
