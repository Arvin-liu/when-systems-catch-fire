from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from tools.operations.plan_ignition_operation_run import plan_tool_route


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_ID = "planning.compare_task_decomposition_solvability"
UNRELATED_TOOL_ID = "research.compare_evidence_update_snapshots"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-task-decomposition-solvability-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-task-decomposition-solvability-route-evidence-r0.json"
CATALOG_PATH = IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json"


def stable_planner_output_digest(result: dict) -> str:
    # The catalog blob appears in result.source_refs; omitting that field avoids
    # a self-reference because the candidate card itself pins this evidence file.
    projection = {key: value for key, value in result.items() if key != "source_refs"}
    payload = json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class TaskDecompositionSolvabilityRoutingTests(unittest.TestCase):
    def test_default_off_explicit_allowlist_and_unrelated_candidate_trials_replay(self):
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        card = next(item for item in catalog["candidates"] if item["tool_id"] == TOOL_ID)
        self.assertFalse(card["router_selectable_by_default"])

        for trial in evidence["route_trials"]:
            result = plan_tool_route(
                profile,
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            self.assertEqual(result["decision"], trial["decision"], trial["trial_id"])
            self.assertEqual([row["tool_id"] for row in result["selected_tools"]], trial["selected_tool_ids"])
            self.assertFalse(result["execution_authorized"])
            self.assertEqual(stable_planner_output_digest(result), trial["planner_output_projection_sha256"])
            self.assertEqual(trial["candidate_tool_invocation_count"], 0)
            if trial["trial_id"] == "default_off":
                self.assertIn({"tool_id": TOOL_ID, "reason": "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"}, result["rejected_candidates"])
            if trial["trial_id"] == "with_unrelated_candidate":
                self.assertIn({"tool_id": UNRELATED_TOOL_ID, "reason": "NO_INPUT_TYPE_MATCH"}, result["rejected_candidates"])

        explicit = next(item for item in evidence["route_trials"] if item["trial_id"] == "explicit_allowlist")
        self.assertEqual(explicit["selected_tool_ids"], [TOOL_ID])
        self.assertFalse(explicit["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
