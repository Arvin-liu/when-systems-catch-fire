from __future__ import annotations

import unittest

from tools.validate_task141_root_cause_archaeology import run_validation


class Task141RootCauseArchaeologyTests(unittest.TestCase):
    def test_public_audit_blocks_blind_codex_retry(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["root_cause_status"], "ROOT_CAUSE_NARROWED_NOT_CONFIRMED")
        self.assertEqual(result["codex_same_family_retry"], "FORBIDDEN_BLIND_RETRY")
        self.assertTrue(result["public_flags_present"])
        self.assertFalse(result["live_inference_started"])


if __name__ == "__main__":
    unittest.main()
