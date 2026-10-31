from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


class ActionsCheckObservationRoutingTests(unittest.TestCase):
    def test_new_tool_is_default_off_and_only_selected_for_exact_check_observations(self) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        tool_id = "maintenance.inspect_exact_head_check_observations"
        card = next(row for row in catalog["candidates"] if row["tool_id"] == tool_id)
        task = {
            "task_id": "classify-supplied-exact-head-check-name-and-app-observations",
            "current_ref": "refs/heads/main@483658e2ff57ad553c3fda762ed855a8bd93ebbe",
            "input_types": card["accepted_input_types"],
            "required_outputs": card["output_types"],
            "allowed_execution_modes": ["READ_ONLY_RUN"],
        }
        default = planner.plan_tool_route(task)
        opted_in = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=[
                tool_id,
                "maintenance.summarize_actions_step_timeline",
                "maintenance.attribute_actions_validation_evidence",
            ],
        )
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(opted_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted_in["selected_tools"]], [tool_id])
        self.assertFalse(opted_in["execution_authorized"])
        permissions = opted_in["selected_tools"][0]["permissions"]
        self.assertEqual(permissions["write_paths"], [])
        self.assertFalse(permissions["network"])
        self.assertFalse(permissions["secrets"])
        self.assertFalse(permissions["billing"])
        self.assertFalse(permissions["external_actions"])
        self.assertEqual(
            {row["tool_id"]: row["reason"] for row in opted_in["rejected_candidates"] if row["tool_id"] in {
                "maintenance.summarize_actions_step_timeline",
                "maintenance.attribute_actions_validation_evidence",
            }},
            {
                "maintenance.summarize_actions_step_timeline": "NO_INPUT_TYPE_MATCH",
                "maintenance.attribute_actions_validation_evidence": "NO_INPUT_TYPE_MATCH",
            },
        )
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-actions-check-observations-route-evidence-r0.json")
            .read_text(encoding="utf-8")
        )
        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                result = planner.plan_tool_route(
                    evidence["task_profile"],
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                self.assertEqual(result["decision"], trial["decision"])
                self.assertEqual(
                    [row["tool_id"] for row in result["selected_tools"]],
                    trial["selected_tool_ids"],
                )
                self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
