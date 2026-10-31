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
R0_EVIDENCE_COMMIT = "3faa2b3af9747ac5aa85e80c88df9467b0aad0d2"
CURRENT_REF = f"refs/heads/codex/toolbox-growth-20261025@{FEATURE_COMMIT}"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-route-evidence-r0.json"
EXECUTION_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-route-execution-evidence-r0.json"
REAL_TASK_EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-real-task-evidence-r0.json"
REAL_TASK_OUTPUT_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-real-task-output-r0.json"
R1_EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-source-section-parity-route-evidence-r1.json"
SOURCE_PATH = IGNITION_ROOT / "tools/toolbox_compare_source_section_bytes.py"
ROUTE_TEST_PATH = IGNITION_ROOT / "tests/test_toolbox_source_section_parity_routing.py"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_sha256(value: dict) -> str:
    return _sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _historical_bytes(path: str, revision: str = FEATURE_COMMIT) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=REPO_ROOT)


class SourceSectionParityRoutingTests(unittest.TestCase):
    def test_r0_route_evidence_remains_bound_to_its_historical_snapshot(self) -> None:
        profile_bytes = PROFILE_PATH.read_bytes()
        profile = json.loads(profile_bytes)
        evidence_bytes = EVIDENCE_PATH.read_bytes()
        evidence = json.loads(evidence_bytes)
        execution_bytes = EXECUTION_PATH.read_bytes()
        execution = json.loads(execution_bytes)
        real_task = json.loads(REAL_TASK_EVIDENCE_PATH.read_text(encoding="utf-8"))
        real_output_bytes = REAL_TASK_OUTPUT_PATH.read_bytes()

        self.assertEqual(evidence["candidate_head"], FEATURE_COMMIT)
        self.assertEqual(profile["current_ref"], CURRENT_REF)
        self.assertEqual(evidence["current_ref"], CURRENT_REF)
        self.assertEqual(execution["current_ref"], CURRENT_REF)
        self.assertEqual(_sha256(profile_bytes), evidence["route_profile_sha256"])
        historical_route_catalog_bytes = _historical_bytes(
            "ignition/data/operations/toolbox-candidate-cards-r0.json", R0_EVIDENCE_COMMIT
        )
        historical_route_catalog = json.loads(historical_route_catalog_bytes)
        self.assertEqual(
            planner.git_blob_sha1(historical_route_catalog_bytes), evidence["candidate_catalog_git_blob_sha1"]
        )
        self.assertEqual(
            _sha256(_historical_bytes("ignition/tools/operations/plan_ignition_operation_run.py", R0_EVIDENCE_COMMIT)),
            evidence["planner_source_sha256"],
        )
        self.assertEqual(
            _sha256(_historical_bytes("ignition/tests/test_toolbox_source_section_parity_routing.py", R0_EVIDENCE_COMMIT)),
            evidence["route_test_source_sha256"],
        )
        self.assertEqual(
            _sha256(_historical_bytes("ignition/tools/toolbox_compare_source_section_bytes.py", R0_EVIDENCE_COMMIT)),
            evidence["tool_source_sha256"],
        )
        self.assertEqual(evidence_bytes, _historical_bytes("ignition/data/operations/toolbox-source-section-parity-route-evidence-r0.json", R0_EVIDENCE_COMMIT))
        self.assertEqual(execution_bytes, _historical_bytes("ignition/data/operations/toolbox-source-section-parity-route-execution-evidence-r0.json", R0_EVIDENCE_COMMIT))
        historical_feature_catalog = json.loads(
            _historical_bytes("ignition/data/operations/toolbox-candidate-cards-r0.json", FEATURE_COMMIT)
        )
        self.assertIn(TOOL_ID, [row["tool_id"] for row in historical_feature_catalog["candidates"]])
        self.assertEqual(len(historical_feature_catalog["candidates"]), evidence["feature_commit_candidate_count"])
        self.assertEqual(real_task["tool_id"], TOOL_ID)
        self.assertEqual(real_task["tool_version"], "0.1.0")
        self.assertEqual(real_task["output_sha256"], _sha256(real_output_bytes))
        self.assertEqual(real_task["input_sha256"], evidence["real_task_input_sha256"])
        self.assertEqual(real_task["output_sha256"], evidence["real_task_output_sha256"])

        expected = {
            "default_off": ("INCOMPLETE", [], "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"),
            "tool_only": ("INCOMPLETE", [], "PERMISSION_PATH_UNAVAILABLE_OR_UNSAFE"),
            "broad_allowlist": ("INCOMPLETE", [], "PERMISSION_PATH_UNAVAILABLE_OR_UNSAFE"),
            "other_candidates_only": ("INCOMPLETE", [], "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"),
            "unrelated_input": ("INCOMPLETE", [], "PERMISSION_PATH_UNAVAILABLE_OR_UNSAFE"),
        }
        recorded = {row["scenario"]: row for row in evidence["route_trials"]}
        self.assertEqual(set(recorded), set(expected))
        for scenario, (decision, selected_ids, rejection_reason) in expected.items():
            row = recorded[scenario]
            self.assertEqual(row["decision"], decision, scenario)
            self.assertEqual(row["selected_tool_ids"], selected_ids, scenario)
            self.assertEqual(row["rejection_reason"], rejection_reason, scenario)
            self.assertFalse(row["execution_authorized"], scenario)
            self.assertEqual(row["allowed_network_hosts"], [], scenario)

        self.assertEqual(evidence["safety_boundary"]["tool_invocations_by_planner"], 0)
        self.assertFalse(evidence["safety_boundary"]["execution_authorized"])
        self.assertEqual(execution["tool_id"], TOOL_ID)
        self.assertEqual(execution["candidate_catalog_git_blob_sha1"], evidence["candidate_catalog_git_blob_sha1"])
        self.assertEqual(execution["route_profile_sha256"], _sha256(profile_bytes))
        self.assertEqual(execution["route_evidence_sha256"], _sha256(evidence_bytes))
        self.assertEqual(execution["tool_source_sha256"], evidence["tool_source_sha256"])
        self.assertEqual(execution["tool_invocations_by_route_planner"], 0)
        self.assertFalse(execution["execution_authorized_by_route_planner"])
        self.assertTrue(execution["manual_tool_result_recorded_separately"])
        self.assertFalse(execution["raw_source_text_retained"])
        self.assertFalse(execution["network_permission"])
        self.assertFalse(execution["tool_file_writes"])

    def test_r1_route_policy_is_default_off_and_only_proposes_for_matching_human_document_task(self) -> None:
        evidence = json.loads(R1_EVIDENCE_PATH.read_text(encoding="utf-8"))
        catalog_bytes = planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()
        catalog = json.loads(catalog_bytes)
        card = next(row for row in catalog["candidates"] if row["tool_id"] == TOOL_ID)
        task_profile = evidence["task_profile"]

        self.assertEqual(card["permissions"]["read_paths"], [".github/", "ignition/"])
        self.assertEqual(evidence["candidate_catalog_git_blob_sha1"], planner.git_blob_sha1(catalog_bytes))
        self.assertEqual(evidence["route_policy_source_sha256"], _sha256(Path(planner.__file__).read_bytes()))
        self.assertEqual(evidence["tool_source_sha256"], _sha256(SOURCE_PATH.read_bytes()))
        self.assertEqual(evidence["route_test_source_sha256"], _sha256(ROUTE_TEST_PATH.read_bytes()))
        self.assertEqual(task_profile["input_types"], card["accepted_input_types"])
        self.assertEqual(task_profile["required_outputs"], card["output_types"])
        self.assertEqual(task_profile["allowed_execution_modes"], ["READ_ONLY_RUN"])

        expected = {
            "default_off": ([], "INCOMPLETE", [], "EXPERIMENTAL_NOT_EXPLICITLY_INCLUDED"),
            "explicit_tool_allowlist": ([TOOL_ID], "COMPLETE", [TOOL_ID], None),
            "unrelated_input": ([TOOL_ID], "INCOMPLETE", [], "NO_INPUT_TYPE_MATCH"),
        }
        recorded = {row["scenario"]: row for row in evidence["route_trials"]}
        self.assertEqual(set(recorded), set(expected))
        for scenario, (allowlist, decision, selected_ids, rejection_reason) in expected.items():
            profile = dict(task_profile)
            if scenario == "unrelated_input":
                profile["input_types"] = ["Unrelated prose document"]
            plan = planner.plan_tool_route(profile, include_experimental_tool_ids=allowlist)
            row = recorded[scenario]
            self.assertEqual(plan["decision"], decision, scenario)
            self.assertEqual([tool["tool_id"] for tool in plan["selected_tools"]], selected_ids, scenario)
            self.assertEqual(row["decision"], decision, scenario)
            self.assertEqual(row["selected_tool_ids"], selected_ids, scenario)
            self.assertEqual(row["rejection_reason"], rejection_reason, scenario)
            self.assertEqual(row["plan_sha256"], _canonical_json_sha256(plan), scenario)
            self.assertEqual(
                plan["source_refs"]["experimental_candidate_catalog_git_blob_sha1"],
                evidence["candidate_catalog_git_blob_sha1"],
                scenario,
            )
            self.assertEqual(plan["allowed_network_hosts"], [], scenario)
            self.assertFalse(plan["execution_authorized"], scenario)
            self.assertFalse(row["execution_authorized"], scenario)
            self.assertFalse(row["candidate_invoked"], scenario)

        self.assertEqual(evidence["safety_boundary"]["tool_invocations_by_planner"], 0)
        self.assertEqual(evidence["safety_boundary"]["network_calls_by_planner"], 0)
        self.assertFalse(evidence["safety_boundary"]["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
