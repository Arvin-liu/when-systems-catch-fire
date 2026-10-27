from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402

TOOL_ID = "maintenance.compare_source_section_bytes"
FEATURE_COMMIT = "ac2a5df1a925e3d2b52d33f79e1e415fff908cb6"
CURRENT_REF = f"refs/heads/codex/toolbox-growth-20261025@{FEATURE_COMMIT}"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-route-evidence-r0.json"
EXECUTION_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-route-execution-evidence-r0.json"
REAL_TASK_EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-real-task-evidence-r0.json"
REAL_TASK_OUTPUT_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-real-task-output-r0.json"
SOURCE_PATH = IGNITION_ROOT / "tools/toolbox_compare_source_section_bytes.py"
ROUTE_TEST_PATH = IGNITION_ROOT / "tests/test_toolbox_source_section_parity_routing.py"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_sha256(value: dict) -> str:
    return _sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _historical_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{FEATURE_COMMIT}:{path}"], cwd=REPO_ROOT)


class SourceSectionParityRoutingTests(unittest.TestCase):
    def test_exact_feature_head_is_default_off_and_route_trials_are_proposals_only(self) -> None:
        profile_bytes = PROFILE_PATH.read_bytes()
        profile = json.loads(profile_bytes)
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        execution = json.loads(EXECUTION_PATH.read_text(encoding="utf-8"))
        real_task = json.loads(REAL_TASK_EVIDENCE_PATH.read_text(encoding="utf-8"))
        real_output_bytes = REAL_TASK_OUTPUT_PATH.read_bytes()
        candidate_bytes = planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()
        catalog = json.loads(candidate_bytes)
        card = next(row for row in catalog["candidates"] if row["tool_id"] == TOOL_ID)
        self.assertEqual(
            card["permissions"]["read_paths"],
            [".github/", "docs/", "ignition/", "HUMAN-READING.md", "README.md", "SUMMARY.md", "llms.txt"],
        )

        self.assertEqual(evidence["candidate_head"], FEATURE_COMMIT)
        self.assertEqual(profile["current_ref"], CURRENT_REF)
        self.assertEqual(evidence["current_ref"], CURRENT_REF)
        self.assertEqual(execution["current_ref"], CURRENT_REF)
        self.assertEqual(_sha256(profile_bytes), evidence["route_profile_sha256"])
        self.assertEqual(planner.git_blob_sha1(candidate_bytes), evidence["candidate_catalog_git_blob_sha1"])
        self.assertEqual(len(catalog["candidates"]), evidence["candidate_count"])
        self.assertEqual(_sha256(ROUTE_TEST_PATH.read_bytes()), evidence["route_test_source_sha256"])
        self.assertEqual(_sha256(SOURCE_PATH.read_bytes()), evidence["tool_source_sha256"])
        self.assertEqual(_sha256(SOURCE_PATH.read_bytes()), _sha256(_historical_bytes("ignition/tools/toolbox_compare_source_section_bytes.py")))

        historical_catalog = json.loads(_historical_bytes("ignition/data/operations/toolbox-candidate-cards-r0.json"))
        self.assertIn(TOOL_ID, [row["tool_id"] for row in historical_catalog["candidates"]])
        self.assertEqual(len(historical_catalog["candidates"]), evidence["feature_commit_candidate_count"])
        self.assertEqual(real_task["tool_id"], TOOL_ID)
        self.assertEqual(real_task["tool_version"], "0.1.0")
        self.assertEqual(real_task["output_sha256"], _sha256(real_output_bytes))
        self.assertEqual(real_task["input_sha256"], evidence["real_task_input_sha256"])
        self.assertEqual(real_task["output_sha256"], evidence["real_task_output_sha256"])

        all_ids = sorted(row["tool_id"] for row in catalog["candidates"])
        allowlists = {
            "default_off": [],
            "tool_only": [TOOL_ID],
            "broad_allowlist": all_ids,
            "other_candidates_only": [tool_id for tool_id in all_ids if tool_id != TOOL_ID],
            "unrelated_input": [TOOL_ID],
        }
        expected = {
            "default_off": ("INCOMPLETE", [], "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"),
            "tool_only": ("INCOMPLETE", [], "PERMISSION_PATH_UNAVAILABLE_OR_UNSAFE"),
            "broad_allowlist": ("INCOMPLETE", [], "PERMISSION_PATH_UNAVAILABLE_OR_UNSAFE"),
            "other_candidates_only": ("INCOMPLETE", [], "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"),
            "unrelated_input": ("INCOMPLETE", [], "PERMISSION_PATH_UNAVAILABLE_OR_UNSAFE"),
        }
        recorded = {row["scenario"]: row for row in evidence["route_trials"]}
        self.assertEqual(set(recorded), set(expected))
        for scenario, allowlist in allowlists.items():
            task_profile = dict(profile)
            if scenario == "unrelated_input":
                task_profile["input_types"] = ["Unrelated prose document"]
            plan = planner.plan_tool_route(task_profile, include_experimental_tool_ids=allowlist)
            decision, selected_ids, rejection_reason = expected[scenario]
            row = recorded[scenario]
            self.assertEqual(plan["decision"], decision, scenario)
            self.assertEqual([tool["tool_id"] for tool in plan["selected_tools"]], selected_ids, scenario)
            self.assertEqual(row["decision"], decision, scenario)
            self.assertEqual(row["selected_tool_ids"], selected_ids, scenario)
            self.assertEqual(row["rejection_reason"], rejection_reason, scenario)
            self.assertEqual(
                next(item["reason"] for item in plan["rejected_candidates"] if item["tool_id"] == TOOL_ID),
                rejection_reason,
                scenario,
            )
            self.assertEqual(row["plan_sha256"], _canonical_json_sha256(plan), scenario)
            self.assertEqual(plan["allowed_network_hosts"], [], scenario)
            self.assertFalse(plan["execution_authorized"], scenario)
            self.assertFalse(row["execution_authorized"], scenario)

        self.assertEqual(evidence["safety_boundary"]["tool_invocations_by_planner"], 0)
        self.assertFalse(evidence["safety_boundary"]["execution_authorized"])
        self.assertEqual(execution["tool_id"], TOOL_ID)
        self.assertEqual(execution["candidate_catalog_git_blob_sha1"], evidence["candidate_catalog_git_blob_sha1"])
        self.assertEqual(execution["route_profile_sha256"], _sha256(profile_bytes))
        self.assertEqual(execution["route_evidence_sha256"], _sha256(EVIDENCE_PATH.read_bytes()))
        self.assertEqual(execution["tool_source_sha256"], _sha256(SOURCE_PATH.read_bytes()))
        self.assertEqual(execution["tool_invocations_by_route_planner"], 0)
        self.assertFalse(execution["execution_authorized_by_route_planner"])
        self.assertTrue(execution["manual_tool_result_recorded_separately"])
        self.assertFalse(execution["raw_source_text_retained"])
        self.assertFalse(execution["network_permission"])
        self.assertFalse(execution["tool_file_writes"])


if __name__ == "__main__":
    unittest.main()
