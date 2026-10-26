from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


class PubMedQuerySearchRoutingTests(unittest.TestCase):
    def test_default_off_host_allowlist_and_redundant_source_trials_replay(self) -> None:
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-pubmed-query-search-route-evidence-r0.json")
            .read_text(encoding="utf-8")
        )
        profile = evidence["route_profile"]
        current_catalog = planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes())
        self.assertEqual(evidence["candidate_catalog_git_blob_sha1"], current_catalog)
        self.assertEqual(profile["candidate_catalog_git_blob_sha1"], current_catalog)
        self.assertEqual(profile["current_registry_git_blob_sha1"], evidence["current_registry_git_blob_sha1"])
        self.assertFalse(evidence["summary"]["execution_authorized"])
        self.assertFalse(evidence["summary"]["router_rule_modified"])

        for trial in evidence["route_trials"]:
            task = trial["task_profile"]
            actual = planner.plan_tool_route(
                task,
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(actual["decision"], trial["expected_decision"], trial["scenario"])
            self.assertEqual(
                [row["tool_id"] for row in actual["selected_tools"]],
                trial["expected_selected_tool_ids"],
                trial["scenario"],
            )
            self.assertEqual(actual["execution_authorized"], trial["expected_execution_authorized"])
            for rejection in trial["expected_rejections"]:
                self.assertIn(rejection, actual["rejected_candidates"], trial["scenario"])

        default = evidence["route_trials"][0]["actual_result"]
        self.assertEqual(default["selected_tools"], [])
        missing_host = evidence["route_trials"][1]["actual_result"]
        self.assertEqual(missing_host["selected_tools"], [])
        explicit = evidence["route_trials"][2]["actual_result"]
        self.assertEqual([row["tool_id"] for row in explicit["selected_tools"]], ["research.search_pubmed_query"])
        self.assertEqual(
            explicit["selected_tools"][0]["permissions"]["network_hosts"],
            ["eutils.ncbi.nlm.nih.gov"],
        )
        redundant = evidence["route_trials"][3]["actual_result"]
        self.assertEqual([row["tool_id"] for row in redundant["selected_tools"]], ["research.search_pubmed_query"])


if __name__ == "__main__":
    unittest.main()
