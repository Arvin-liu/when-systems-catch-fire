import copy
import json
import unittest

from tools.validate_task150_step04_viewport_residual_repair import ARTIFACT_PATH, validate


class Task150Step04ViewportResidualRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes_fail_closed_validation(self):
        self.assertEqual(validate(self.document), [])

    def test_baseline_keeps_all_six_task149_residuals(self):
        residuals = self.document["baseline_reproduction"]["visual_check"]["residuals"]
        self.assertEqual(len(residuals), 6)
        self.assertEqual(self.document["baseline_reproduction"]["visual_check"]["diagnostics"], 6)
        self.assertTrue(all(item["ok"] is False for item in residuals))

    def test_geometry_repair_preserves_topology_and_provenance_binding(self):
        adapter = self.document["adapter"]
        self.assertTrue(adapter["topology_unchanged"])
        self.assertTrue(adapter["geometry_repair_only"])
        self.assertEqual(adapter["viewBox"], [1650, 420])
        self.assertEqual(adapter["component_size"], [190, 28])

    def test_standalone_pass_is_separate_from_delta_shell_result(self):
        self.assertEqual(self.document["repair_validation"]["standalone_delivery"]["status"], "PASS")
        self.assertEqual(self.document["repair_validation"]["standalone_visual_check"]["status"], "PASS")
        self.assertEqual(self.document["repair_validation"]["delta_compare"]["semantic_checks"], {"total": 28, "passed": 28})
        self.assertEqual(self.document["repair_validation"]["delta_visual_check"]["status"], "FAIL_UPSTREAM_WRAPPER")

    def test_delta_residual_cannot_be_relabelled_as_a_pass(self):
        mutated = copy.deepcopy(self.document)
        mutated["repair_validation"]["delta_visual_check"]["status"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_upstream_blocker_is_not_fixed_by_forbidden_mutation(self):
        forbidden = self.document["adapter"]["forbidden_changes"]
        self.assertIn("no upstream fork or source mutation", forbidden)
        self.assertIn("no CSS override or overflow hiding", forbidden)
        self.assertIn("no filler element, tiny-font or viewport-specific concealment", forbidden)
        mutated = copy.deepcopy(self.document)
        mutated["upstream_blocker"]["confirmed"] = False
        self.assertTrue(validate(mutated))

    def test_current_auth_and_live_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["current_admission"], "NOT_ADMITTED")
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")


if __name__ == "__main__":
    unittest.main()
