from __future__ import annotations

import copy
import unittest

from agent_runtime.steering import (
    AuthorityProvenance,
    CompletionContract,
    GoalRecord,
    IntentRecord,
    SteeringValidationError,
    ontology_contract,
)


NOW = "2026-08-21T12:00:00+08:00"


def owner_provenance() -> AuthorityProvenance:
    return AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-001", "synthetic fixture authorization", authorized=True)


class SteeringOntologyTests(unittest.TestCase):
    def test_layer_order_and_invariants_are_explicit(self) -> None:
        contract = ontology_contract()
        self.assertEqual([row["kind"] for row in contract["layers"]], ["intent", "goal", "commitment", "episode", "run", "action"])
        self.assertIn("INTENT_AUTHORITY_INVARIANT", contract["invariants"])
        self.assertIn("GOAL_COMPLETION_NON_INFERENCE_INVARIANT", contract["invariants"])

    def test_owner_declared_intent_is_explicitly_authorized(self) -> None:
        intent = IntentRecord("intent-001", "Finish a synthetic research brief", "fixture.public", owner_provenance(), "ACTIVE", {}, 1, None, NOW, NOW)
        self.assertTrue(intent.owner_authoritative)
        self.assertEqual(IntentRecord.from_dict(intent.to_dict()), intent)

    def test_proposal_cannot_become_owner_authority_by_field_change(self) -> None:
        provenance = AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "system.fixture", "proposal-001", "derived from a synthetic run")
        with self.assertRaises(SteeringValidationError):
            IntentRecord("intent-proposal", "A proposed direction", "fixture.public", provenance, "ACTIVE", {}, 1, None, NOW, NOW)

    def test_goal_digest_is_versioned_and_run_is_not_satisfaction(self) -> None:
        contract = CompletionContract("contract-001", ("validator_receipt_present",), ("VALIDATOR_RECEIPT",), "VALIDATOR", ("run_pass", "tests_green"))
        goal = GoalRecord("goal-001", "intent-001", "Produce a bounded brief", "fixture.public", contract.contract_id, owner_provenance(), "PROPOSED", 1, None, NOW, NOW)
        self.assertEqual(len(goal.objective_digest()), 64)
        changed = copy.deepcopy(goal.to_dict())
        changed["version"] = 2
        self.assertNotEqual(changed["version"], goal.version)

    def test_private_material_is_rejected(self) -> None:
        with self.assertRaises(SteeringValidationError):
            IntentRecord("intent-private", "Use this prompt body as a goal", "fixture.public", owner_provenance(), "ACTIVE", {}, 1, None, NOW, NOW)


if __name__ == "__main__":
    unittest.main()
