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
        self.assertEqual(document["candidate_cards"]["candidate_count"], 8)
        self.assertEqual(document["card_count"], 28)
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
        batch = next(card for card in candidates if card["tool_id"] == "foundation.batch_resolve_current_asset_references")
        self.assertEqual(batch["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(batch["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertIn("Python >=3.9 standard library", batch["runtime_dependencies"])
        self.assertIn("ambiguous", " ".join(batch["counterindicated_when"]).lower())
        self.assertTrue(any("legacy-mappings.jsonl" in path for path in batch["dependencies"]))
        pack_catalog = next(card for card in candidates if card["tool_id"] == "runtime.inspect_declared_pack_catalog")
        self.assertEqual(pack_catalog["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(pack_catalog["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertFalse(pack_catalog["permissions"]["network"])
        self.assertEqual(pack_catalog["permissions"]["write_paths"], [])
        self.assertIn("no Pack module is loaded", pack_catalog["claim_ceiling"])
        self.assertIn("ignition/packs/", pack_catalog["dependencies"])
        reader = next(card for card in candidates if card["tool_id"] == "foundation.read_current_asset_card")
        self.assertEqual(reader["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(reader["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertEqual(reader["permissions"]["write_paths"], [])
        self.assertIn("both identity registries source-hashed", reader["claim_ceiling"])
        function_os = next(card for card in candidates if card["tool_id"] == "function_os.run_bounded_symbolic_spec")
        self.assertEqual(function_os["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(function_os["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(function_os["permissions"]["write_paths"], [])
        self.assertFalse(function_os["permissions"]["network"])
        self.assertIn("security isolation", function_os["claim_ceiling"])
        self.assertIn("isolated security sandbox", " ".join(function_os["not_for"]))
        archify = next(card for card in candidates if card["tool_id"] == "visualization.build_archify_derived_ir")
        self.assertEqual(archify["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(archify["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(archify["permissions"]["write_paths"], [])
        self.assertFalse(archify["permissions"]["network"])
        self.assertIn("unresolved caller-supplied revision", archify["claim_ceiling"])
        evidence = next(card for card in candidates if card["tool_id"] == "research.validate_evidence_program_snapshot")
        self.assertEqual(evidence["execution_mode"], "READ_ONLY_RUN")
        self.assertEqual(evidence["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(evidence["permissions"]["write_paths"], [])
        self.assertFalse(evidence["permissions"]["network"])
        self.assertIn("no source authenticity", evidence["claim_ceiling"])

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
