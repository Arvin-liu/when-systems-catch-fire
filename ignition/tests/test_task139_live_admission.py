from __future__ import annotations

import unittest

from tools.run_task139_live_admission import run_gate


class Task139LiveAdmissionTests(unittest.TestCase):
    def test_single_live_attempt_admission_is_bounded_without_inference(self) -> None:
        report = run_gate()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["census"]["selected_executor_id"], "external.codex")
        self.assertEqual(report["admission"]["status"], "ADMITTED")
        self.assertEqual(report["admission"]["effective_capabilities"], ["repo.read"])
        self.assertEqual(report["probe_calls"], 2)
        self.assertFalse(report["dispatch"]["inference_started"])
        self.assertTrue(report["filesystem"]["runtime_parent_separate_from_capture_parent"])
        self.assertTrue(report["filesystem"]["workspace_read_only_guard"])
        self.assertEqual(report["child_depth_guard"], "PASS_ONE_LEVEL_ONLY")
        self.assertEqual(report["validator_freeze"]["status"], "PASS")
        self.assertTrue(report["validator_freeze"]["self_test_is_not_live_result"])


if __name__ == "__main__":
    unittest.main()
