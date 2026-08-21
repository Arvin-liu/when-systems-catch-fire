from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, OwnerOverride, PriorityInputs, PriorityPolicy


NOW = "2026-08-21T12:00:00+08:00"


class PriorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "synthetic", authorized=True)
        self.policy = PriorityPolicy()

    def test_permission_ceiling_beats_deadline_and_rank(self) -> None:
        decision = self.policy.evaluate(PriorityInputs("goal-denied", 0, "DUE", 100, "LOW", True, False, False, 999, "OVERDUE"))
        self.assertFalse(decision.eligible)
        self.assertIn("permission_ineligible", decision.reasons)

    def test_owner_override_is_visible_and_retractable(self) -> None:
        override = OwnerOverride("override-1", "goal-override", 0, "explicit", self.owner, NOW)
        candidate = PriorityInputs("goal-override", 50, owner_override=override)
        decision = self.policy.evaluate(candidate)
        self.assertTrue(decision.owner_override_visible)
        self.assertTrue(decision.owner_override_retractable)
        self.assertFalse(self.policy.retract_override(override).active)

    def test_lexicographic_order_does_not_depend_on_score(self) -> None:
        candidates = [PriorityInputs("goal-b", 20, fairness_age=100), PriorityInputs("goal-a", 10, fairness_age=0)]
        ordered = self.policy.order(candidates)
        self.assertEqual([item.goal_id for item in ordered], ["goal-a", "goal-b"])
        self.assertTrue(all(item.authority == "LEXICOGRAPHIC_RULES_R1" for item in ordered))

    def test_blocked_high_priority_is_not_eligible(self) -> None:
        decision = self.policy.evaluate(PriorityInputs("goal-blocked", 0, "DUE", 100, "HIGH", True, True, True, 1000, "DUE", approval_required=True))
        self.assertFalse(decision.eligible)
        self.assertIn("blocked", decision.reasons)
        self.assertIn("high_risk_requires_explicit_approval", decision.reasons)

    def test_unknown_owner_rank_is_preserved_not_inferred(self) -> None:
        decision = self.policy.evaluate(PriorityInputs("goal-unknown", None, unknowns=("owner_rank",)))
        self.assertIn("unknown_inputs_preserved", decision.reasons)


if __name__ == "__main__":
    unittest.main()
