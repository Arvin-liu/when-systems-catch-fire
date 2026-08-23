from __future__ import annotations

import copy
import unittest

from tools import advance_current_task as advancement
from tools import validate_execution_contract_135 as validate_execution_contract


class CurrentTaskAdvancementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = advancement.load_json(advancement.STATUS_PATH)
        self.source["current_task"] = {
            "task_id": "IGNITION-20260822-134",
            "scope": "Residual Debt & Projection Hygiene R1",
            "execution_status": "COMPLETED_WITH_CLASSIFIED_RESIDUALS",
            "terminal": True,
            "identity_impact": "PRESENTATION_ONLY",
        }
        self.source.pop("task_identity", None)
        self.contract = validate_execution_contract.load_json(validate_execution_contract.CONTRACT_PATH)

    def test_advancement_moves_canonical_source_to_task135(self) -> None:
        updated, changed = advancement.advance_document(self.source, self.contract)
        self.assertTrue(changed)
        self.assertEqual(updated["current_task"]["task_id"], "IGNITION-20260822-135")
        self.assertEqual(updated["task_identity"]["latest_architecture_changing_task"], "IGNITION-20260821-129")
        self.assertEqual(updated["task_identity"]["previous_canonical_current_task"], "IGNITION-20260822-134")
        self.assertEqual(updated["task_identity"]["previous_formal_task"], "IGNITION-20260822-134")
        self.assertEqual(advancement.validate_state(updated), [])

    def test_same_advancement_is_idempotent(self) -> None:
        updated, _ = advancement.advance_document(self.source, self.contract)
        repeated, changed = advancement.advance_document(updated, self.contract)
        self.assertFalse(changed)
        self.assertEqual(repeated, updated)

    def test_backward_transition_is_rejected(self) -> None:
        updated, _ = advancement.advance_document(self.source, self.contract)
        backward = copy.deepcopy(self.contract)
        backward["identity_expectations"]["current_formal_task"] = "IGNITION-20260821-131"
        backward["task_id"] = "IGNITION-20260821-131"
        with self.assertRaises(advancement.AdvancementError):
            advancement.advance_document(updated, backward)

    def test_unknown_task_requires_valid_explicit_contract(self) -> None:
        unknown = copy.deepcopy(self.contract)
        unknown["identity_expectations"]["current_formal_task"] = "IGNITION-20260822-999"
        with self.assertRaises(advancement.AdvancementError):
            advancement.advance_document(self.source, unknown)

    def test_historical_lineage_is_retained(self) -> None:
        updated, _ = advancement.advance_document(self.source, self.contract)
        edges = {(row["predecessor_task_id"], row["successor_task_id"]) for row in updated["task_identity"]["historical_lineage"]}
        self.assertIn(("IGNITION-20260821-129", "IGNITION-20260821-130"), edges)
        self.assertIn(("IGNITION-20260821-130", "IGNITION-20260821-131"), edges)
        self.assertIn(("IGNITION-20260822-132", "IGNITION-20260822-133"), edges)
        self.assertIn(("IGNITION-20260822-133", "IGNITION-20260822-134"), edges)


if __name__ == "__main__":
    unittest.main()
