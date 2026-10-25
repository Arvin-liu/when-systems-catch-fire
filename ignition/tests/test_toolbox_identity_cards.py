from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/operations/build_toolbox_identity_cards.py"
SPEC = importlib.util.spec_from_file_location("toolbox_identity_cards", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class ToolboxIdentityCardTests(unittest.TestCase):
    def test_projection_keeps_current_registry_and_candidate_tools_separate(self) -> None:
        document = TOOL.build_cards()
        self.assertEqual(document["current_registry"]["operation_count"], 20)
        self.assertEqual(document["candidate_cards"]["candidate_count"], 2)
        self.assertEqual(document["card_count"], 22)
        current = [card for card in document["cards"] if card["card_kind"] == "CURRENT_OPERATION_REGISTRY_PROJECTION"]
        candidates = [card for card in document["cards"] if card["card_kind"] == "OPTIONAL_EXPERIMENTAL_TOOL"]
        self.assertEqual(len(current), 20)
        self.assertTrue(all(card["availability"] == "REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE" for card in current))
        self.assertTrue(all(card["router_selectable_by_default"] is False for card in candidates))
        self.assertTrue(all(card["permissions"]["network"] is False for card in candidates))
        self.assertTrue(all(card["permissions"]["write_paths"] == [] for card in candidates))
        self.assertTrue(all(card["dependencies"] for card in candidates))
        self.assertTrue(all(card["source_refs_with_hashes"] for card in candidates))
        self.assertTrue(all(card["explicit_owner_authorization_required"] is False for card in candidates))

    def test_candidate_catalog_schema_and_source_pin_are_valid(self) -> None:
        validator_path = IGNITION_ROOT / "tools/operations/validate_toolbox_candidates.py"
        validator_spec = importlib.util.spec_from_file_location("validate_toolbox_candidates", validator_path)
        validator = importlib.util.module_from_spec(validator_spec)
        assert validator_spec.loader is not None
        validator_spec.loader.exec_module(validator)
        self.assertEqual(validator.validate(), [])

    def test_candidate_schema_rejects_dependency_path_traversal(self) -> None:
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-candidate-cards-r0.schema.json").read_text(encoding="utf-8"))
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        catalog["candidates"][0]["dependencies"].append("ignition/../../outside.py")
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))


if __name__ == "__main__":
    unittest.main()
