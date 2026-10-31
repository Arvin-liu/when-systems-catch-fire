from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


NEW_TOOL = "maintenance.summarize_actions_interval_union"
TIMELINE_TOOL = "maintenance.summarize_actions_step_timeline"
REPEATED_TOOL = "maintenance.compare_actions_repeated_step_sequences"


def profile(inputs: list[str], outputs: list[str]) -> dict:
    return {
        "task_id": "pr264-multi-run-observed-interval-union",
        "current_ref": "refs/heads/main@483658e2ff57ad553c3fda762ed855a8bd93ebbe",
        "input_types": inputs,
        "required_outputs": outputs,
        "allowed_execution_modes": ["READ_ONLY_RUN"],
    }


class ActionsIntervalUnionRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        cls.cards = {row["tool_id"]: row for row in catalog["candidates"]}
        cls.card = cls.cards[NEW_TOOL]
        cls.task = profile(
            cls.card["accepted_input_types"] + cls.cards[REPEATED_TOOL]["accepted_input_types"],
            [cls.card["output_types"][0]],
        )

    def test_route_is_default_off_then_selects_only_minimum_sufficient_tool(self) -> None:
        default = planner.plan_tool_route(self.task)
        light = planner.plan_tool_route(self.task, include_experimental_tool_ids=[TIMELINE_TOOL])
        adequate = planner.plan_tool_route(self.task, include_experimental_tool_ids=[NEW_TOOL])
        redundant = planner.plan_tool_route(
            self.task,
            include_experimental_tool_ids=[NEW_TOOL, TIMELINE_TOOL, REPEATED_TOOL],
        )

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(light["decision"], "INCOMPLETE")
        self.assertEqual(adequate["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in adequate["selected_tools"]], [NEW_TOOL])
        self.assertEqual(redundant["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in redundant["selected_tools"]], [NEW_TOOL])
        self.assertFalse(any(row["execution_authorized"] for row in (default, light, adequate, redundant)))
        self.assertTrue(all(row["cost_estimate"]["status"] == "UNKNOWN" for row in (default, light, adequate, redundant)))
        self.assertTrue(all(not row["selected_tools"] or row["selected_tools"][0]["permissions"]["network"] is False for row in (adequate, redundant)))

        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-actions-interval-union-route-evidence-r0.json").read_text(encoding="utf-8")
        )
        plans = {
            "default_off": default,
            "repeated_step_only_insufficient": light,
            "adequate_explicit_allowlist": adequate,
            "redundant_allowlist": redundant,
        }
        for name, route in plans.items():
            saved = evidence["scenario_results"][name]
            self.assertEqual(saved["decision"], route["decision"])
            self.assertEqual(saved["selected_tool_ids"], [row["tool_id"] for row in route["selected_tools"]])
            self.assertEqual(saved["execution_authorized"], route["execution_authorized"])
            self.assertEqual(saved["cost_estimate"]["status"], route["cost_estimate"]["status"])
        self.assertEqual(
            evidence["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )


if __name__ == "__main__":
    unittest.main()
