from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, CompletionContract, GoalRecord, GoalRegistry, evaluate_completion


NOW = "2026-08-21T12:00:00+08:00"


class CompletionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = CompletionContract("contract-c", ("receipt_present",), ("VALIDATOR_RECEIPT",), "VALIDATOR", ("run_pass", "tests_green"))
        owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "synthetic", authorized=True)
        self.goal = GoalRecord("goal-c", "intent-c", "Completion fixture", "fixture.public", self.contract.contract_id, owner, "ACTIVE", 1, None, NOW, NOW)
        self.validator = AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "validator.synthetic", "validator-1", "validator")

    def test_run_pass_is_not_completion(self) -> None:
        decision = evaluate_completion(self.goal, self.contract, {"run_pass": True}, authority=self.validator, decided_at=NOW)
        self.assertEqual(decision.outcome, "UNVERIFIABLE")

    def test_forbidden_shortcut_is_rejected(self) -> None:
        decision = evaluate_completion(self.goal, self.contract, {"evidence_types": ["VALIDATOR_RECEIPT"], "predicate_results": {"receipt_present": True}, "shortcut_flags": ["run_pass"]}, authority=self.validator, decided_at=NOW)
        self.assertEqual(decision.outcome, "REJECTED")

    def test_independent_evidence_can_satisfy(self) -> None:
        decision = evaluate_completion(self.goal, self.contract, {"evidence_types": ["VALIDATOR_RECEIPT"], "evidence_refs": ["receipt-1"], "predicate_results": {"receipt_present": True}}, authority=self.validator, decided_at=NOW)
        self.assertEqual(decision.outcome, "SATISFIED")
        self.assertEqual(len(decision.decision_sha256), 64)

    def test_registry_accepts_only_independent_satisfaction(self) -> None:
        registry = GoalRegistry([self.goal], [self.contract])
        decision = evaluate_completion(self.goal, self.contract, {"evidence_types": ["VALIDATOR_RECEIPT"], "predicate_results": {"receipt_present": True}}, authority=self.validator, decided_at=NOW)
        satisfied = registry.mark_satisfied(decision)
        self.assertEqual(satisfied.status, "SATISFIED")
        self.assertFalse(registry.events[-1]["completion_inferred"])

    def test_stale_decision_is_rejected(self) -> None:
        registry = GoalRegistry([self.goal], [self.contract])
        registry.transition(self.goal.goal_id, "PAUSED", provenance=self.validator, reason="pause", updated_at=NOW)
        decision = evaluate_completion(self.goal, self.contract, {"evidence_types": ["VALIDATOR_RECEIPT"], "predicate_results": {"receipt_present": True}}, authority=self.validator, decided_at=NOW)
        with self.assertRaises(Exception):
            registry.mark_satisfied(decision)


if __name__ == "__main__":
    unittest.main()
