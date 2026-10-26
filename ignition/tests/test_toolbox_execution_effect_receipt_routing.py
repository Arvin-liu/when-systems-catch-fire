from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "maintenance.preflight_execution_effect_receipt"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-execution-effect-receipt-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-execution-effect-receipt-route-evidence-r0.json"


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ExecutionEffectReceiptRoutingTests(unittest.TestCase):
    def profile(self) -> dict:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    def test_default_off_and_explicit_selection_only_propose_the_read_only_candidate(self) -> None:
        profile = self.profile()
        default = planner.plan_tool_route(profile)
        explicit = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertIn({"tool_id": TOOL_ID, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"}, default["rejected_candidates"])
        self.assertEqual(explicit["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in explicit["selected_tools"]], [TOOL_ID])
        self.assertFalse(default["execution_authorized"])
        self.assertFalse(explicit["execution_authorized"])
        selected = explicit["selected_tools"][0]
        self.assertFalse(selected["permissions"]["network"])
        self.assertFalse(selected["permissions"]["external_actions"])
        self.assertEqual(selected["permissions"]["write_paths"], [])

    def test_explicit_allowlist_does_not_route_an_unrelated_input(self) -> None:
        profile = self.profile()
        profile["input_types"] = ["ordinary prose"]
        result = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["selected_tools"], [])
        self.assertIn({"tool_id": TOOL_ID, "reason": "NO_INPUT_TYPE_MATCH"}, result["rejected_candidates"])

    def test_broad_allowlist_still_selects_only_the_matching_candidate(self) -> None:
        profile = self.profile()
        result = planner.plan_tool_route(
            profile,
            include_experimental_tool_ids=[
                TOOL_ID,
                "maintenance.preflight_failure_anchored_recovery",
                "collaboration.validate_portable_research_episode",
            ],
        )
        self.assertEqual([row["tool_id"] for row in result["selected_tools"]], [TOOL_ID])
        self.assertFalse(result["execution_authorized"])

    def test_route_evidence_replays_expected_decisions(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        profile = self.profile()
        self.assertEqual(
            evidence["candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )
        self.assertEqual(
            evidence["current_registry_git_blob_sha1"],
            planner.git_blob_sha1(planner.REGISTRY_PATH.read_bytes()),
        )
        self.assertEqual(evidence["route_profile_git_blob_sha1"], planner.git_blob_sha1(PROFILE_PATH.read_bytes()))
        self.assertEqual(evidence["route_trials_replayed"], len(evidence["route_trials"]))
        for trial in evidence["route_trials"]:
            result = planner.plan_tool_route(
                trial.get("task_profile", profile),
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(trial["decision"], result["decision"])
            self.assertEqual(trial["selected_tool_ids"], [row["tool_id"] for row in result["selected_tools"]])
            self.assertEqual(trial["result_sha256"], canonical_sha256(result))
            self.assertFalse(trial["candidate_invoked"])
            self.assertFalse(trial["execution_authorized"])
            self.assertEqual(trial["provider_calls_made"], 0)
        self.assertTrue(evidence["all_expected_decisions_reproduced"])
        self.assertFalse(evidence["candidate_invoked"])
        self.assertFalse(evidence["execution_authorized"])
        self.assertEqual(evidence["provider_calls_made"], 0)


if __name__ == "__main__":
    unittest.main()
