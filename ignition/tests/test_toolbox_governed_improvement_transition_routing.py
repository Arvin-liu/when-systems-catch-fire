from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "maintenance.preflight_governed_improvement_transition"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-governed-improvement-transition-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-governed-improvement-transition-route-evidence-r0.json"


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class GovernedImprovementTransitionRoutingTests(unittest.TestCase):
    def profile(self) -> dict:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    def test_default_off_and_explicit_allowlist_produce_only_a_route_proposal(self) -> None:
        profile = self.profile()
        default = planner.plan_tool_route(profile)
        explicit = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(explicit["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in explicit["selected_tools"]], [TOOL_ID])
        self.assertFalse(default["execution_authorized"])
        self.assertFalse(explicit["execution_authorized"])
        self.assertEqual(explicit["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertFalse(explicit["selected_tools"][0]["permissions"]["network"])
        self.assertIn(
            {"tool_id": TOOL_ID, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            default["rejected_candidates"],
        )

    def test_mismatched_input_type_does_not_route_even_with_explicit_allowlist(self) -> None:
        profile = self.profile()
        profile["input_types"] = ["ordinary markdown paragraph"]
        result = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["selected_tools"], [])
        self.assertIn({"tool_id": TOOL_ID, "reason": "NO_INPUT_TYPE_MATCH"}, result["rejected_candidates"])

    def test_route_evidence_replays_against_current_candidate_and_registry_blobs(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        profile = self.profile()
        catalog_sha = planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes())
        registry_sha = planner.git_blob_sha1(planner.REGISTRY_PATH.read_bytes())

        self.assertEqual(evidence["candidate_catalog_git_blob_sha1"], catalog_sha)
        self.assertEqual(evidence["current_registry_git_blob_sha1"], registry_sha)
        self.assertEqual(evidence["route_profile_git_blob_sha1"], planner.git_blob_sha1(PROFILE_PATH.read_bytes()))
        self.assertEqual(evidence["route_trials_replayed"], 2)
        self.assertTrue(evidence["all_expected_decisions_reproduced"])
        for trial in evidence["route_trials"]:
            result = planner.plan_tool_route(
                profile,
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(trial["decision"], result["decision"])
            self.assertEqual(trial["selected_tool_ids"], [row["tool_id"] for row in result["selected_tools"]])
            self.assertEqual(trial["result_sha256"], canonical_sha256(result))
            self.assertFalse(trial["candidate_invoked"])
            self.assertFalse(trial["execution_authorized"])
            self.assertEqual(trial["provider_calls_made"], 0)


if __name__ == "__main__":
    unittest.main()
