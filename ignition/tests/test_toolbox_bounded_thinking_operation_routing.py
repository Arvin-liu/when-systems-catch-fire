from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.operations import plan_ignition_operation_run as planner


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_ID = "ignition.select_bounded_thinking_operation"


class BoundedThinkingOperationRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        cls.card = next(row for row in catalog["candidates"] if row["tool_id"] == TOOL_ID)

    def task(self):
        return {
            "task_id": "bounded-thinking-operation-route-smoke",
            "current_ref": "caller-declared-current-ref",
            "input_types": self.card["accepted_input_types"],
            "required_outputs": self.card["output_types"],
            "allowed_execution_modes": ["READ_ONLY_RUN"],
        }

    def test_new_operation_is_default_off_and_explicitly_selectable(self) -> None:
        default = planner.plan_tool_route(self.task())
        opted_in = planner.plan_tool_route(
            self.task(),
            include_experimental_tool_ids=[TOOL_ID],
        )
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(opted_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted_in["selected_tools"]], [TOOL_ID])
        self.assertFalse(opted_in["execution_authorized"])
        self.assertFalse(opted_in["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(opted_in["selected_tools"][0]["permissions"]["write_paths"], [])

    def test_irrelevant_experimental_tool_is_rejected_even_with_host_context(self) -> None:
        task = self.task()
        task["allowed_network_hosts"] = ["api.crossref.org"]
        result = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=[TOOL_ID, "research.verify_crossref_metadata"],
        )
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in result["selected_tools"]], [TOOL_ID])
        self.assertIn(
            {"tool_id": "research.verify_crossref_metadata", "reason": "NO_INPUT_TYPE_MATCH"},
            result["rejected_candidates"],
        )
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
