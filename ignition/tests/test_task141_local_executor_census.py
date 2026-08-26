from __future__ import annotations

import unittest

from tools.validate_task141_local_executor_census import run_validation


class Task141LocalExecutorCensusTests(unittest.TestCase):
    def test_fresh_matrix_has_no_authorized_live_family(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["candidate_count"], 14)
        self.assertEqual(result["agentic_executor_count"], 5)
        self.assertEqual(result["admitted_executor_count"], 1)
        self.assertEqual(result["capability_selected_executor_id"], "external.codex")
        self.assertEqual(result["live_selection_status"], "NO_AUTHORIZED_FAMILY")
        self.assertEqual(result["codex_same_family_retry"], "FORBIDDEN_BLIND_RETRY")
        self.assertFalse(result["live_inference_started"])


if __name__ == "__main__":
    unittest.main()
