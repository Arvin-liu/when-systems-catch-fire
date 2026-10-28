import copy
import json
import unittest

from tools.validate_task149_step10_agent_reach_safety import ARTIFACT_PATH, validate


class Task149Step10AgentReachSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_real_path_and_empty_isolation(self):
        environment = self.document["ephemeral_environment"]
        self.assertTrue(environment["all_paths_symlink_free"])
        self.assertEqual(environment["before_file_count"], 0)
        self.assertEqual(environment["after_file_count"], 0)
        self.assertEqual(environment["credential_or_cookie_content_access"], "NONE")

    def test_dry_run_proves_no_system_change(self):
        dry_run = self.document["commands"]["install_dry_run"]
        self.assertEqual(dry_run["status"], "NO_CHANGE_DRY_RUN")
        self.assertFalse(dry_run["system_install_requested"])
        self.assertFalse(dry_run["system_changes_performed"])
        self.assertTrue(dry_run["output_explicitly_says_no_changes"])

    def test_mutation_audit_is_closed(self):
        mutation = self.document["mutation_audit"]
        self.assertTrue(mutation["command_argv_forbidden_tokens_absent"])
        self.assertTrue(all(value is False for key, value in mutation.items() if key != "command_argv_forbidden_tokens_absent"))

    def test_authenticated_boundary_is_closed(self):
        self.assertEqual(self.document["boundaries"]["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")

    def test_mutated_system_install_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["mutation_audit"]["system_install_performed"] = True
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
