from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, GoalDriftGuard, GoalRecord, sha256_json


NOW = "2026-08-21T12:00:00+08:00"


def make_goal(source: str = "OWNER_DECLARED") -> GoalRecord:
    provenance = AuthorityProvenance(source, "owner.synthetic" if source == "OWNER_DECLARED" else "system.synthetic", "auth-drift", "drift test", authorized=source == "OWNER_DECLARED")
    return GoalRecord("goal-drift-test", "intent-drift-test", "Drift test objective", "owner.synthetic", "contract-drift-test", provenance, status="ACTIVE" if source == "OWNER_DECLARED" else "PROPOSED", created_at=NOW, updated_at=NOW)


class DriftGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = GoalDriftGuard()

    def report(self, goal: GoalRecord, *, objective: str | None = None, expected: tuple[str, ...] = ("a",), observed: tuple[str, ...] = ("a",), observed_owner: bool = False, superseded: str | None = None, memory: bool = False, handoff_match: bool = True):
        owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-owner", "observed owner", authorized=True) if observed_owner else None
        expected_handoff = sha256_json({"handoff": "expected"})
        observed_handoff = expected_handoff if handoff_match else sha256_json({"handoff": "other"})
        return self.guard.inspect("report-drift", goal, objective or goal.objective_digest(), expected, observed, observed_provenance=owner, superseded_reference=superseded, memory_conflict=memory, expected_handoff_identity_digest=expected_handoff, observed_handoff_identity_digest=observed_handoff, created_at=NOW)

    def test_clear_handoff(self) -> None:
        self.assertEqual(self.report(make_goal()).outcome, "CLEAR")

    def test_objective_and_acceptance_loss_pause(self) -> None:
        report = self.report(make_goal(), objective=sha256_json({"changed": True}), observed=())
        self.assertEqual(report.outcome, "PAUSE_RECONCILE")
        self.assertIn("objective_digest_mismatch", report.reasons)
        self.assertIn("acceptance_criteria_lost", report.reasons)

    def test_proposal_owner_escalation_requires_review(self) -> None:
        report = self.report(make_goal("SYSTEM_DERIVED_PROPOSAL"), observed_owner=True)
        self.assertEqual(report.outcome, "HUMAN_REVIEW")
        self.assertIn("proposal_to_owner_escalation", report.reasons)

    def test_memory_conflict_requires_review(self) -> None:
        self.assertEqual(self.report(make_goal(), memory=True).outcome, "HUMAN_REVIEW")

    def test_handoff_mismatch_pauses(self) -> None:
        report = self.report(make_goal(), handoff_match=False)
        self.assertEqual(report.outcome, "PAUSE_RECONCILE")
        self.assertIn("handoff_identity_mismatch", report.reasons)


if __name__ == "__main__":
    unittest.main()
