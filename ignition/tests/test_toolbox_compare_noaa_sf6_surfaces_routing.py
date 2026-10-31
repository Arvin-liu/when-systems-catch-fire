from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "research.compare_noaa_sf6_source_surfaces"
RAW_LOOKUP_ID = "research.lookup_noaa_global_sf6_annual_growth"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-noaa-sf6-source-surface-comparison-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-noaa-sf6-source-surface-comparison-route-evidence-r0.json"
CATALOG_PATH = planner.EXPERIMENTAL_TOOL_CARDS_PATH


class NoaaSf6SourceSurfaceRoutingTests(unittest.TestCase):
    def test_route_receipt_is_bound_to_current_catalog_registry_profile_and_planner(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema_version"], "toolbox-noaa-sf6-source-surface-comparison-route-evidence-r0")
        self.assertEqual(evidence["candidate_tool_id"], TOOL_ID)
        self.assertEqual(evidence["compared_existing_tool_id"], RAW_LOOKUP_ID)
        self.assertEqual(evidence["route_trials_replayed"], 8)
        self.assertTrue(evidence["all_expected_decisions_reproduced"])
        self.assertEqual(evidence["candidate_catalog_git_blob_sha1"], planner.git_blob_sha1(CATALOG_PATH.read_bytes()))
        self.assertEqual(evidence["current_registry_git_blob_sha1"], planner.git_blob_sha1(planner.REGISTRY_PATH.read_bytes()))
        self.assertEqual(evidence["route_profile_sha256"], hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest())
        self.assertEqual(evidence["routing_contract_sha256"], hashlib.sha256(Path(planner.__file__).read_bytes()).hexdigest())

    def test_default_off_permissions_and_task_scoped_selection(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        cards = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["candidates"]
        card = next(row for row in cards if row["tool_id"] == TOOL_ID)
        self.assertEqual(card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertEqual(card["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertFalse(card["router_selectable_by_default"])
        self.assertEqual(card["comparison_evidence"]["status"], "SPECIALIZED_NO_REPLACEMENT_ESTABLISHED")
        self.assertEqual(card["deprecation_or_retirement_status"]["status"], "SPECIALIZED")
        self.assertEqual(card["replacement_candidates"], [])
        self.assertTrue(card["unique_remaining_use_cases"])
        self.assertEqual(card["permissions"]["network_hosts"], ["gml.noaa.gov"])
        self.assertEqual(card["permissions"]["write_paths"], [])
        self.assertFalse(card["permissions"]["secrets"])
        self.assertFalse(card["permissions"]["billing"])
        self.assertFalse(card["permissions"]["external_actions"])

        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                actual = planner.plan_tool_route(
                    trial["task_profile"],
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                canonical = json.dumps(actual, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), trial["planner_output_sha256"])
                self.assertEqual(actual["decision"], trial["expected_decision"])
                self.assertEqual([row["tool_id"] for row in actual["selected_tools"]], trial["expected_selected_tool_ids"])
                self.assertFalse(actual["execution_authorized"])
                self.assertFalse(trial["expected_execution_authorized"])
                self.assertFalse(trial["candidate_invoked"])
                self.assertEqual(trial["network_calls_made"], 0)
                for rejected in trial["expected_rejections"]:
                    self.assertIn(rejected, actual["rejected_candidates"])

        trials = {row["scenario"]: row for row in evidence["route_trials"]}
        self.assertEqual(trials["DEFAULT_COMPARATOR"]["expected_selected_tool_ids"], [])
        self.assertEqual(trials["EXPLICIT_COMPARATOR_EXACT_HOST"]["expected_selected_tool_ids"], [TOOL_ID])
        self.assertEqual(trials["COMPARATOR_HOST_MISSING"]["expected_decision"], "INCOMPLETE")
        self.assertEqual(trials["COMPARATOR_OVERBROAD_HOSTS"]["expected_selected_tool_ids"], [TOOL_ID])
        self.assertEqual(trials["COMPARATOR_WITH_RAW_LOOKUP"]["expected_selected_tool_ids"], [TOOL_ID])
        self.assertEqual(trials["RAW_ONLY_LOOKUP"]["expected_selected_tool_ids"], [RAW_LOOKUP_ID])
        self.assertEqual(trials["RAW_ONLY_WITH_COMPARATOR"]["expected_selected_tool_ids"], [RAW_LOOKUP_ID])
        self.assertEqual(trials["COMPARATOR_TASK_LOOKUP_ONLY"]["expected_decision"], "INCOMPLETE")
        self.assertFalse(evidence["summary"]["execution_authorized"])
        self.assertFalse(evidence["summary"]["candidate_invoked"])
        self.assertEqual(evidence["summary"]["network_calls_made"], 0)


if __name__ == "__main__":
    unittest.main()
