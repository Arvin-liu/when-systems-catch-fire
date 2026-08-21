from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_runtime.steering import AuthorityProvenance, GoalRegistry, GoalRegistryError


NOW = "2026-08-21T12:00:00+08:00"


class GoalLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data/operations/iterations/129/fixtures/goal-lifecycle-r1.json"
        self.registry = GoalRegistry.from_dict(json.loads(path.read_text(encoding="utf-8")))
        self.owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "synthetic", authorized=True)
        self.system = AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "system.fixture", "sys-1", "synthetic")

    def test_allowed_transitions_are_versioned(self) -> None:
        goal = self.registry.transition("goal-synthetic-brief", "ACTIVE", provenance=self.owner, reason="activate", updated_at=NOW)
        self.assertEqual(goal.status, "ACTIVE")
        self.assertEqual(goal.version, 2)
        goal = self.registry.transition(goal.goal_id, "PAUSED", provenance=self.system, reason="operator pause required", updated_at=NOW)
        self.assertEqual(goal.status, "PAUSED")

    def test_blocked_reason_is_recorded(self) -> None:
        self.registry.transition("goal-synthetic-brief", "BLOCKED", provenance=self.system, reason="prerequisite missing", updated_at=NOW)
        self.assertEqual(self.registry.events[-1]["reason"], "prerequisite missing")
        self.assertEqual(self.registry.events[-1]["completion_inferred"], False)

    def test_run_or_receipt_cannot_satisfy_goal(self) -> None:
        with self.assertRaises(GoalRegistryError):
            self.registry.transition("goal-synthetic-brief", "SATISFIED", provenance=self.owner, reason="run PASS", evidence_refs=("run-receipt",), updated_at=NOW)

    def test_terminal_goal_reopen_requires_new_lineage(self) -> None:
        self.registry.transition("goal-synthetic-brief", "ABANDONED", provenance=self.system, reason="bounded abandonment", updated_at=NOW)
        with self.assertRaises(GoalRegistryError):
            self.registry.reopen("goal-synthetic-brief", self.registry.get("goal-synthetic-brief"), provenance=self.owner, reason="invalid same record")

    def test_unknown_contract_is_rejected(self) -> None:
        self.assertEqual(self.registry.contract("contract-synthetic-brief").completion_authority, "VALIDATOR")
        with self.assertRaises(GoalRegistryError):
            self.registry.contract("missing-contract")


if __name__ == "__main__":
    unittest.main()
