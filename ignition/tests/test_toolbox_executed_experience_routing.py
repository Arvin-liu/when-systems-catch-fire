from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "knowledge.preflight_executed_experience_reuse"
RECEIPT_TOOL = "maintenance.preflight_execution_effect_receipt"


class ExecutedExperienceRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-executed-experience-route-profile-r0.json").read_text(encoding="utf-8")
        )
        cls.evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-executed-experience-route-evidence-r0.json").read_text(encoding="utf-8")
        )

    def test_default_off_explicit_allowlist_and_minimum_sufficient_route(self):
        default = planner.plan_tool_route(self.profile)
        exact = planner.plan_tool_route(self.profile, include_experimental_tool_ids=[TOOL_ID])
        comparator_only = planner.plan_tool_route(self.profile, include_experimental_tool_ids=[RECEIPT_TOOL])
        overallowlisted = planner.plan_tool_route(
            self.profile,
            include_experimental_tool_ids=[TOOL_ID, RECEIPT_TOOL],
        )
        expected = {
            "default_off": default,
            "exact_allowlist": exact,
            "adjacent_receipt_tool_only": comparator_only,
            "both_allowlisted": overallowlisted,
        }
        for key, plan in expected.items():
            saved = self.evidence["scenario_results"][key]
            self.assertEqual(saved["decision"], plan["decision"])
            self.assertEqual(saved["selected_tool_ids"], [row["tool_id"] for row in plan["selected_tools"]])
            self.assertEqual(saved["execution_authorized"], plan["execution_authorized"])
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(exact["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in exact["selected_tools"]], [TOOL_ID])
        self.assertEqual(comparator_only["decision"], "INCOMPLETE")
        self.assertEqual(overallowlisted["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in overallowlisted["selected_tools"]], [TOOL_ID])
        self.assertTrue(all(plan["execution_authorized"] is False for plan in expected.values()))
        self.assertTrue(all(not plan["selected_tools"] or plan["selected_tools"][0]["permissions"]["network"] is False for plan in expected.values()))
        self.assertEqual(
            self.evidence["candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )


if __name__ == "__main__":
    unittest.main()
