from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, IntentRecord, MemoryProfileBoundary, MemoryProfileObservation


NOW = "2026-08-21T12:00:00+08:00"


class MemoryProfileBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "canonical", authorized=True)
        self.canonical = IntentRecord("canonical", "Canonical direction", "owner.synthetic", owner, status="ACTIVE", created_at=NOW, updated_at=NOW)
        self.boundary = MemoryProfileBoundary()

    def test_repeated_preference_is_proposal_only(self) -> None:
        observation = MemoryProfileObservation("memory-1", "OPERATIONAL_MEMORY", "Repeated preference", "Prefer bounded work", True, created_at=NOW)
        decision = self.boundary.evaluate(observation)
        self.assertEqual(decision.decision, "PROPOSAL_ONLY")
        self.assertIsNotNone(decision.proposal)
        self.assertFalse(decision.proposal.owner_authoritative)
        self.assertEqual(decision.proposal.status, "PROPOSED")
        self.assertEqual(decision.priority_effect, "NONE")

    def test_esi_is_advisory_and_cannot_change_priority(self) -> None:
        observation = MemoryProfileObservation("esi-1", "ESI_ADVISORY", "ESI suggestion", "Suggested direction", True, created_at=NOW)
        decision = self.boundary.evaluate(observation, canonical_intent=self.canonical)
        self.assertEqual(decision.decision, "ADVISORY_ONLY")
        self.assertEqual(decision.priority_effect, "NONE")

    def test_stale_conflicting_memory_loses_to_canonical_intent(self) -> None:
        observation = MemoryProfileObservation("memory-stale", "OPERATIONAL_MEMORY", "Stale direction", "Old direction", True, True, True, NOW)
        decision = self.boundary.evaluate(observation, canonical_intent=self.canonical)
        self.assertEqual(decision.decision, "CANONICAL_INTENT_WINS")
        self.assertEqual(decision.canonical_intent_id, "canonical")
        self.assertEqual(decision.priority_effect, "CANONICAL_INTENT_ONLY")

    def test_stale_memory_without_canonical_is_ignored(self) -> None:
        observation = MemoryProfileObservation("memory-old", "OPERATIONAL_MEMORY", "Old direction", "Old direction", True, True, created_at=NOW)
        self.assertEqual(self.boundary.evaluate(observation).decision, "STALE_IGNORED")

    def test_profile_projection_is_advisory(self) -> None:
        observation = MemoryProfileObservation("profile-1", "PROFILE_PROJECTION", "Profile narrows capability", created_at=NOW)
        self.assertEqual(self.boundary.evaluate(observation, canonical_intent=self.canonical).decision, "ADVISORY_ONLY")


if __name__ == "__main__":
    unittest.main()
