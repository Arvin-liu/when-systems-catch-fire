from __future__ import annotations

import unittest

from tools.validate_task141_live_policy_freeze import run_validation


class Task141LivePolicyFreezeTests(unittest.TestCase):
    def test_policy_has_bounded_caps_and_no_unauthorized_probe(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["live_probe_authorization"], "NO_AUTHORIZED_FAMILY")
        self.assertEqual(result["authorized_families"], [])
        self.assertEqual(result["max_distinct_executor_families"], 2)
        self.assertEqual(result["max_attempts_per_family"], 1)
        self.assertEqual(result["validated_completion_count"], 0)


if __name__ == "__main__":
    unittest.main()
