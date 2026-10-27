from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, GoalEpisodeBinder, GoalRecord, SteeringValidationError


NOW = "2026-08-21T12:00:00+08:00"


def goal(status: str = "ACTIVE") -> GoalRecord:
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "binding test", authorized=True)
    return GoalRecord("goal-binding", "intent-binding", "Bound synthetic objective", "owner.synthetic", "contract-binding", owner, status=status, created_at=NOW, updated_at=NOW)


class EpisodeGoalBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.binder = GoalEpisodeBinder()

    def test_episode_and_pass_run_do_not_satisfy_goal(self) -> None:
        binding = self.binder.bind(goal(), "episode-binding", ("run-a", "run-b"), secondary_goal_ids=("goal-secondary",), created_at=NOW)
        self.binder.update_episode(binding.binding_id, "EPISODE_COMPLETED_VALIDATED", updated_at=NOW)
        updated = self.binder.record_run_outcome(binding.binding_id, "run-a", "PASS", updated_at=NOW)
        receipt = self.binder.reconcile_run_result(binding.binding_id, "run-a", "PASS")
        self.assertEqual(updated.goal_status_at_bind, "ACTIVE")
        self.assertFalse(receipt["goal_status_mutated"])
        self.assertEqual(receipt["completion_inference"], "INDEPENDENT_CONTRACT_REQUIRED")

    def test_handoff_preserves_run_identity_digest(self) -> None:
        binding = self.binder.bind(goal(), "episode-handoff", ("run-a",), created_at=NOW)
        handed = self.binder.handoff(binding.binding_id, "run-a", "instance-2", updated_at=NOW)
        self.assertEqual(handed.handoff_identity_digest, binding.handoff_identity_digest)
        self.assertEqual(handed.handoff_identities[0].run_id, "run-a")
        self.assertEqual(handed.handoff_identities[0].sequence, 1)

    def test_run_outside_binding_is_rejected(self) -> None:
        binding = self.binder.bind(goal(), "episode-scope", ("run-a",), created_at=NOW)
        with self.assertRaises(SteeringValidationError):
            self.binder.record_run_outcome(binding.binding_id, "run-outside", "PASS", updated_at=NOW)

    def test_goal_status_is_captured_not_derived(self) -> None:
        binding = self.binder.bind(goal("BLOCKED"), "episode-blocked", ("run-a",), created_at=NOW)
        self.assertEqual(binding.goal_status_at_bind, "BLOCKED")
        self.assertEqual(binding.completion_inference, "INDEPENDENT_CONTRACT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
