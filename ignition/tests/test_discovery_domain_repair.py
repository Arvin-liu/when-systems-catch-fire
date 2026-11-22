from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.operations.task_intent_router import resolve_task_intent  # noqa: E402
from tools.operations.validate_discovery_domain_assets import (  # noqa: E402
    AssetValidationError,
    validate_all,
    validate_component_matrix,
    validate_execution_boundary_map,
)


DATA = ROOT / "data" / "operations"


def load_json(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class DiscoveryDomainRepairTests(unittest.TestCase):
    def test_intent_router_filters_typed_inputs_and_fails_closed(self) -> None:
        registry = load_json("ignition-operation-capability-registry-r1.json")
        index = load_json("task-intent-index-r1.json")

        note = resolve_task_intent("分析笔记来源案例或论证", "note", intent_index=index, operation_registry=registry)
        self.assertEqual(note["status"], "CANDIDATE")
        self.assertEqual(note["candidates"][0]["operation_id"], "knowledge.collide_object")

        obligation = resolve_task_intent("登记证据请求", "evidence_request", intent_index=index, operation_registry=registry)
        self.assertEqual(obligation["status"], "CANDIDATE")
        self.assertEqual(obligation["candidates"][0]["operation_id"], "research.coordinate_obligations")

        ambiguous = resolve_task_intent("检查 function asset", "function_asset", intent_index=index, operation_registry=registry)
        self.assertEqual(ambiguous["status"], "UNRESOLVED")
        self.assertEqual(
            {row["operation_id"] for row in ambiguous["candidates"]},
            {"knowledge.read_foundation", "knowledge.validate_claim"},
        )

        new_research_question = resolve_task_intent("提出一个新研究问题", "research_obligation", intent_index=index, operation_registry=registry)
        self.assertEqual(new_research_question["status"], "UNSUPPORTED")
        self.assertEqual(resolve_task_intent("anything", "invented_type", intent_index=index, operation_registry=registry)["status"], "UNSUPPORTED")
        self.assertEqual(resolve_task_intent("分析笔记来源案例或论证", None, intent_index=index, operation_registry=registry)["status"], "UNSUPPORTED")

    def test_generated_assets_cover_the_declared_scope(self) -> None:
        report = validate_all()
        self.assertEqual(report["task_intent_entries"], 16)
        self.assertEqual(report["components"], 106)
        self.assertEqual(report["previously_unmapped"], 46)
        self.assertEqual(report["operations"], 20)
        self.assertEqual(report["packs"], 4)
        self.assertEqual(report["optional_experimental_tools"], 77)
        self.assertEqual(report["classification_counts"], {
            "single_domain_primary": {"G": 12, "O": 5, "R": 1},
            "shared_cross_domain": 2,
            "unresolved": 86,
        })
        matrix = load_json("component-domain-responsibilities-r1.json")
        self.assertEqual(
            {status: sum(item["disposition"] == status for item in matrix["previously_unmapped_review"])
             for status in ("SINGLE_DOMAIN_PRIMARY", "SHARED_CROSS_DOMAIN", "UNRESOLVED")},
            {"SINGLE_DOMAIN_PRIMARY": 10, "SHARED_CROSS_DOMAIN": 0, "UNRESOLVED": 36},
        )

    def test_validation_map_cannot_be_promoted_to_responsibility(self) -> None:
        matrix = load_json("component-domain-responsibilities-r1.json")
        components = load_json("project-components.json")
        validation_map = load_json("component-validation-map-r1.json")
        registry = load_json("ignition-operation-capability-registry-r1.json")
        tampered = copy.deepcopy(matrix)
        row = next(item for item in tampered["components"] if item.get("validation_map_projection"))
        row["validation_map_projection"]["declared_validation_domain_associations"] = ["G"]
        with self.assertRaises(AssetValidationError):
            validate_component_matrix(tampered, components, validation_map, registry)

    def test_discovery_map_rejects_execution_promotion(self) -> None:
        boundary = load_json("capability-execution-boundary-map-r1.json")
        registry = load_json("ignition-operation-capability-registry-r1.json")
        components = load_json("project-components.json")
        candidates = load_json("toolbox-candidate-cards-r0.json")
        tampered = copy.deepcopy(boundary)
        tampered["operations"][0]["execution_state"] = "EXECUTED"
        with self.assertRaises(AssetValidationError):
            validate_execution_boundary_map(tampered, registry, components, candidates)

        tampered = copy.deepcopy(boundary)
        tampered["packs"][0]["execution_claim"] = "EXECUTED"
        with self.assertRaises(AssetValidationError):
            validate_execution_boundary_map(tampered, registry, components, candidates)

    def test_generic_executor_is_not_bound_to_registered_domain_operations(self) -> None:
        boundary = load_json("capability-execution-boundary-map-r1.json")
        self.assertEqual(
            boundary["generic_runtime_boundary"]["operation_binding"],
            "NO_EXACT_OPERATION_ID_TO_RUNTIME_ENTRYPOINT_BINDING_ESTABLISHED",
        )
        self.assertTrue(all(row["implementation"]["state"] == "UNRESOLVED" for row in boundary["operations"]))
        self.assertTrue(all(row["execution_claim"] == "NOT_PERFORMED_BY_PACK_AWARE_ROUTER" for row in boundary["packs"]))


if __name__ == "__main__":
    unittest.main()
