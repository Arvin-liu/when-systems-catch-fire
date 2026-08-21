from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, ConflictCandidate, NextWorkCandidate, OwnerOverride, PriorityInputs, SteeringEngine


NOW = "2026-08-21T12:00:00+08:00"


def work(goal_id: str, *, rank: int | None = 1, permission: bool = True, budget: bool = True, blockers: tuple[str, ...] = (), unknowns: tuple[str, ...] = (), override: OwnerOverride | None = None) -> NextWorkCandidate:
    return NextWorkCandidate(
        ConflictCandidate(PriorityInputs(goal_id, rank, permission_eligible=permission, owner_override=override)),
        pack_ref="pack-synthetic",
        executor_ref="executor-synthetic",
        budget_available=budget,
        blockers=blockers,
        unknowns=unknowns,
    )


class WhyNextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SteeringEngine()
        owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "why-next", authorized=True)
        self.override = OwnerOverride("override-1", "owner-goal", 0, "Owner selected", owner, NOW)

    def test_trace_explains_owner_selection_and_skipped_goal(self) -> None:
        trace = self.engine.select_next("trace-1", "OVERRIDE_VS_AUTOMATION", [work("owner-goal", rank=50, override=self.override, unknowns=("owner_context",)), work("auto-goal", rank=0, blockers=("override_precedence",))], created_at=NOW)
        self.assertEqual(trace.selected_goal_id, "owner-goal")
        self.assertEqual(trace.owner_override_ref, "override-1")
        self.assertIn("telemetry score has no authority", trace.why_selected)
        self.assertEqual(trace.skipped_goals[0].goal_id, "auto-goal")
        self.assertTrue(trace.permission_budget_resource)
        self.assertIn("owner_context", trace.unknowns)

    def test_permission_failure_is_visible_without_inference(self) -> None:
        trace = self.engine.select_next("trace-2", "PERMISSION_VS_DEADLINE", [work("denied", permission=False, blockers=("permission_missing",), unknowns=("scope_unknown",))], created_at=NOW)
        self.assertIsNone(trace.selected_goal_id)
        self.assertIn("permission_ceiling", " ".join(trace.blockers))
        self.assertIn("scope_unknown", trace.unknowns)
        self.assertIn("No next action selected", trace.why_selected)

    def test_budget_is_part_of_skip_explanation(self) -> None:
        trace = self.engine.select_next("trace-3", "RESOURCE_CONTENTION", [work("budget-missing", budget=False, blockers=("budget_unavailable",))], created_at=NOW)
        self.assertIsNone(trace.selected_goal_id)
        self.assertIn("budget_unavailable", " ".join(trace.blockers))
        self.assertIn("budget-missing:budget=unavailable", trace.permission_budget_resource)

    def test_empty_candidate_set_is_rejected(self) -> None:
        with self.assertRaises(Exception):
            self.engine.select_next("trace-4", "RESOURCE_CONTENTION", [], created_at=NOW)


if __name__ == "__main__":
    unittest.main()
