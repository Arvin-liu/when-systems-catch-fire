import copy
import json
import unittest

from tools.validate_task150_step09_environment_admission import ARTIFACT_PATH, admission_result, validate


class Task150Step09EnvironmentAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_policy_and_observation_pass(self):
        self.assertEqual(validate(self.document), [])
        self.assertEqual(self.document["environment_observation"]["provider"]["doctor"], "PASS")

    def test_present_environment_can_run_bounded_read_only(self):
        self.assertEqual(admission_result(True, True), "RUN_BOUNDED_READ_ONLY")
        self.assertEqual(self.document["admission_policy"]["present_provider"], "RUN_BOUNDED_READ_ONLY")

    def test_absent_provider_or_runtime_returns_unavailable(self):
        self.assertEqual(admission_result(False, True), "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT")
        self.assertEqual(admission_result(True, False), "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT")
        self.assertEqual(admission_result(False, False), "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT")

    def test_no_install_is_fail_closed(self):
        self.assertFalse(self.document["admission_policy"]["automatic_system_install"])
        self.assertEqual(self.document["admission_policy"]["skill_install"], "EXPLICIT_REQUEST_ONLY")
        for case in self.document["simulated_admission_cases"]:
            self.assertFalse(case["system_install"])
        mutated = copy.deepcopy(self.document)
        mutated["admission_policy"]["automatic_system_install"] = True
        self.assertTrue(validate(mutated))

    def test_provider_selection_is_not_permission(self):
        self.assertEqual(self.document["admission_policy"]["scope"], "PROVIDER_SELECTION_IS_NOT_PERMISSION")
        self.assertEqual(self.document["admission_policy"]["alternate_provider"], "ROUTE_ONLY_IF_EXPLICITLY_ADMITTED")

    def test_current_and_auth_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["current_admission"], "NOT_ADMITTED")
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")

    def test_agent_reach_and_task_scope_remain_frozen(self):
        self.assertEqual(self.document["scope_freeze"]["agent_reach"], "NO_CHANGE")
        self.assertEqual(self.document["scope_freeze"]["task150_scope"], "ARCHIFY_ONLY")
        self.assertEqual(self.document["scope_freeze"]["installation"], "NO_INSTALL_OR_AUTO_UPGRADE")


if __name__ == "__main__":
    unittest.main()
