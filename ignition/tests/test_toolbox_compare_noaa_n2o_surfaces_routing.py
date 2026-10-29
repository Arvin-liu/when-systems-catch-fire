from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "research.compare_noaa_n2o_source_surfaces"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-noaa-n2o-source-surface-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-noaa-n2o-source-surface-route-evidence-r0.json"


class NoaaN2oSourceSurfaceRoutingTests(unittest.TestCase):
    def test_default_off_minimum_sufficient_route_and_missing_host_control(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(evidence["route_profile_sha256"], hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest())
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

        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                actual = planner.plan_tool_route(
                    trial["task_profile"],
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
                for expected in trial["expected_rejections"]:
                    self.assertIn(expected, actual["rejected_candidates"])
                if trial["scenario"] in {"EXPLICIT_EXACT_HOST", "OVERBROAD_ALLOWLIST"}:
                    self.assertEqual(selected, [TOOL_ID])
                    self.assertEqual(actual["selected_tools"][0]["permissions"]["network_hosts"], ["gml.noaa.gov"])
                else:
                    self.assertNotIn(TOOL_ID, selected)

        trials = {trial["scenario"]: trial for trial in evidence["route_trials"]}
        default = trials["DEFAULT_OFF"]
        explicit = trials["EXPLICIT_EXACT_HOST"]
        missing_host = trials["EXPLICIT_HOST_MISSING"]
        overbroad = trials["OVERBROAD_ALLOWLIST"]
        self.assertEqual(default["expected_decision"], "INCOMPLETE")
        self.assertEqual(default["expected_selected_tool_ids"], [])
        self.assertEqual(explicit["expected_decision"], "COMPLETE")
        self.assertEqual(explicit["expected_selected_tool_ids"], [TOOL_ID])
        self.assertEqual(missing_host["expected_decision"], "INCOMPLETE")
        self.assertEqual(missing_host["expected_selected_tool_ids"], [])
        self.assertEqual(overbroad["expected_decision"], "COMPLETE")
        self.assertEqual(overbroad["expected_selected_tool_ids"], [TOOL_ID])
        self.assertFalse(evidence["summary"]["execution_authorized"])
        self.assertFalse(evidence["summary"]["candidate_invoked"])
        self.assertEqual(evidence["summary"]["network_calls_made"], 0)


if __name__ == "__main__":
    unittest.main()
