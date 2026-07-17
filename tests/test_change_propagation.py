import copy
import hashlib
import json
import unittest
from pathlib import Path

from tools.generate_interactive_system_map import build_projection, load_json
from tools.operations.compute_change_propagation import COMPONENTS, SURFACES, TOPOLOGY, compute


BASE_REQUEST = load_json(__import__("pathlib").Path("data/operations/propagation/121Q32-request.json"))
COMPONENT_DOC = load_json(COMPONENTS)
TOPOLOGY_DOC = load_json(TOPOLOGY)
SURFACE_DOC = load_json(SURFACES)
CURRENT_PROJECTION = build_projection()


class ChangePropagationTests(unittest.TestCase):
    def request(self, **updates):
        request = copy.deepcopy(BASE_REQUEST)
        request.update(updates)
        return request

    def test_a_method_version_change_reaches_front_doors_and_map(self):
        closure, _ = compute(copy.deepcopy(BASE_REQUEST))
        self.assertTrue(closure["closure_complete"])
        self.assertIn("iteration", closure["resolved_components"])
        self.assertIn("human.readme", closure["registry_derived_surfaces"])
        self.assertIn("agent.handoff", closure["registry_derived_surfaces"])
        self.assertEqual(closure["system_map_impact"]["decision"], "CHANGE")
        self.assertIn("iteration", closure["system_map_impact"]["changed_nodes"])

    def test_b_visible_new_component_requires_layout_or_a_no_change_reason(self):
        components = copy.deepcopy(COMPONENT_DOC)
        visible = copy.deepcopy(components["components"][0])
        visible.update({"component_id": "new_architecture", "label": "New architecture", "canonical_target": "ARCHITECTURE.md"})
        visible["path_patterns"] = ["docs/architecture/new-architecture.md"]
        visible["map_projection"] = {"visible": True, "group": "models"}
        components["components"].append(visible)
        with self.assertRaisesRegex(ValueError, "visibility mismatch"):
            build_projection(components, TOPOLOGY_DOC)

        visible["map_projection"] = {
            "visible": False,
            "represented_by": "mcf",
            "no_change_reason": "The existing MCF node is the canonical human-visible entrance.",
        }
        projection = build_projection(components, TOPOLOGY_DOC)
        self.assertNotIn("new_architecture", {node["id"] for node in projection["nodes"]})

    def test_c_lifecycle_change_is_a_map_delta_without_erasing_candidate_semantics(self):
        components = copy.deepcopy(COMPONENT_DOC)
        iteration = next(item for item in components["components"] if item["component_id"] == "iteration")
        iteration["lifecycle"]["status"] = "current"
        iteration["label"] = "点火迭代操作法 1.2.0 Current"
        closure, _ = compute(self.request(), components_doc=components, baseline_map=CURRENT_PROJECTION)
        self.assertIn("iteration", closure["system_map_impact"]["changed_nodes"])
        causal_relation = next(item for item in TOPOLOGY_DOC["relations"] if item["relation_domain"] == "substantive_causal_candidate")
        self.assertIn("candidate", causal_relation["claim_ceiling"])

    def test_d_pages_change_requires_deployment_surfaces_not_foundation_docs(self):
        request = self.request(
            changed_paths=[".github/workflows/pages.yml"],
            explicit_seed_components=[],
            state_transition_subjects=["Pages generation chain"],
            changed_dimensions=["deployment_rendering"],
            change_classifications=["INTERFACE_CHANGE"],
            system_map_decision={"item_id": "interactive_system_map", "decision": "NO_CHANGE_WITH_REASON", "reason": "The hosting chain changes without a component, target, status or visible relation change."},
        )
        closure, _ = compute(request, baseline_map=CURRENT_PROJECTION)
        self.assertTrue(closure["closure_complete"])
        self.assertIn("pages_pipeline", closure["resolved_components"])
        self.assertIn("external.pages_homepage", closure["registry_derived_surfaces"])
        self.assertNotIn("foundation", closure["resolved_components"])

    def test_e_historical_typo_allows_machine_checked_map_no_change(self):
        request = self.request(
            changed_paths=["reports/operations/old-report.md"],
            explicit_seed_components=[],
            state_transition_subjects=["historical report typo"],
            changed_dimensions=[],
            change_classifications=["HISTORICAL_ONLY"],
            system_map_decision={"item_id": "interactive_system_map", "decision": "NO_CHANGE_WITH_REASON", "reason": "The typo changes no capability, identity, lifecycle, target, relation or navigation."},
        )
        closure, _ = compute(request, baseline_map=CURRENT_PROJECTION)
        self.assertTrue(closure["closure_complete"])
        self.assertEqual(closure["resolved_components"], ["historical_reports"])
        self.assertEqual(closure["system_map_impact"]["decision"], "NO_CHANGE_WITH_REASON")

    def test_f_unmapped_path_and_cycle_are_explicit_blocking_residue(self):
        request = self.request(changed_paths=["unregistered/new-file.xyz"])
        closure, _ = compute(request, baseline_map=CURRENT_PROJECTION)
        self.assertFalse(closure["closure_complete"])
        self.assertIn("unmapped_path", {item["type"] for item in closure["residue"]})

        topology = copy.deepcopy(TOPOLOGY_DOC)
        cycle = copy.deepcopy(topology["relations"][-2])
        cycle.update({"relation_id": "test_pages_registry_cycle", "source": "pages_pipeline", "target": "project_component_registry", "propagation_mode": "automatic", "trigger_dimensions": ["operations_method"], "trigger_classifications": ["OPERATIONS_METHOD"]})
        topology["relations"].append(cycle)
        closure, _ = compute(self.request(), topology_doc=topology)
        self.assertFalse(closure["closure_complete"])
        self.assertIn("propagation_cycle", {item["type"] for item in closure["residue"]})

    def test_g_q29r_is_frozen(self):
        payload = Path("docs/publication/works/when-an-army-believes-its-own-back.md").read_bytes()
        self.assertEqual(hashlib.sha256(payload).hexdigest(), "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b")

    def test_fixpoint_and_hash_are_deterministic(self):
        first, _ = compute(copy.deepcopy(BASE_REQUEST))
        second, _ = compute(copy.deepcopy(BASE_REQUEST))
        self.assertEqual(first["closure_hash"], second["closure_hash"])
        self.assertEqual(first["typed_paths"], second["typed_paths"])
        self.assertTrue(first["fixpoint"]["reached"])

    def test_substantive_causal_candidate_cannot_auto_propagate(self):
        topology = copy.deepcopy(TOPOLOGY_DOC)
        relation = next(item for item in topology["relations"] if item["relation_domain"] == "substantive_causal_candidate")
        relation["propagation_mode"] = "automatic"
        with self.assertRaisesRegex(ValueError, "cannot auto-propagate"):
            compute(self.request(), topology_doc=topology)


if __name__ == "__main__":
    unittest.main()
