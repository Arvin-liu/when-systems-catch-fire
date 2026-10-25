from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
import hashlib


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import plan_ignition_operation_run as planner  # noqa: E402
import toolbox_actions_step_timeline as timeline  # noqa: E402
import toolbox_actions_validation_attribution as attribution  # noqa: E402


class ActionsValidationAttributionRoutingTests(unittest.TestCase):
    def test_new_tool_stays_default_off_and_explicit_route_is_non_authorizing(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "maintenance.attribute_actions_validation_evidence"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = {
            "task_id": "offline-validation-plan-run-receipt-attribution",
            "current_ref": "refs/heads/main@483658e2ff57ad553c3fda762ed855a8bd93ebbe",
            "input_types": card["accepted_input_types"],
            "required_outputs": card["output_types"],
            "allowed_execution_modes": ["READ_ONLY_RUN"],
        }
        default = planner.plan_tool_route(task)
        opted_in = planner.plan_tool_route(task, include_experimental_tool_ids=[tool_id])
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-actions-validation-attribution-route-evidence-r0.json").read_text(encoding="utf-8")
        )
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(opted_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted_in["selected_tools"]], [tool_id])
        self.assertEqual(opted_in["selected_tools"][0]["kind"], "EXPERIMENTAL_OPTIONAL_TOOL")
        self.assertFalse(opted_in["execution_authorized"])
        self.assertFalse(opted_in["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(opted_in["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertEqual(opted_in["selected_tools"][0]["permissions"]["secrets"], False)
        self.assertEqual(opted_in["selected_tools"][0]["permissions"]["billing"], False)
        trials = {trial["scenario"]: trial for trial in evidence["route_trials"]}
        self.assertEqual(trials["default_opt_out"]["decision"], default["decision"])
        self.assertEqual(trials["default_opt_out"]["selected_tool_ids"], [])
        self.assertEqual(trials["explicit_candidate_allowlist"]["decision"], opted_in["decision"])
        self.assertEqual(trials["explicit_candidate_allowlist"]["selected_tool_ids"], [tool_id])
        self.assertFalse(trials["explicit_candidate_allowlist"]["execution_authorized"])

    def test_measured_real_task_routes_match_the_frozen_contract(self) -> None:
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-actions-validation-attribution-route-evidence-r0.json").read_text(encoding="utf-8")
        )["end_to_end_task_trials"]
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        cards = {row["tool_id"]: row for row in catalog["candidates"]}
        attr_id = "maintenance.attribute_actions_validation_evidence"
        timeline_id = "maintenance.summarize_actions_step_timeline"
        contract = evidence["task_contract"]
        full_task = {
            "task_id": contract["task_id"],
            "current_ref": contract["current_ref"],
            "input_types": contract["input_types"],
            "required_outputs": contract["required_outputs"],
            "allowed_execution_modes": contract["allowed_execution_modes"],
        }
        light_task = {
            "task_id": "pr264-run-40064357026-job-interval-summary-only",
            "current_ref": contract["current_ref"],
            "input_types": cards[timeline_id]["accepted_input_types"],
            "required_outputs": cards[timeline_id]["output_types"],
            "allowed_execution_modes": ["READ_ONLY_RUN"],
        }
        route_specs = {
            "default_full_task": (full_task, []),
            "time_only_explicit_route": (light_task, [timeline_id]),
            "full_task_timeline_only_allowlist": (full_task, [timeline_id]),
            "minimum_sufficient_full_task": (full_task, [attr_id]),
            "both_allowlisted_full_task": (full_task, [timeline_id, attr_id]),
        }
        saved_trials = {row["scenario"]: row for row in evidence["route_trials"]}
        for name, (task, allowlist) in route_specs.items():
            with self.subTest(route=name):
                planned = planner.plan_tool_route(task, include_experimental_tool_ids=allowlist)
                saved = saved_trials[name]
                self.assertEqual(saved["decision"], planned["decision"])
                self.assertEqual(saved["selected_tool_ids"], [row["tool_id"] for row in planned["selected_tools"]])
                self.assertFalse(saved["execution_authorized"])

        fixture_path = IGNITION_ROOT / "tests/fixtures/toolbox-actions-validation-attribution/input-run-40064357026-r0.json"
        raw = fixture_path.read_bytes()
        envelope = json.loads(raw)
        new_result = attribution.attribute_validation_evidence(raw)
        timeline_raw = attribution.canonical_json(envelope["actions_snapshot"]).encode("utf-8")
        timeline_result = timeline.summarize_snapshot(timeline_raw)
        canonical_output = attribution.canonical_json(new_result).encode("utf-8") + b"\n"
        canonical_timeline = attribution.canonical_json(timeline_result).encode("utf-8") + b"\n"
        measurements = evidence["measured_execution_comparison"]
        light = measurements["light_baseline"]
        sufficient = measurements["minimum_sufficient_route"]
        redundant = measurements["redundant_counterfactual"]
        self.assertEqual(light["execution"]["output_sha256_per_sample"], hashlib.sha256(canonical_timeline).hexdigest())
        self.assertEqual(sufficient["execution"]["output_sha256_per_sample"], hashlib.sha256(canonical_output).hexdigest())
        self.assertEqual(sufficient["observed_facts"]["plan_sha256"], new_result["plan_binding"]["plan_sha256"])
        self.assertEqual(sufficient["observed_facts"]["receipt_presence"], new_result["artifact_inventory"]["validation_receipt_presence"])
        self.assertEqual(timeline_result["summary"], new_result["timeline_summary"])
        self.assertTrue(redundant["timeline_summary_equal_to_attribution"])
        self.assertFalse(redundant["selected_by_adaptive_router"])
        self.assertEqual(redundant["execution"]["sample_count"], 3)


if __name__ == "__main__":
    unittest.main()
