from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "reasoning.search_structural_analogies"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-structural-analogy-search-route-evidence-r0.json"


class StructuralAnalogySearchRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        catalog = json.loads(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_text(encoding="utf-8"))
        cls.card = next(row for row in catalog["candidates"] if row["tool_id"] == TOOL_ID)
        cls.profile = {
            "task_id": "typed-cross-domain-structure-search",
            "current_ref": "refs/heads/main@483658e2ff57ad553c3fda762ed855a8bd93ebbe",
            "input_types": cls.card["accepted_input_types"],
            "required_outputs": cls.card["output_types"],
            "allowed_execution_modes": ["READ_ONLY_RUN"],
        }
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    def test_route_trials_are_reproducible_default_off_and_not_invocation(self) -> None:
        self.assertEqual(self.evidence["candidate_tool_id"], TOOL_ID)
        self.assertEqual(self.evidence["task_profile"], self.profile)
        for trial in self.evidence["trials"]:
            result = planner.plan_tool_route(
                self.profile,
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(result["decision"], trial["decision"])
            self.assertEqual([row["tool_id"] for row in result["selected_tools"]], trial["selected_tool_ids"])
            self.assertFalse(result["execution_authorized"])
            self.assertEqual(result["source_refs"]["experimental_candidate_catalog_git_blob_sha1"], self.evidence["candidate_catalog_git_blob_sha1"])
            self.assertEqual(trial["router_provider_calls"], 0)
            self.assertFalse(trial["candidate_invoked"])

    def test_candidate_is_default_off_and_explicit_allowlist_selects_only_it(self) -> None:
        default = planner.plan_tool_route(self.profile)
        allowed = planner.plan_tool_route(self.profile, include_experimental_tool_ids=[TOOL_ID])
        existing = planner.plan_tool_route(
            self.profile,
            include_experimental_tool_ids=["research.preflight_grounded_ideation"],
        )
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(allowed["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in allowed["selected_tools"]], [TOOL_ID])
        self.assertFalse(allowed["execution_authorized"])
        self.assertEqual(existing["decision"], "INCOMPLETE")
        self.assertEqual(existing["selected_tools"], [])
        permissions = allowed["selected_tools"][0]["permissions"]
        self.assertFalse(permissions["network"])
        self.assertEqual(permissions["write_paths"], [])
        self.assertFalse(permissions["secrets"])
        self.assertFalse(permissions["billing"])
        self.assertFalse(permissions["external_actions"])

    def test_combined_allowlist_keeps_the_distinct_graph_search_route(self) -> None:
        result = planner.plan_tool_route(
            self.profile,
            include_experimental_tool_ids=[TOOL_ID, "research.preflight_grounded_ideation"],
        )
        self.assertEqual(result["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in result["selected_tools"]], [TOOL_ID])
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
