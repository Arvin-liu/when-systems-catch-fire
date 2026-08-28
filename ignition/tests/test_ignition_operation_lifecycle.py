from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


class IgnitionOperationLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = json.loads(planner.FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_all_nine_lifecycle_fixtures_pass(self) -> None:
        self.assertEqual(len(self.fixtures["cases"]), 9)
        self.assertEqual(planner.validate_fixtures(self.fixtures), [])

    def test_lifecycle_has_exact_fourteen_stages(self) -> None:
        self.assertEqual(len(planner.LIFECYCLE_STAGES), 14)
        self.assertEqual(planner.LIFECYCLE_STAGES[0], "ACCEPT_REQUEST")
        self.assertEqual(planner.LIFECYCLE_STAGES[-1], "STOP / HANDOFF")

    def test_unknown_operation_fails_closed(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "unknown_operation_stops")
        result = planner.plan_run(case["request"], case["operation_id"], case["current_ref"])
        self.assertEqual(result["stop_reason"], "UNSUPPORTED_OPERATION")
        self.assertFalse(result["side_effects_authorized_by_plan"])

    def test_owner_deferred_capability_stops(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "owner_deferred_stops")
        result = planner.plan_run(case["request"], case["operation_id"], case["current_ref"])
        self.assertEqual(result["stop_reason"], "CAPABILITY_OWNER_DEFERRED")
        self.assertFalse(result["side_effects_authorized_by_plan"])

    def test_minimal_read_plan_is_deduplicated_and_source_bound(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "bounded_operation_proceeds_bounded")
        result = planner.plan_run(case["request"], case["operation_id"], case["current_ref"])
        self.assertEqual(result["minimal_read_plan"][: len(planner.CORE_CURRENT_READS)], list(planner.CORE_CURRENT_READS))
        self.assertEqual(len(result["minimal_read_plan"]), len(set(result["minimal_read_plan"])))
        self.assertNotIn("ignition/RESULTS/CHRONOLOGY.md", result["minimal_read_plan"])

    def test_malformed_operation_or_current_ref_fails_closed(self) -> None:
        request = {"request_envelope": {"user_request": "请核查断言。"}, "input_objects": []}
        with self.assertRaises(planner.RunPlanningError):
            planner.plan_run(request, "", "refs/heads/main@example")
        with self.assertRaises(planner.RunPlanningError):
            planner.plan_run(request, "knowledge.validate_claim", "")

    def test_only_callable_current_operations_load_playbook_index(self) -> None:
        request = {"request_envelope": {"user_request": "请核查断言。"}, "input_objects": []}
        current = planner.plan_run(request, "knowledge.validate_claim", "refs/heads/main@example-current")
        historical = planner.plan_run(request, "repository.apply_iteration_method_1_3", "refs/heads/main@example-current")
        self.assertEqual(current["playbook_source"], planner.PLAYBOOKS_PATH)
        self.assertIn(planner.PLAYBOOKS_PATH, current["minimal_read_plan"])
        self.assertIsNone(historical["playbook_source"])
        self.assertNotIn(planner.PLAYBOOKS_PATH, historical["minimal_read_plan"])

    def test_every_run_plan_loads_the_unified_output_contract(self) -> None:
        request = {"request_envelope": {"user_request": "请说明当前状态。"}, "input_objects": []}
        current = planner.plan_run(request, "ignition.recover_current_state", "refs/heads/main@example-current")
        status_only = planner.plan_run(request, "executor.reference_conformance", "refs/heads/main@example-current")
        unknown = planner.plan_run(request, "ignition.unknown", "refs/heads/main@example-current")
        for result in (current, status_only, unknown):
            self.assertEqual(result["output_contract_source"], planner.OUTPUT_CONTRACT_PATH)
            self.assertIn(planner.OUTPUT_CONTRACT_PATH, result["minimal_read_plan"])


if __name__ == "__main__":
    unittest.main()
