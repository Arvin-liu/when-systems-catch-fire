from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as operation_planner  # noqa: E402


TOOL_ID = "maintenance.audit_execution_state_lineage"
ROUTE_HEAD = "5516c269e82bb4c326f895cb2016a95086a13d92"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-execution-state-lineage-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-execution-state-lineage-route-experiment-r0.json"


class ExecutionStateLineageRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.candidates = operation_planner.load_json(operation_planner.EXPERIMENTAL_TOOL_CARDS_PATH)["candidates"]
        self.card = next(row for row in self.candidates if row["tool_id"] == TOOL_ID)

    def run_route(self, profile: dict, allowlist: list[str]) -> tuple[subprocess.CompletedProcess[str], dict]:
        command = [
            sys.executable,
            "-B",
            str(IGNITION_ROOT / "tools/operations/plan_ignition_operation_run.py"),
            "--route-request",
        ]
        for tool_id in allowlist:
            command.extend(["--allow-experimental", tool_id])
        process = subprocess.run(
            command,
            input=json.dumps(profile, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
        )
        return process, json.loads(process.stdout)

    def test_routes_require_explicit_opt_in_and_select_only_sufficient_candidate(self) -> None:
        bindings = self.evidence["bindings"]
        all_ids = sorted(row["tool_id"] for row in self.candidates)
        scenarios = [
            ("default_off", self.profile, [], 2),
            ("explicit_tool_only", self.profile, [TOOL_ID], 0),
            ("broad_explicit_allowlist", self.profile, all_ids, 0),
            (
                "unrelated_input_even_when_allowed",
                {**self.profile, "input_types": ["Unrelated prose document"]},
                [TOOL_ID],
                2,
            ),
        ]
        self.assertEqual(self.card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertFalse(self.card["router_selectable_by_default"])
        self.assertEqual(self.profile["current_ref"], self.evidence["bindings"]["current_ref_echoed_by_planner"])

        for scenario_id, profile, allowlist, expected_exit in scenarios:
            with self.subTest(scenario=scenario_id):
                process, plan = self.run_route(profile, allowlist)
                recorded = self.evidence["route_trials"][scenario_id]
                self.assertEqual(process.returncode, expected_exit)
                self.assertEqual(process.returncode, recorded["cli_exit_code"])
                self.assertEqual(plan["decision"], recorded["decision"])
                self.assertEqual([row["tool_id"] for row in plan["selected_tools"]], recorded["selected_tool_ids"])
                self.assertEqual(
                    [row["reason"] for row in plan["rejected_candidates"] if row["tool_id"] == TOOL_ID],
                    recorded["rejected_target_reasons"],
                )
                self.assertEqual(plan["required_outputs"], recorded["required_outputs"])
                self.assertEqual(plan["unmet_outputs"], recorded["unmet_outputs"])
                self.assertEqual(plan["allowed_network_hosts"], [])
                self.assertEqual(plan["current_ref_binding"], "CALLER_SUPPLIED_NOT_RESOLVED_BY_THIS_PLANNER")
                self.assertFalse(plan["execution_authorized"])
                self.assertFalse(recorded["execution_authorized"])
                self.assertEqual(plan["source_refs"]["current_registry_git_blob_sha1"], bindings["current_operation_registry_git_blob_sha1"])

    def test_route_evidence_binds_the_exact_pre_evidence_candidate_state(self) -> None:
        bindings = self.evidence["bindings"]
        self.assertEqual(bindings["task_branch_head_sha"], ROUTE_HEAD)
        self.assertEqual(bindings["candidate_count"], 10)
        self.assertEqual(bindings["route_profile_path"], str(PROFILE_PATH.relative_to(REPO_ROOT)))
        self.assertEqual(hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(), bindings["route_profile_sha256"])
        self.assertEqual(self.evidence["effect_observation"]["candidate_tool_invocations"], 0)
        self.assertEqual(self.evidence["effect_observation"]["network_requests"], 0)
        self.assertFalse(self.evidence["effect_observation"]["execution_authorized"])

        self.assertEqual(
            operation_planner.git_blob_sha1((REPO_ROOT / bindings["planner_path"]).read_bytes()),
            bindings["planner_git_blob_sha1"],
        )
        tool_source = (REPO_ROOT / bindings["tool_source_path"]).read_bytes()
        self.assertEqual(operation_planner.git_blob_sha1(tool_source), bindings["tool_source_git_blob_sha1"])
        self.assertEqual(hashlib.sha256(tool_source).hexdigest(), bindings["tool_source_sha256"])

        baseline_catalog = operation_planner.load_json(operation_planner.EXPERIMENTAL_TOOL_CARDS_PATH)
        baseline_card = next(row for row in baseline_catalog["candidates"] if row["tool_id"] == TOOL_ID)
        route_artifact_paths = {
            "ignition/data/operations/toolbox-execution-state-lineage-route-profile-r0.json",
            "ignition/data/operations/toolbox-execution-state-lineage-route-experiment-r0.json",
            "ignition/tests/test_toolbox_execution_state_lineage_routing.py",
        }
        baseline_card["source_refs"] = [
            row for row in baseline_card["source_refs"] if row["path"] not in route_artifact_paths
        ]
        baseline_card["validation"]["focused_checks"] = [
            path for path in baseline_card["validation"]["focused_checks"]
            if path != "ignition/tests/test_toolbox_execution_state_lineage_routing.py"
        ]
        baseline_catalog_bytes = (json.dumps(baseline_catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.assertEqual(
            operation_planner.git_blob_sha1(baseline_catalog_bytes),
            bindings["candidate_catalog_git_blob_sha1"],
        )
        self.assertEqual(len(baseline_catalog["candidates"]), bindings["candidate_count"])



if __name__ == "__main__":
    unittest.main()
