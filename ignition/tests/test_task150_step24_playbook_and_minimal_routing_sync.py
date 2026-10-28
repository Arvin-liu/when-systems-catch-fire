from __future__ import annotations

import copy
import json
import unittest

from tools.validate_task150_step24_playbook_and_minimal_routing_sync import (
    ARTIFACT_PATH,
    EXPECTED_READS,
    LIFECYCLE_FIXTURE_PATH,
    OPERATING_METHOD_PATH,
    PLAYBOOKS_PATH,
    REGISTRY_PATH,
    validate,
)


class Task150Step24PlaybookAndMinimalRoutingSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.playbooks = json.loads(PLAYBOOKS_PATH.read_text(encoding="utf-8"))

    def test_step24_receipt_passes(self) -> None:
        self.assertEqual(validate(self.document), [])

    def test_capability_lookup_and_playbook_are_registry_derived(self) -> None:
        operation = next(row for row in self.registry["operations"] if row["operation_id"] == "visualization.render_derived_system_view")
        self.assertEqual(operation["current_status"], "CURRENT_BOUNDED")
        self.assertEqual(operation["ai_callability"], "PUBLIC_BOUNDED")
        self.assertEqual(operation["default_execution_mode"], "READ_ONLY_RUN")
        self.assertIsNone(operation["pack_binding"])
        self.assertIn("visualization.render_derived_system_view", [row["operation_id"] for row in self.playbooks["playbooks"]])
        self.assertEqual(len(self.playbooks["playbooks"]), 16)

    def test_typical_request_uses_read_only_minimal_plan(self) -> None:
        route = self.document["request_route"]
        reads = self.document["minimal_read_plan"]["reads"]
        self.assertEqual((route["run_mode"], route["operation_id"], route["decision"]), ("READ_ONLY_RUN", "visualization.render_derived_system_view", "PROCEED_BOUNDED"))
        self.assertEqual(reads, EXPECTED_READS)
        self.assertEqual(reads[:6], [
            "ignition/OPERATING-METHOD.md",
            "ignition/AI-START-HERE.md",
            "ignition/data/architecture/current-facts.json",
            "ignition/data/operations/current-snapshot-r1.json",
            "ignition/data/operations/ignition-operation-capability-registry-r1.json",
            "ignition/data/operations/ignition-run-output-contract-r1.json",
        ])
        self.assertFalse(route["side_effects_authorized_by_plan"])

    def test_provider_unavailable_and_analysis_only_boundaries_are_explicit(self) -> None:
        rules = self.document["routing_boundaries"]
        self.assertEqual(rules["provider_unavailable_result"], "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT")
        self.assertFalse(rules["automatic_provider_installation"])
        self.assertFalse(rules["automatic_provider_substitution"])
        self.assertFalse(rules["canonical_source_writeback"])
        self.assertFalse(self.document["request_route"]["architecture_analysis_only_auto_render"])
        method = OPERATING_METHOD_PATH.read_text(encoding="utf-8")
        self.assertIn("只要求分析架构而没有图请求时，不得因 provider 可用而自动渲染", method)

    def test_negative_mutations_fail_closed(self) -> None:
        mutated = copy.deepcopy(self.document)
        mutated["request_route"]["run_mode"] = "REPOSITORY_CHANGE_RUN"
        self.assertTrue(validate(mutated))

        mutated = copy.deepcopy(self.document)
        mutated["routing_boundaries"]["automatic_provider_installation"] = True
        self.assertTrue(validate(mutated))

        mutated = copy.deepcopy(self.document)
        mutated["minimal_read_plan"]["reads"] = mutated["minimal_read_plan"]["reads"][:-1]
        self.assertTrue(validate(mutated))

    def test_planning_fixture_has_new_route_case(self) -> None:
        fixture = json.loads(LIFECYCLE_FIXTURE_PATH.read_text(encoding="utf-8"))
        ids = {case["case_id"] for case in fixture["cases"]}
        self.assertEqual(len(fixture["cases"]), 10)
        self.assertIn("bounded_visualization_request_routes_read_only", ids)


if __name__ == "__main__":
    unittest.main()
