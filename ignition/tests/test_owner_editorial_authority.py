from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools import validate_owner_editorial_authority as authority


ROOT = Path(__file__).resolve().parents[1]


class OwnerEditorialAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads((ROOT / "data/governance/owner-editorial-authority-r1.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((ROOT / "schemas/governance/owner-editorial-authority-r1.schema.json").read_text(encoding="utf-8"))
        cls.fixtures = json.loads((ROOT / "data/governance/owner-editorial-authority-negative-fixtures-r1.json").read_text(encoding="utf-8"))

    def test_contract_and_negative_fixtures_pass(self) -> None:
        self.assertEqual(authority.validate_contract(self.contract, self.schema), [])
        for fixture in self.fixtures:
            self.assertIn(fixture["expected_error_code"], authority.validate_item(fixture, self.contract), fixture["fixture_id"])

    def test_task143_smoke_inventory_is_not_selected_or_accepted(self) -> None:
        inventory = json.loads((ROOT / "data/operations/iterations/144/task143-smoke-output-inventory-r1.json").read_text(encoding="utf-8"))
        self.assertEqual(authority.validate_smoke_inventory(inventory, self.contract), [])

    def test_draft_generation_does_not_accept_a_work(self) -> None:
        item = copy.deepcopy(self.fixtures[2])
        self.assertIn("DRAFT_GENERATED_NOT_PUBLICATION_ACCEPTED", authority.validate_item(item, self.contract))

    def test_owner_selection_requires_explicit_authority(self) -> None:
        item = {
            "kind": "article",
            "source_origin": "OWNER_BRIEF",
            "owner_selection": "OWNER_SELECTED",
            "draft_status": "NOT_GENERATED",
            "production_state": "OWNER_SELECTED",
            "publication_acceptance": "PUBLICATION_ACCEPTANCE_NOT_GRANTED",
            "authority_source": "NONE",
        }
        self.assertIn("OWNER_SELECTED_REQUIRES_OWNER_AUTHORITY", authority.validate_item(item, self.contract))

    def test_publication_acceptance_requires_owner_authority(self) -> None:
        item = {
            "kind": "article",
            "source_origin": "OWNER_BRIEF",
            "owner_selection": "NOT_REVIEWED",
            "draft_status": "DRAFT_GENERATED",
            "production_state": "CANDIDATE",
            "publication_acceptance": "PUBLICATION_ACCEPTED",
            "authority_source": "NONE",
        }
        self.assertIn("PUBLICATION_ACCEPTED_REQUIRES_OWNER_AUTHORITY", authority.validate_item(item, self.contract))

    def test_state_machine_has_only_minimal_editorial_transitions(self) -> None:
        transitions = {(row["from"], row["to"]) for row in self.contract["state_machine"]["allowed_transitions"]}
        self.assertEqual(transitions, {
            ("CANDIDATE", "OWNER_SELECTED"),
            ("OWNER_SELECTED", "DRAFTING"),
            ("DRAFTING", "OWNER_REVIEW"),
            ("OWNER_REVIEW", "ACCEPTED"),
            ("OWNER_REVIEW", "REVISE"),
            ("OWNER_REVIEW", "PARKED"),
            ("OWNER_REVIEW", "REJECTED"),
        })


if __name__ == "__main__":
    unittest.main()
