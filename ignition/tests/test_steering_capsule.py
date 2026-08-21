from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, GoalRecord, IntentCapsule, IntentRecord, SteeringValidationError, build_intent_capsule


NOW = "2026-08-21T12:00:00+08:00"


def records() -> tuple[IntentRecord, GoalRecord]:
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "capsule test", authorized=True)
    intent = IntentRecord("intent-capsule", "Bound intent", "owner.synthetic", owner, status="ACTIVE", created_at=NOW, updated_at=NOW)
    goal = GoalRecord("goal-capsule", intent.intent_id, "Bound goal", "owner.synthetic", "contract-capsule", owner, status="ACTIVE", created_at=NOW, updated_at=NOW)
    return intent, goal


class IntentCapsuleTests(unittest.TestCase):
    def test_capsule_round_trip_and_report_boundary(self) -> None:
        intent, goal = records()
        capsule = build_intent_capsule(intent, goal, success_criteria=("criterion-a",), permission_summary=("repo.read",), report_contract_refs=("report-1",), created_at=NOW)
        self.assertEqual(IntentCapsule.from_dict(capsule.to_dict()), capsule)
        self.assertFalse(capsule.executor_report_boundary()["canonical_mutation_allowed"])

    def test_goal_must_bind_to_intent(self) -> None:
        intent, goal = records()
        other = GoalRecord("goal-other", "intent-other", "Other goal", "owner.synthetic", "contract-other", goal.provenance, status="ACTIVE", created_at=NOW, updated_at=NOW)
        with self.assertRaises(SteeringValidationError):
            build_intent_capsule(intent, other, success_criteria=("criterion",), permission_summary=("repo.read",), report_contract_refs=("report",), created_at=NOW)

    def test_prompt_and_canonical_mutation_fields_are_rejected(self) -> None:
        intent, goal = records()
        with self.assertRaises(SteeringValidationError):
            build_intent_capsule(intent, goal, success_criteria=("prompt body",), permission_summary=("repo.read",), report_contract_refs=("report",), created_at=NOW)
        capsule = build_intent_capsule(intent, goal, success_criteria=("criterion",), permission_summary=("repo.read",), report_contract_refs=("report",), created_at=NOW)
        with self.assertRaises(SteeringValidationError):
            IntentCapsule(**{**capsule.__dict__, "executor_can_mutate_canonical": True})

    def test_capsule_keeps_blocker_and_temporal_refs_bounded(self) -> None:
        intent, goal = records()
        capsule = build_intent_capsule(intent, goal, success_criteria=("criterion",), permission_summary=("repo.read",), blocker_refs=("blocker-1",), temporal_refs=("window-1",), report_contract_refs=("report",), minimal_context_refs=("digest-1",), created_at=NOW)
        self.assertEqual(capsule.blocker_refs, ("blocker-1",))
        self.assertEqual(capsule.temporal_refs, ("window-1",))
        self.assertEqual(capsule.minimal_context_refs, ("digest-1",))


if __name__ == "__main__":
    unittest.main()
