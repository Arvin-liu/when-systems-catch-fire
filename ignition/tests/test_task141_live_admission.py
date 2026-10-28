from __future__ import annotations

import unittest

from tools.validate_task141_live_admission import run_validation


class Task141LiveAdmissionTests(unittest.TestCase):
    def test_no_family_means_no_dispatch(self) -> None:
        result = run_validation()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["admission_status"], "NO_AUTHORIZED_FAMILY")
        self.assertEqual(result["live_dispatch_calls"], 0)
        self.assertFalse(result["live_inference_started"])


if __name__ == "__main__":
    unittest.main()
