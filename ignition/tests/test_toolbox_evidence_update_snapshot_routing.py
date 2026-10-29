from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


EVIDENCE = IGNITION_ROOT / "data/operations/toolbox-evidence-update-snapshot-route-evidence-r0.json"


class EvidenceUpdateSnapshotRoutingTests(unittest.TestCase):
    def test_default_off_explicit_match_and_unrelated_allowlist(self) -> None:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
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
        self.assertFalse(evidence["summary"]["execution_authorized"])
        self.assertFalse(evidence["summary"]["router_rule_modified"])
        self.assertFalse(evidence["summary"]["candidate_invoked"])

        for trial in evidence["route_trials"]:
            actual = planner.plan_tool_route(
                trial["task_profile"],
                include_experimental_tool_ids=trial["include_experimental_tool_ids"],
            )
            actual_digest = hashlib.sha256(
                json.dumps(actual, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            self.assertEqual(actual_digest, trial["planner_output_sha256"], trial["scenario"])
            self.assertEqual(actual["decision"], trial["expected_decision"], trial["scenario"])
            self.assertEqual(
                [row["tool_id"] for row in actual["selected_tools"]],
                trial["expected_selected_tool_ids"],
                trial["scenario"],
            )
            self.assertEqual(actual["execution_authorized"], trial["expected_execution_authorized"], trial["scenario"])
            for rejection in trial["expected_rejections"]:
                self.assertIn(rejection, actual["rejected_candidates"], trial["scenario"])

            relevant_rejections = [
                row for row in actual["rejected_candidates"] if row in trial["expected_rejections"]
            ]
            self.assertEqual(relevant_rejections, trial["expected_rejections"], trial["scenario"])
            compact_result = {
                "schema_version": actual["schema_version"],
                "task_id": actual["task_id"],
                "current_ref": actual["current_ref"],
                "current_ref_binding": actual["current_ref_binding"],
                "decision": actual["decision"],
                "selected_tool_ids": [row["tool_id"] for row in actual["selected_tools"]],
                "allowed_network_hosts": actual["allowed_network_hosts"],
                "network_authority_binding": actual["network_authority_binding"],
                "required_outputs": actual["required_outputs"],
                "covered_outputs": actual["covered_outputs"],
                "unmet_outputs": actual["unmet_outputs"],
                "relevant_rejections": relevant_rejections,
                "rejected_candidate_count": len(actual["rejected_candidates"]),
                "omitted_rejected_candidate_count": len(actual["rejected_candidates"]) - len(relevant_rejections),
                "execution_authorized": actual["execution_authorized"],
            }
            self.assertEqual(compact_result, trial["actual_result"], trial["scenario"])

        default, explicit, unrelated = [row["actual_result"] for row in evidence["route_trials"]]
        self.assertEqual(default["selected_tool_ids"], [])
        self.assertEqual(explicit["selected_tool_ids"][0], "research.compare_evidence_update_snapshots")
        self.assertEqual(unrelated["selected_tool_ids"][0], "research.compare_evidence_update_snapshots")


if __name__ == "__main__":
    unittest.main()
