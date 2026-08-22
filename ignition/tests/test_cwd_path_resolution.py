from __future__ import annotations

import unittest

from tools.validate_cwd_path_resolution import build_receipt, run_cases


class CwdPathResolutionTests(unittest.TestCase):
    def test_targeted_fixtures_pass_from_all_required_cwd_boundaries(self) -> None:
        receipt = build_receipt(run_cases())
        self.assertEqual(receipt["status"], "PASS", receipt)
        self.assertEqual(receipt["target_count_per_case"], 5)
        self.assertEqual([row["case_id"] for row in receipt["cases"]], [
            "repository-root",
            "ignition-root",
            "temporary-cwd",
            "fresh-clone",
        ])
        self.assertTrue(receipt["root_contract"]["global_chdir"] is False)
        fresh = receipt["cases"][-1]
        self.assertTrue(fresh["head_match"])


if __name__ == "__main__":
    unittest.main()
