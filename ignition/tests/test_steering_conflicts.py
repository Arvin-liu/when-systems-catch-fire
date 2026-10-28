from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, ConflictArbiter, ConflictCandidate, OwnerOverride, PriorityInputs


NOW = "2026-08-21T12:00:00+08:00"


def candidate(goal_id: str, *, owner_rank: int | None = 1, permission: bool = True, resource: bool = True, executor: bool = True, status: str = "ACTIVE", stale: bool = False, superseded: bool = False, safety: bool = False, approval: bool = False, group: str | None = None, override: OwnerOverride | None = None) -> ConflictCandidate:
    return ConflictCandidate(PriorityInputs(goal_id, owner_rank, resource_available=resource, permission_eligible=permission, owner_override=override, approval_required=approval, risk_level="HIGH" if safety else "LOW"), intent_status=status, executor_available=executor, stale=stale, superseded=superseded, safety_critical=safety, mutually_exclusive_group=group)


class ConflictArbitrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.arbiter = ConflictArbiter()
        self.owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "explicit arbitration", authorized=True)

    def test_permission_ceiling_beats_overdue_deadline(self) -> None:
        receipt = self.arbiter.arbitrate("arb-1", "PERMISSION_VS_DEADLINE", [candidate("denied", permission=False), candidate("fallback", owner_rank=2)], created_at=NOW)
        self.assertEqual(receipt.outcome, "SELECTED")
        self.assertEqual(receipt.selected_goal_id, "fallback")
        self.assertTrue(any("permission_ineligible" in reason for reason in receipt.reasons))

    def test_safety_conflict_requires_human_review(self) -> None:
        receipt = self.arbiter.arbitrate("arb-2", "DEADLINE_VS_SAFETY", [candidate("unsafe", safety=True, approval=True), candidate("safe", owner_rank=2)], created_at=NOW)
        self.assertEqual(receipt.outcome, "HUMAN_REVIEW")
        self.assertIsNone(receipt.selected_goal_id)

    def test_owner_override_wins_over_automation_and_is_visible(self) -> None:
        override = OwnerOverride("override-1", "owner", 0, "Owner selected", self.owner, NOW)
        receipt = self.arbiter.arbitrate("arb-3", "OVERRIDE_VS_AUTOMATION", [candidate("owner", owner_rank=50, override=override), candidate("automation", owner_rank=0)], created_at=NOW)
        self.assertEqual(receipt.selected_goal_id, "owner")
        self.assertTrue(receipt.decisions[0].owner_override_visible)

    def test_superseded_intent_and_unavailable_executor_reconcile(self) -> None:
        for index, conflict_type, item in ((4, "SUPERSEDED_INTENT", candidate("old", status="SUPERSEDED", superseded=True)), (5, "EXECUTOR_UNAVAILABLE", candidate("offline", executor=False))):
            receipt = self.arbiter.arbitrate(f"arb-{index}", conflict_type, [item], created_at=NOW)
            self.assertEqual(receipt.outcome, "RECONCILIATION_REQUIRED")
            self.assertTrue(receipt.reconciliation_required)

    def test_mutually_exclusive_selection_is_deterministic(self) -> None:
        receipt = self.arbiter.arbitrate("arb-6", "MUTUALLY_EXCLUSIVE_GOALS", [candidate("first", owner_rank=1, group="one"), candidate("second", owner_rank=2, group="one")], created_at=NOW)
        self.assertEqual(receipt.selected_goal_id, "first")
        self.assertIn("mutually_exclusive_losers_deferred", receipt.reasons)

    def test_duplicate_candidates_fail_closed(self) -> None:
        with self.assertRaises(Exception):
            self.arbiter.arbitrate("arb-7", "RESOURCE_CONTENTION", [candidate("same"), candidate("same")], created_at=NOW)


if __name__ == "__main__":
    unittest.main()
