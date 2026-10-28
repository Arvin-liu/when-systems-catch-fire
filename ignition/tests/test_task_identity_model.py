from __future__ import annotations

import copy
import unittest

from tools import validate_task_identity_model as validator


class TaskIdentityModelTests(unittest.TestCase):
    def test_declarative_role_bindings_are_valid(self) -> None:
        self.assertEqual(validator.validate(), [])

    def test_architecture_task_is_not_a_current_formal_task_alias(self) -> None:
        model = validator.load_json(validator.MODEL_PATH)
        self.assertNotEqual(
            model["role_bindings"]["current_formal_task"]["role"],
            model["role_bindings"]["latest_architecture_changing_task"]["role"],
        )

    def test_witness_binding_must_stay_in_control_repository(self) -> None:
        model = copy.deepcopy(validator.load_json(validator.MODEL_PATH))
        model["role_bindings"]["publication_witness_task"]["source_path"] = "ignition/data/operations/publication-witness.json"
        self.assertTrue(any("control repository" in error for error in validator.validate(model)))

    def test_history_source_is_not_optional(self) -> None:
        model = copy.deepcopy(validator.load_json(validator.MODEL_PATH))
        model["historical_lineage_source"]["preserve_history"] = False
        self.assertTrue(validator.validate(model))


if __name__ == "__main__":
    unittest.main()
