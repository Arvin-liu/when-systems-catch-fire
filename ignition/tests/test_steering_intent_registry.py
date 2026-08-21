from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_runtime.steering import AuthorityProvenance, IntentRecord, IntentRegistry, IntentRegistryError


NOW = "2026-08-21T12:00:00+08:00"


class IntentRegistryTests(unittest.TestCase):
    def test_fixture_has_one_owner_record_and_one_proposal(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data/operations/iterations/129/fixtures/intent-registry-r1.json"
        registry = IntentRegistry.from_dict(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(len(registry.owner_active()), 1)
        self.assertEqual(len(registry.records), 2)

    def test_system_proposal_cannot_be_activated(self) -> None:
        proposal = IntentRecord("intent-proposal", "A bounded proposal", "fixture.public", AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "system.fixture", "p-1", "synthetic"), "PROPOSED", {}, 1, None, NOW, NOW)
        registry = IntentRegistry([proposal])
        with self.assertRaises(IntentRegistryError):
            registry.transition("intent-proposal", "ACTIVE", provenance=proposal.provenance, reason="should fail", updated_at=NOW)

    def test_owner_supersession_preserves_lineage(self) -> None:
        owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "synthetic", authorized=True)
        replacement_provenance = AuthorityProvenance("OWNER_APPROVED_DERIVED", "owner.synthetic", "auth-2", "explicit replacement", authorized=True)
        old = IntentRecord("intent-old", "Old direction", "fixture.public", owner, "ACTIVE", {}, 1, None, NOW, NOW)
        new = IntentRecord("intent-new", "Replacement direction", "fixture.public", replacement_provenance, "ACTIVE", {}, 1, old.intent_id, NOW, NOW)
        registry = IntentRegistry([old])
        superseded, replacement = registry.supersede(old.intent_id, new, provenance=owner, reason="new explicit direction", updated_at=NOW)
        self.assertEqual(superseded.status, "SUPERSEDED")
        self.assertEqual(replacement.supersedes_intent_id, old.intent_id)
        self.assertTrue(registry.get(old.intent_id).version > 1)

    def test_registry_round_trip_keeps_authority_counts(self) -> None:
        owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "synthetic", authorized=True)
        registry = IntentRegistry([IntentRecord("intent-roundtrip", "Round trip", "fixture.public", owner, "ACTIVE", {}, 1, None, NOW, NOW)])
        restored = IntentRegistry.from_dict(registry.to_dict())
        self.assertEqual(restored.to_dict()["owner_authoritative_count"], 1)


if __name__ == "__main__":
    unittest.main()
