from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "research.pair_noaa_co2_ch4_growth_by_year"
OPERATIONS = IGNITION_ROOT / "data/operations"
EVIDENCE_PATH = OPERATIONS / "toolbox-noaa-co2-ch4-growth-pair-route-evidence-r1.json"
PROFILE_PATHS = {
    "TWO_GAS": OPERATIONS / "toolbox-noaa-co2-ch4-growth-pair-route-profile-r1.json",
    "THREE_GAS": OPERATIONS / "toolbox-noaa-co2-ch4-n2o-growth-pair-route-profile-r1.json",
}


class NoaaGrowthPairRoutingTests(unittest.TestCase):
    def test_two_and_three_gas_routes_remain_default_off_and_single_n2o_rejects(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        profiles = {key: json.loads(path.read_text(encoding="utf-8")) for key, path in PROFILE_PATHS.items()}
        self.assertEqual(evidence["candidate_tool_id"], TOOL_ID)
        self.assertEqual(evidence["candidate_tool_version"], "0.2.0")
        self.assertEqual(evidence["candidate_catalog_git_blob_sha1"], planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()))
        self.assertEqual(evidence["current_registry_git_blob_sha1"], planner.git_blob_sha1(planner.REGISTRY_PATH.read_bytes()))
        self.assertEqual(evidence["routing_contract_sha256"], hashlib.sha256(Path(planner.__file__).read_bytes()).hexdigest())
        for profile in evidence["route_profiles"]:
            path = Path(profile["path"]).relative_to("ignition")
            profile_path = IGNITION_ROOT / path
            self.assertEqual(profile["sha256"], hashlib.sha256(profile_path.read_bytes()).hexdigest())
        self.assertEqual(evidence["route_trials_replayed"], 5)
        self.assertTrue(evidence["all_expected_decisions_reproduced"])

        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                profile_id = trial["route_profile_id"]
                if profile_id in profiles:
                    profile = profiles[profile_id]
                else:
                    profile = trial["task_profile"]
                self.assertEqual(trial["task_profile"], profile)
                actual = planner.plan_tool_route(
                    profile,
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                canonical = json.dumps(actual, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), trial["planner_output_sha256"])
                self.assertEqual(actual["decision"], trial["expected_decision"])
                selected = [row["tool_id"] for row in actual["selected_tools"]]
                self.assertEqual(selected, trial["expected_selected_tool_ids"])
                self.assertFalse(actual["execution_authorized"])
                self.assertFalse(trial["candidate_invoked"])
                self.assertEqual(trial["network_calls_made"], 0)
                self.assertEqual(
                    [row for row in actual["rejected_candidates"] if row["tool_id"] == TOOL_ID],
                    trial["actual_candidate_rejections"],
                )
                if trial["expected_rejections"]:
                    for expected in trial["expected_rejections"]:
                        self.assertIn(expected, actual["rejected_candidates"])

        self.assertFalse(evidence["summary"]["execution_authorized"])
        self.assertFalse(evidence["summary"]["candidate_invoked"])
        self.assertEqual(evidence["summary"]["network_calls_made"], 0)
        self.assertEqual(evidence["summary"]["three_gas_explicit_allowlist"], "COMPLETE_ONE_CANDIDATE_PROPOSED")
        self.assertEqual(evidence["summary"]["single_n2o_explicit_allowlist"], "INCOMPLETE_NO_INPUT_TYPE_MATCH")


if __name__ == "__main__":
    unittest.main()
