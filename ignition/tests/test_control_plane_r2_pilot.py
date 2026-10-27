from __future__ import annotations

import unittest

from agent_runtime.pilots.control_plane_r2 import run_pilot


class ControlPlaneR2PilotTests(unittest.TestCase):
    def test_five_child_offline_pilot_and_adversarial_matrix(self) -> None:
        result = run_pilot()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(sorted(result["children"]), ["pilot-a", "pilot-b", "pilot-c", "pilot-d", "pilot-e"])
        self.assertEqual(result["scheduler"]["max_concurrent_observed"], 2)
        self.assertTrue(all(result["adversarial"].values()))
        self.assertIn("cannot establish external success", result["driver_console"]["human"])


if __name__ == "__main__":
    unittest.main()
