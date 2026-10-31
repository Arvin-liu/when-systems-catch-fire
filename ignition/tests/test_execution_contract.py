from __future__ import annotations

import copy
import unittest

from tools import validate_execution_contract as validator


class ExecutionContractTests(unittest.TestCase):
    def test_current_task_contract_is_valid(self) -> None:
        self.assertEqual(validator.validate(), [])

    def test_current_task_allows_ready_pr_but_keeps_owner_authorization_gate(self) -> None:
        contract = validator.load_json(validator.CONTRACT_PATH)
        self.assertFalse(contract["draft_pr_only"])
        self.assertTrue(contract["owner_authorization_required_for_ready_merge_or_close"])
        self.assertEqual(validator.validate(contract), [])

    def test_wrong_baseline_is_rejected(self) -> None:
        contract = copy.deepcopy(validator.load_json(validator.CONTRACT_PATH))
        contract["formal_baseline"]["sha"] = "1" * 40
        self.assertTrue(any("baseline" in error for error in validator.validate(contract)))

    def test_owner_middle_relay_cannot_be_enabled(self) -> None:
        contract = copy.deepcopy(validator.load_json(validator.CONTRACT_PATH))
        contract["no_owner_intermediate"] = False
        self.assertTrue(validator.validate(contract))

    def test_current_task_keeps_architecture_identity_distinct(self) -> None:
        contract = validator.load_json(validator.CONTRACT_PATH)
        self.assertNotEqual(
            contract["identity_expectations"]["current_formal_task"],
            contract["identity_expectations"]["latest_architecture_changing_task"],
        )
        self.assertEqual(contract["identity_impact"], "NONE")


if __name__ == "__main__":
    unittest.main()
