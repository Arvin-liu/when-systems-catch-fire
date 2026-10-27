from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "research.lookup_noaa_global_sf6_annual_growth"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-noaa-sf6-annual-growth-lookup-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-noaa-sf6-annual-growth-lookup-route-evidence-r0.json"


class NoaaSf6AnnualGrowthLookupRoutingTests(unittest.TestCase):
    def test_default_off_explicit_exact_host_missing_host_and_other_gas_routes_replay(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(evidence["candidate_tool_id"], TOOL_ID)
        self.assertEqual(
            evidence["candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()),
        )
        self.assertEqual(
            evidence["current_registry_git_blob_sha1"],
            planner.git_blob_sha1(planner.REGISTRY_PATH.read_bytes()),
        )
        self.assertEqual(
            evidence["routing_contract_sha256"],
            hashlib.sha256(Path(planner.__file__).read_bytes()).hexdigest(),
        )
        self.assertEqual(
            evidence["route_profile_sha256"],
            hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        )
        self.assertEqual(profile["task_id"], "noaa-gml-sf6-raw-table-annual-growth-2023-2025")

        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                actual = planner.plan_tool_route(
                    trial["task_profile"],
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                canonical = json.dumps(
                    actual, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ).encode("utf-8")
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), trial["planner_output_sha256"])
                self.assertEqual(actual["decision"], trial["expected_decision"])
                self.assertEqual(
                    [row["tool_id"] for row in actual["selected_tools"]],
                    trial["expected_selected_tool_ids"],
                )
                self.assertFalse(actual["execution_authorized"])
                self.assertFalse(trial["candidate_invoked"])
                self.assertEqual(trial["network_calls_made"], 0)
                for rejection in trial["expected_rejections"]:
                    self.assertIn(rejection, actual["rejected_candidates"])

        trials = {trial["scenario"]: trial for trial in evidence["route_trials"]}
        self.assertEqual(trials["DEFAULT_OFF_RAW_ONLY"]["expected_selected_tool_ids"], [])
        exact = trials["EXPLICIT_RAW_ONLY_EXACT_HOST"]
        self.assertEqual(exact["expected_selected_tool_ids"], [TOOL_ID])
        plan = planner.plan_tool_route(
            exact["task_profile"], include_experimental_tool_ids=exact["include_experimental_tool_ids"]
        )
        self.assertEqual(plan["selected_tools"][0]["permissions"]["network_hosts"], ["gml.noaa.gov"])
        self.assertEqual(plan["selected_tools"][0]["permissions"]["write_paths"], [])

        missing = trials["EXPLICIT_RAW_ONLY_HOST_MISSING"]
        self.assertEqual(missing["expected_selected_tool_ids"], [])
        self.assertIn(
            {"tool_id": TOOL_ID, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            missing["expected_rejections"],
        )
        broad = trials["EXPLICIT_RAW_ONLY_OVERBROAD_HOST_LIST"]
        broad_plan = planner.plan_tool_route(
            broad["task_profile"], include_experimental_tool_ids=broad["include_experimental_tool_ids"]
        )
        self.assertEqual(broad_plan["selected_tools"][0]["permissions"]["network_hosts"], ["gml.noaa.gov"])
        other_gas = trials["OTHER_GAS_ONLY"]
        self.assertEqual(
            other_gas["expected_selected_tool_ids"],
            ["research.lookup_noaa_global_n2o_annual_growth"],
        )
        self.assertIn(
            {"tool_id": TOOL_ID, "reason": "NO_INPUT_TYPE_MATCH"},
            other_gas["expected_rejections"],
        )
        self.assertFalse(evidence["summary"]["execution_authorized"])
        self.assertFalse(evidence["summary"]["candidate_invoked"])
        self.assertEqual(evidence["summary"]["network_calls_made"], 0)


if __name__ == "__main__":
    unittest.main()
