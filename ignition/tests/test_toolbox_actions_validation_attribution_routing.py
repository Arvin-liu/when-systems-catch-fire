from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
