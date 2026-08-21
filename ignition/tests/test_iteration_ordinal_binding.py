from __future__ import annotations

import copy
import unittest

from tools import validate_iteration_ordinal_binding as gate


class IterationOrdinalBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = gate.load_json(gate.CONTRACT_PATH)
        self.lineage = gate.load_json(gate.LINEAGE_PATH)
        self.lifecycle = gate.load_json(gate.LIFECYCLE_PATH)
        self.snapshot = gate.load_json(gate.SNAPSHOT_PATH)
        self.facts = gate.load_json(gate.FACTS_PATH)

    def test_current_chain_passes_with_terminal_evidence_pending(self) -> None:
        errors, records = gate.validate_documents(
            contract=self.contract,
            lineage=self.lineage,
            lifecycle=self.lifecycle,
            snapshot=self.snapshot,
            facts=self.facts,
        )
        self.assertEqual(errors, [])
        self.assertEqual(gate.pending_roles(records), ["formal_result_task", "publication_witness_task"])

    def test_formal_and_architecture_ordinals_are_independent(self) -> None:
        records = [
            {"role_id": "execution_contract_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "current_formal_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "architecture_task", "task_id": "IGNITION-20260821-129", "declared_ordinal": 129},
            {"role_id": "lifecycle_task", "task_id": "IGNITION-20260822-133", "declared_ordinal": 133},
            {"role_id": "snapshot_task", "task_id": "IGNITION-20260822-133", "declared_ordinal": 133},
            {"role_id": "release_candidate_task", "task_id": "IGNITION-20260822-133"},
        ]
        self.assertEqual(
            gate.validate_binding_chain(
                records,
                expected_task_id="IGNITION-20260822-133",
                expected_architecture_task="IGNITION-20260821-129",
            ),
            [],
        )

    def test_stale_alias_fails_closed(self) -> None:
        lifecycle = copy.deepcopy(self.lifecycle)
        lifecycle["current_iteration_boundary"] = 130
        errors, _ = gate.validate_documents(
            contract=self.contract,
            lineage=self.lineage,
            lifecycle=lifecycle,
            snapshot=self.snapshot,
            facts=self.facts,
        )
        self.assertTrue(any("COMPATIBILITY_ALIAS_MISMATCH:lifecycle_task" in error for error in errors))

    def test_architecture_ordinal_cannot_be_formal_ordinal(self) -> None:
        records = [
            {"role_id": "current_formal_task", "task_id": "IGNITION-20260822-133", "architecture_task_id": "IGNITION-20260821-129", "architecture_ordinal": 133},
            {"role_id": "architecture_task", "task_id": "IGNITION-20260821-129", "declared_ordinal": 133},
        ]
        errors = gate.validate_binding_chain(records)
        self.assertTrue(any("ARCHITECTURE_ORDINAL_MISMATCH" in error for error in errors))

    def test_terminal_records_require_explicit_ordinals(self) -> None:
        records = [
            {"role_id": "current_formal_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "architecture_task", "task_id": "IGNITION-20260821-129", "declared_ordinal": 129},
            {"role_id": "lifecycle_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "snapshot_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "execution_contract_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "release_candidate_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "formal_result_task", "task_id": "IGNITION-20260822-133"},
            {"role_id": "publication_witness_task", "task_id": "IGNITION-20260822-133", "declared_ordinal": 133},
        ]
        errors = gate.validate_binding_chain(records, require_terminal_evidence=True)
        self.assertTrue(any("ORDINAL_ASSERTION_MISSING:formal_result_task" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
