from __future__ import annotations

import unittest

from agent_runtime.pilots.steering_portfolio_129 import run_pilot


class SteeringPilotTests(unittest.TestCase):
    def test_cross_domain_pilot_is_offline_and_deterministic(self) -> None:
        result = run_pilot()
        self.assertTrue(result["offline_only"])
        self.assertEqual(result["selected_goal_id"], "goal-writing")
        self.assertEqual(len(result["domains"]), 7)
        self.assertTrue(result["durability"]["replay_same_selection"])

    def test_run_pass_does_not_complete_goal(self) -> None:
        completion = run_pilot()["completion"]
        self.assertEqual(completion["run_pass_outcome"], "UNVERIFIABLE")
        self.assertEqual(completion["owner_independent_outcome"], "SATISFIED")
        self.assertEqual(completion["goal_status_after_owner_decision"], "SATISFIED")

    def test_blocked_permission_superseded_and_unavailable_cases_remain_ineligible(self) -> None:
        boundaries = run_pilot()["candidate_boundaries"]
        for goal_id in ("goal-repository", "goal-knowledge", "goal-superseded", "goal-unavailable"):
            self.assertFalse(boundaries[goal_id]["eligible"], goal_id)


if __name__ == "__main__":
    unittest.main()
