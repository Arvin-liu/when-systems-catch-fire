from __future__ import annotations

import unittest

from tools.validate_task141_current_state_sync import build_report


class Task141CurrentStateSyncTests(unittest.TestCase):
    def test_step14_current_state_sync_is_closed(self) -> None:
        report = build_report()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["current_identity"]["current_formal_task_ordinal"], 141)
        self.assertEqual(report["map_identity"]["current_map_version"], "0.15.0")
        self.assertEqual(report["surface_sync"]["required_surface_count"], 11)
        self.assertEqual(report["surface_sync"]["changed_surface_count"], 11)
        self.assertEqual(report["source_projections"]["live_state_dimensions"]["live_process_observation_status"], "OBSERVED")
        self.assertEqual(report["source_projections"]["live_state_dimensions"]["validated_completion_status"], "NOT_VALIDATED")


if __name__ == "__main__":
    unittest.main()
