from __future__ import annotations

import unittest

from tools import record_current_surface_determinism as determinism


class CurrentSurfaceDeterminismTests(unittest.TestCase):
    def test_recorded_two_pass_hashes_match_current_outputs(self) -> None:
        self.assertEqual(determinism.check_report(), [])


if __name__ == "__main__":
    unittest.main()
