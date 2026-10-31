from __future__ import annotations

from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))

from operations.plan_ignition_operation_run import plan_tool_route  # noqa: E402


TOOL_ID = "collaboration.preflight_handoff_action_binding"


def profile(*, task_id: str, input_type: str) -> dict:
    return {
        "task_id": task_id,
        "current_ref": "caller-ref:synthetic-handoff-route",
        "input_types": [input_type],
        "required_outputs": ["handoff_action_binding_result"],
        "allowed_execution_modes": ["READ_ONLY_RUN"],
    }


class HandoffActionBindingRoutingTests(unittest.TestCase):
    def test_optional_tool_is_excluded_by_default(self) -> None:
        result = plan_tool_route(profile(task_id="default-off", input_type="federated_handoff_action_binding_records"))
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["selected_tools"], [])
        self.assertIn(
            {"tool_id": TOOL_ID, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            result["rejected_candidates"],
        )
        self.assertFalse(result["execution_authorized"])

    def test_explicit_allowlist_proposes_only_this_sufficient_tool(self) -> None:
        result = plan_tool_route(
            profile(task_id="handoff-preflight", input_type="federated_handoff_action_binding_records"),
            include_experimental_tool_ids=[TOOL_ID],
        )
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in result["selected_tools"]], [TOOL_ID])
        self.assertEqual(result["selected_tools"][0]["declared_effect_rank"], 0)
        self.assertEqual(result["cost_estimate"]["status"], "UNKNOWN")
        self.assertFalse(result["execution_authorized"])

    def test_unrelated_input_does_not_select_explicitly_allowed_tool(self) -> None:
        result = plan_tool_route(
            profile(task_id="unrelated-reading", input_type="plain_article_markdown"),
            include_experimental_tool_ids=[TOOL_ID],
        )
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["selected_tools"], [])
        self.assertIn({"tool_id": TOOL_ID, "reason": "NO_INPUT_TYPE_MATCH"}, result["rejected_candidates"])
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
