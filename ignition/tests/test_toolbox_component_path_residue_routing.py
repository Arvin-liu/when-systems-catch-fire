from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "maintenance.summarize_component_path_residue"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-component-path-residue-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-component-path-residue-route-evidence-r0.json"


class ComponentPathResidueRouteTests(unittest.TestCase):
    def test_default_off_and_explicit_allowlist_route_are_replayable(self) -> None:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        catalog_sha = planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes())

        default = planner.plan_tool_route(profile)
        explicit = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(explicit["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in explicit["selected_tools"]], [TOOL_ID])
        self.assertFalse(explicit["execution_authorized"])
        self.assertEqual(explicit["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertFalse(explicit["selected_tools"][0]["permissions"]["network"])

        self.assertEqual(evidence["candidate_catalog_git_blob_sha1"], catalog_sha)
        self.assertTrue(evidence["catalog_replay"]["all_expected_decisions_reproduced"])
        self.assertEqual(evidence["catalog_replay"]["provider_calls_made"], 0)
        self.assertFalse(evidence["catalog_replay"]["execution_authorized"])
        self.assertEqual(evidence["route_trials"][0]["decision"], default["decision"])
        self.assertEqual(evidence["route_trials"][0]["selected_tool_ids"], [])
        self.assertEqual(evidence["route_trials"][1]["decision"], explicit["decision"])
        self.assertEqual(evidence["route_trials"][1]["selected_tool_ids"], [TOOL_ID])
        self.assertEqual(evidence["route_trials"][1]["router_provider_calls"], 0)
        self.assertFalse(evidence["route_trials"][1]["candidate_invoked"])
        self.assertFalse(evidence["route_trials"][1]["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
