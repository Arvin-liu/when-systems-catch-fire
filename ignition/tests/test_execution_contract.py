from __future__ import annotations

import copy
import unittest

from tools import validate_execution_contract as validator


class ExecutionContractTests(unittest.TestCase):
    def test_task136_contract_is_fixed(self) -> None:
        self.assertEqual(validator.validate(), [])

    def test_wrong_baseline_is_rejected(self) -> None:
        contract = copy.deepcopy(validator.load_json(validator.CONTRACT_PATH))
        contract["formal_baseline"]["sha"] = "1" * 40
        self.assertTrue(any("baseline" in error for error in validator.validate(contract)))

    def test_owner_middle_relay_cannot_be_enabled(self) -> None:
        contract = copy.deepcopy(validator.load_json(validator.CONTRACT_PATH))
        contract["no_owner_intermediate"] = False
        self.assertTrue(validator.validate(contract))

    def test_architecture_changed_task_is_current_formal_identity(self) -> None:
        contract = validator.load_json(validator.CONTRACT_PATH)
        self.assertEqual(
            contract["identity_expectations"]["current_formal_task"],
            contract["identity_expectations"]["latest_architecture_changing_task"],
        )
        self.assertEqual(contract["identity_impact"], "ARCHITECTURE_CHANGED")


if __name__ == "__main__":
    unittest.main()
