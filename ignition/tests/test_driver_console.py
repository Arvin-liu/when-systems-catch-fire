from __future__ import annotations

import unittest

from agent_runtime.driver_console import DriverConsoleError, build_driver_snapshot, render_driver_console


def sources() -> dict[str, object]:
    return {
        "scheduler": {"episode_id": "episode-console", "terminal": None, "children": {"run-a": {"status": "RUNNING"}}, "max_concurrent_observed": 2, "budget_usage": {"actions": 1}},
        "queue": {"depth": 2, "paused": False, "state_counts": {"QUEUED": 2}, "backpressure_events": 1},
        "health": {"lease_count": 2, "effective_status_counts": {"HEALTHY": 1, "STALE": 1}},
        "resources": {"active_count": 1, "waiting_count": 1, "unknown_side_effect_policy": "NO_OVERLAP_NO_AUTOMATIC_FAILOVER"},
        "dispatch": {"record_count": 2, "state_counts": {"REQUIRES_RECONCILIATION": 1, "RUNNING": 1}},
        "memory": {"generation": 3, "active_count": 2, "capsule_stale": True},
        "policy": {"digest": "a" * 64, "status": "EFFECTIVE_NARROWED", "claim_ceiling": "bounded policy only"},
    }


class DriverConsoleTests(unittest.TestCase):
    def test_machine_and_human_projection_prioritize_reconciliation(self) -> None:
        snapshot = build_driver_snapshot(sources())
        self.assertEqual(snapshot["overall_state"], "RUNNING")
        self.assertIn("Reconcile", snapshot["next_action"])
        self.assertGreaterEqual(len(snapshot["open_obligations"]), 4)
        text = render_driver_console(snapshot)
        self.assertIn("Driver Console", text)
        self.assertIn("external dispatch reconciliation", text)
        self.assertIn("cannot establish external success", text)

    def test_checkpoint_terminal_and_secret_input_fail_closed(self) -> None:
        value = sources()
        value["scheduler"] = {"episode_id": "episode-console", "terminal": {"state": "CHECKPOINTED_RESUMABLE"}, "children": {"run-a": {"status": "CHECKPOINTED_RESUMABLE"}}}
        value["dispatch"] = {"record_count": 0, "state_counts": {}}
        value["health"] = {"lease_count": 1, "effective_status_counts": {"HEALTHY": 1}}
        value["resources"] = {"active_count": 0, "waiting_count": 0, "unknown_side_effect_policy": "NO_OVERLAP_NO_AUTOMATIC_FAILOVER"}
        snapshot = build_driver_snapshot(value)
        self.assertIn("explicitly resume", snapshot["next_action"])
        value["policy"] = {"digest": "prompt material", "status": "EFFECTIVE_NARROWED", "claim_ceiling": "bounded"}
        with self.assertRaises(DriverConsoleError):
            build_driver_snapshot(value)


if __name__ == "__main__":
    unittest.main()
