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
        self.assertEqual(document["candidate_cards"]["candidate_count"], 10)
        self.assertEqual(document["card_count"], 30)
        current = [card for card in document["cards"] if card["card_kind"] == "CURRENT_OPERATION_REGISTRY_PROJECTION"]
        candidates = [card for card in document["cards"] if card["card_kind"] == "OPTIONAL_EXPERIMENTAL_TOOL"]
        self.assertEqual(len(current), 20)
        self.assertTrue(all(card["availability"] == "REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE" for card in current))
        self.assertTrue(all(card["router_selectable_by_default"] is False for card in candidates))
        crossref = next(card for card in candidates if card["tool_id"] == "research.verify_crossref_metadata")
        pubmed = next(card for card in candidates if card["tool_id"] == "research.resolve_pubmed_identifiers")
        self.assertEqual({card["tool_id"] for card in candidates if card["permissions"]["network"]}, {crossref["tool_id"], pubmed["tool_id"]})
        self.assertEqual(crossref["permissions"]["network_hosts"], ["api.crossref.org"])
        self.assertEqual(pubmed["permissions"]["network_hosts"], ["pmc.ncbi.nlm.nih.gov"])
        self.assertEqual(crossref["permission_mode"], "READ_ONLY_FIXED_HOST_NETWORK_QUERY")
        self.assertIn("--allow-public-network", crossref["entrypoint"])
        self.assertFalse(crossref["router_selectable_by_default"])
        self.assertEqual(crossref["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(crossref["estimated_cost"]["status"], "UNKNOWN")
        self.assertIn("article full text", " ".join(crossref["not_for"]))
        self.assertEqual(pubmed["permission_mode"], "READ_ONLY_FIXED_HOST_NETWORK_QUERY")
        self.assertIn("--allow-public-network", pubmed["entrypoint"])
        self.assertEqual(pubmed["evidence_level"], "REAL_TOOL_TEST")
        self.assertEqual(pubmed["estimated_cost"]["status"], "UNKNOWN")
        self.assertEqual(pubmed["dependencies"], [])
        self.assertIn("scientific truth", pubmed["claim_ceiling"])
        self.assertTrue(all(card["permissions"]["write_paths"] == [] for card in candidates))
        self.assertTrue(all(card["dependencies"] or card["tool_id"] == pubmed["tool_id"] for card in candidates))
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
        planner_card = next(card for card in candidates if card["tool_id"] == "ignition.adaptive_toolbox_route_planner")
        self.assertIn("allowed_network_hosts", " ".join(planner_card["accepted_input_types"]))
        self.assertIn("authorization", planner_card["claim_ceiling"])

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

    def test_network_candidate_requires_a_bounded_exact_host(self) -> None:
        schema = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-candidate-cards-r0.schema.json").read_text(encoding="utf-8"))
        catalog = json.loads((IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        crossref = next(row for row in catalog["candidates"] if row["tool_id"] == "research.verify_crossref_metadata")
        crossref["permissions"].pop("network_hosts")
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))
        crossref["permissions"]["network_hosts"] = ["*.crossref.org"]
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))
        crossref["permissions"]["network_hosts"] = ["127.0.0.1"]
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))
        crossref["permissions"]["network_hosts"] = [f"host-{index}.example.org" for index in range(17)]
        self.assertFalse(Draft202012Validator(schema).is_valid(catalog))


if __name__ == "__main__":
    unittest.main()
