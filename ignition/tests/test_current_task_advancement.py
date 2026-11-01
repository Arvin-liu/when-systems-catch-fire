from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

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

    def test_in_progress_predecessor_is_not_rewritten_as_terminal(self) -> None:
        source = copy.deepcopy(self.source)
        source["current_task"] = {
            "task_id": "IGNITION-20261024-020",
            "scope": "Task20 bounded R3 work",
            "execution_status": "IN_PROGRESS",
            "terminal": False,
            "identity_impact": "NONE",
        }
        contract = copy.deepcopy(self.contract)
        task_id = "IGNITION-20261101-021"
        contract["task_id"] = task_id
        contract["identity_expectations"].update({
            "current_formal_task": task_id,
            "previous_canonical_current_task": "IGNITION-20261024-020",
            "previous_formal_task": "IGNITION-20261024-020",
            "release_candidate_task": task_id,
            "publication_witness_task": task_id,
        })
        updated, changed = advancement.advance_document(source, contract)
        reason = updated["task_identity"]["advancement"]["transition_reason"]
        self.assertTrue(changed)
        self.assertEqual(updated["task_identity"]["previous_canonical_current_task"], "IGNITION-20261024-020")
        self.assertIn("execution_status=IN_PROGRESS", reason)
        self.assertIn("terminal=false", reason)
        self.assertNotIn("from terminal", reason)
        self.assertEqual(
            updated["task_identity"]["advancement"]["execution_contract_path"],
            "ignition/data/operations/iterations/021/execution-contract-r1.json",
        )

    def test_contract_selection_follows_registered_task20_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = "ignition/data/operations/iterations/020/execution-contract-r1.json"
            path = root / source
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "task_id": "IGNITION-20261024-020",
                "identity_expectations": {"release_candidate_task": "IGNITION-20261024-020"},
            }), encoding="utf-8")
            model = {"role_bindings": {"release_candidate_task": {"source_path": source}}}
            self.assertEqual(advancement.resolve_contract_path(model, root), path.resolve())

    def test_contract_selection_rejects_unbound_or_escaping_path(self) -> None:
        with self.assertRaises(advancement.AdvancementError):
            advancement.resolve_contract_path({"role_bindings": {"release_candidate_task": {
                "source_path": "ignition/data/operations/iterations/149/execution-contract-r1.json"
            }}}, Path("/tmp"))
        with self.assertRaises(advancement.AdvancementError):
            advancement.resolve_contract_path({"role_bindings": {"release_candidate_task": {
                "source_path": "../../outside.json"
            }}}, Path("/tmp"))


if __name__ == "__main__":
    unittest.main()
