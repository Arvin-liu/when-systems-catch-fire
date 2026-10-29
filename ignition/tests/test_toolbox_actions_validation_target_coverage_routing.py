from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


class ActionsValidationTargetCoverageRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        operation_data = IGNITION_ROOT / "data/operations"
        self.cards = json.loads((operation_data / "toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))["candidates"]
        self.by_id = {row["tool_id"]: row for row in self.cards}
        self.profile = json.loads(
            (operation_data / "toolbox-actions-validation-target-coverage-route-profile-r0.json").read_text(encoding="utf-8")
        )
        self.evidence = json.loads(
            (operation_data / "toolbox-actions-validation-target-coverage-route-evidence-r0.json").read_text(encoding="utf-8")
        )

    def test_default_off_explicit_route_and_overinclusive_minimum_sufficiency(self) -> None:
        candidate_id = self.profile["required_candidate_tool_id"]
        task = {
            "task_id": self.profile["task_id"],
            "current_ref": self.profile["current_ref"],
            "input_types": self.profile["input_types"],
            "required_outputs": self.profile["required_outputs"],
            "allowed_execution_modes": self.profile["allowed_execution_modes"],
        }
        scenarios = {
            "default_opt_out": ([], "INCOMPLETE", []),
            "explicit_candidate_allowlist": ([candidate_id], "COMPLETE", [candidate_id]),
            "overinclusive_allowlist": ([candidate_id,
                "maintenance.attribute_actions_validation_evidence",
                "maintenance.compare_actions_repeated_step_sequences"], "COMPLETE", [candidate_id]),
        }
        saved = {row["scenario"]: row for row in self.evidence["route_trials"]}
        for name, (allowlist, expected_decision, expected_tools) in scenarios.items():
            with self.subTest(scenario=name):
                planned = planner.plan_tool_route(task, include_experimental_tool_ids=allowlist)
                selected = [row["tool_id"] for row in planned["selected_tools"]]
                trial = saved[name]
                self.assertEqual(planned["decision"], expected_decision)
                self.assertEqual(selected, expected_tools)
                self.assertEqual(trial["decision"], planned["decision"])
                self.assertEqual(trial["selected_tool_ids"], selected)
                self.assertFalse(planned["execution_authorized"])
                self.assertFalse(trial["execution_authorized"])

        opt_in = planner.plan_tool_route(task, include_experimental_tool_ids=[candidate_id])
        selected = opt_in["selected_tools"][0]
        self.assertEqual(selected["kind"], "EXPERIMENTAL_OPTIONAL_TOOL")
        self.assertFalse(selected["permissions"]["network"])
        self.assertEqual(selected["permissions"]["write_paths"], [])
        self.assertFalse(selected["permissions"]["secrets"])
        self.assertFalse(selected["permissions"]["billing"])
        self.assertFalse(selected["permissions"]["external_actions"])

    def test_existing_tools_keep_their_single_run_and_step_history_scopes(self) -> None:
        candidate_id = self.profile["required_candidate_tool_id"]
        specs = [
            ("single_run_attribution_scope", "maintenance.attribute_actions_validation_evidence", [
                "maintenance.attribute_actions_validation_evidence", candidate_id,
            ]),
            ("repeated_step_history_scope", "maintenance.compare_actions_repeated_step_sequences", [
                "maintenance.compare_actions_repeated_step_sequences", candidate_id,
            ]),
        ]
        saved = {row["scenario"]: row for row in self.evidence["route_trials"]}
        for scenario, task_tool_id, allowlist in specs:
            card = self.by_id[task_tool_id]
            task = {
                "task_id": scenario,
                "current_ref": self.profile["current_ref"],
                "input_types": card["accepted_input_types"],
                "required_outputs": card["output_types"],
                "allowed_execution_modes": ["READ_ONLY_RUN"],
            }
            planned = planner.plan_tool_route(task, include_experimental_tool_ids=allowlist)
            selected = [row["tool_id"] for row in planned["selected_tools"]]
            self.assertEqual(planned["decision"], "COMPLETE")
            self.assertEqual(selected, [task_tool_id])
            self.assertFalse(planned["execution_authorized"])
            self.assertEqual(saved[scenario]["selected_tool_ids"], selected)
            self.assertEqual(saved[scenario]["candidate_rejection_reason"], "NO_INPUT_TYPE_MATCH")


if __name__ == "__main__":
    unittest.main()
