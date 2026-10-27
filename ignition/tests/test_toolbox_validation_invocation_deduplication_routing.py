from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "maintenance.plan_validation_invocation_deduplication"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-validation-invocation-dedup-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-validation-invocation-dedup-route-evidence-r0.json"


class ValidationInvocationDedupRoutingTests(unittest.TestCase):
    def test_default_off_and_explicit_route_do_not_authorize_or_invoke(self) -> None:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        current_catalog_sha = planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes())

        default = planner.plan_tool_route(profile)
        explicit = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(explicit["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in explicit["selected_tools"]], [TOOL_ID])
        self.assertFalse(explicit["execution_authorized"])
        self.assertEqual(explicit["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertFalse(explicit["selected_tools"][0]["permissions"]["network"])

        trials = {row["scenario"]: row for row in evidence["route_trials"]}
        self.assertEqual(trials["default_off"]["decision"], default["decision"])
        self.assertEqual(trials["explicit_allowlist"]["decision"], explicit["decision"])
        self.assertEqual(trials["explicit_allowlist"]["selected_tool_ids"], [TOOL_ID])
        self.assertEqual(evidence["candidate_catalog_git_blob_sha1"], current_catalog_sha)
        self.assertTrue(evidence["catalog_replay"]["all_expected_decisions_reproduced"])
        self.assertEqual(trials["default_off"]["provider_calls_made"], 0)
        self.assertEqual(trials["explicit_allowlist"]["provider_calls_made"], 0)
        self.assertFalse(trials["explicit_allowlist"]["candidate_invoked"])
        self.assertFalse(trials["explicit_allowlist"]["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
