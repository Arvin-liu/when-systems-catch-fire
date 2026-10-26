from __future__ import annotations

import json
import hashlib
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "research.match_pubmed_citation"
HOST = "eutils.ncbi.nlm.nih.gov"
CATALOG = IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json"


class PubMedCitationMatcherRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.card = next(row for row in catalog["candidates"] if row["tool_id"] == TOOL_ID)
        cls.task = {
            "task_id": "structured-citation-to-pubmed-id",
            "current_ref": "refs/heads/main@483658e2ff57ad553c3fda762ed855a8bd93ebbe",
            "input_types": cls.card["accepted_input_types"],
            "required_outputs": [cls.card["output_types"][0]],
            "allowed_execution_modes": ["READ_ONLY_RUN"],
        }

    def test_candidate_is_excluded_by_default(self) -> None:
        result = planner.plan_tool_route(self.task)
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["selected_tools"], [])
        self.assertIn(
            {"tool_id": TOOL_ID, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"},
            result["rejected_candidates"],
        )
        self.assertFalse(result["execution_authorized"])

    def test_allowlist_without_exact_host_permission_remains_incomplete(self) -> None:
        result = planner.plan_tool_route(self.task, include_experimental_tool_ids=[TOOL_ID])
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["selected_tools"], [])
        self.assertIn(
            {"tool_id": TOOL_ID, "reason": "NETWORK_HOST_NOT_EXPLICITLY_ALLOWED"},
            result["rejected_candidates"],
        )
        self.assertFalse(result["execution_authorized"])

    def test_explicit_host_and_tool_allowlist_select_only_this_optional_adapter(self) -> None:
        task = {**self.task, "allowed_network_hosts": [HOST]}
        result = planner.plan_tool_route(task, include_experimental_tool_ids=[TOOL_ID])
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in result["selected_tools"]], [TOOL_ID])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["selected_tools"][0]["permissions"]["network_hosts"], [HOST])

    def test_redundant_generic_query_candidate_is_not_selected_for_structured_match(self) -> None:
        task = {**self.task, "allowed_network_hosts": [HOST]}
        result = planner.plan_tool_route(
            task,
            include_experimental_tool_ids=[TOOL_ID, "research.search_pubmed_query"],
        )
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in result["selected_tools"]], [TOOL_ID])
        self.assertIn(
            {"tool_id": "research.search_pubmed_query", "reason": "NO_INPUT_TYPE_MATCH"},
            result["rejected_candidates"],
        )
        self.assertFalse(result["execution_authorized"])

    def test_checked_in_route_evidence_replays_without_invoking_tools(self) -> None:
        evidence = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-pubmed-citation-matcher-route-evidence-r0.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["tool_id"], TOOL_ID)
        self.assertEqual(
            evidence["candidate_catalog_git_blob_sha1"],
            planner.git_blob_sha1(CATALOG.read_bytes()),
        )
        self.assertEqual(
            evidence["current_registry_git_blob_sha1"],
            planner.git_blob_sha1(planner.REGISTRY_PATH.read_bytes()),
        )
        for trial in evidence["route_trials"]:
            with self.subTest(scenario=trial["scenario"]):
                result = planner.plan_tool_route(
                    trial["task_profile"],
                    include_experimental_tool_ids=trial["include_experimental_tool_ids"],
                )
                encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                self.assertEqual(result["decision"], trial["decision"])
                self.assertEqual([row["tool_id"] for row in result["selected_tools"]], trial["selected_tool_ids"])
                self.assertFalse(result["execution_authorized"])
                self.assertFalse(trial["candidate_invoked"])
                self.assertEqual(trial["provider_calls"], 0)
                self.assertEqual(hashlib.sha256(encoded).hexdigest(), trial["full_planner_output_sha256"])


if __name__ == "__main__":
    unittest.main()
