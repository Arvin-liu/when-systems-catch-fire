from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "maintenance.compare_toolbox_component_coverage"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-component-comparison-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-component-comparison-route-evidence-r0.json"


class ToolboxComponentComparisonRoutingTests(unittest.TestCase):
    def test_default_off_and_explicit_allowlist_route_without_invocation(self) -> None:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        catalog_sha = planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes())

        default = planner.plan_tool_route(profile)
        allowed = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(allowed["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in allowed["selected_tools"]], [TOOL_ID])
        permissions = allowed["selected_tools"][0]["permissions"]
        self.assertEqual(permissions["write_paths"], [])
        self.assertFalse(permissions["network"])
        self.assertFalse(permissions["secrets"])
        self.assertFalse(permissions["billing"])
        self.assertFalse(permissions["external_actions"])
        self.assertFalse(allowed["execution_authorized"])

        self.assertEqual(evidence["candidate_catalog_git_blob_sha1"], catalog_sha)
        self.assertEqual(evidence["route_trials"][0]["decision"], default["decision"])
        self.assertEqual(evidence["route_trials"][1]["decision"], allowed["decision"])
        self.assertEqual(evidence["route_trials"][1]["selected_tool_ids"], [TOOL_ID])
        self.assertFalse(evidence["route_trials"][1]["candidate_invoked"])
        self.assertEqual(evidence["router_provider_calls"], 0)


if __name__ == "__main__":
    unittest.main()
