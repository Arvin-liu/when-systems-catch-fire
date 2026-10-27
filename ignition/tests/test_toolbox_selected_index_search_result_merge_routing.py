from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402


TOOL_ID = "research.merge_selected_index_search_results"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-route-evidence-r0.json"
ROUTED_PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-routed-real-task-profile-r1.json"
ROUTED_EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-route-execution-evidence-r1.json"
ROUTED_INPUT_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-input-r0.json"
ROUTED_EXPECTED_OUTPUT_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-output-r0.json"
R2_PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-route-profile-r2.json"
R2_ROUTE_EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-route-evidence-r1.json"
R2_ROUTED_PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-routed-real-task-profile-r2.json"
R2_EXECUTION_EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-selected-index-search-result-merge-route-execution-evidence-r2.json"


class SelectedIndexSearchResultMergeRoutingTests(unittest.TestCase):
    def test_default_off_and_explicit_allowlist_only_proposes_offline_tool(self) -> None:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        default = planner.plan_tool_route(profile)
        explicit = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(explicit["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in explicit["selected_tools"]], [TOOL_ID])
        self.assertFalse(explicit["execution_authorized"])
        self.assertFalse(explicit["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(explicit["selected_tools"][0]["permissions"]["network_hosts"], [])

        trials = {row["scenario"]: row for row in evidence["route_trials"]}
        self.assertEqual(trials["default_off"]["decision"], default["decision"])
        self.assertEqual(trials["explicit_allowlist"]["decision"], explicit["decision"])
        self.assertEqual(trials["explicit_allowlist"]["selected_tool_ids"], [TOOL_ID])
        self.assertRegex(evidence["candidate_catalog_git_blob_sha1"], r"^[a-f0-9]{40}$")
        self.assertTrue(evidence["catalog_replay"]["all_expected_decisions_reproduced"])
        self.assertFalse(trials["explicit_allowlist"]["candidate_invoked"])
        self.assertFalse(trials["explicit_allowlist"]["execution_authorized"])

    def test_exact_head_route_experiment_replays_and_invokes_only_the_selected_offline_tool(self) -> None:
        profile_bytes = ROUTED_PROFILE_PATH.read_bytes()
        profile = json.loads(profile_bytes)
        evidence = json.loads(ROUTED_EVIDENCE_PATH.read_text(encoding="utf-8"))
        candidates = planner.load_json(planner.EXPERIMENTAL_TOOL_CARDS_PATH)["candidates"]
        all_ids = sorted(row["tool_id"] for row in candidates)
        candidate_head = evidence["candidate_head"]

        def historical_bytes(path: str) -> bytes:
            return subprocess.check_output(
                ["git", "show", f"{candidate_head}:{path}"],
                cwd=REPO_ROOT,
            )

        self.assertEqual(hashlib.sha256(profile_bytes).hexdigest(), evidence["bindings"]["task_profile_sha256"])
        self.assertEqual(profile["current_ref"], f"refs/heads/codex/toolbox-growth-20261025@{candidate_head}")
        historical_catalog = historical_bytes("ignition/data/operations/toolbox-candidate-cards-r0.json")
        historical_planner = historical_bytes("ignition/tools/operations/plan_ignition_operation_run.py")
        historical_tool = historical_bytes("ignition/tools/toolbox_merge_selected_index_search_results.py")
        historical_input = historical_bytes("ignition/data/operations/toolbox-selected-index-search-result-merge-input-r0.json")
        historical_output = historical_bytes("ignition/data/operations/toolbox-selected-index-search-result-merge-output-r0.json")
        self.assertEqual(planner.git_blob_sha1(historical_catalog), evidence["bindings"]["catalog_git_blob_sha1_at_route_time"])
        self.assertEqual(len(json.loads(historical_catalog)["candidates"]), evidence["bindings"]["candidate_count"])
        self.assertEqual(
            hashlib.sha256(historical_planner).hexdigest(),
            evidence["bindings"]["planner_source_sha256"],
        )
        self.assertEqual(hashlib.sha256(historical_tool).hexdigest(), evidence["bindings"]["tool_source_sha256"])
        self.assertEqual(hashlib.sha256(historical_input).hexdigest(), evidence["bindings"]["input_sha256"])
        self.assertEqual(hashlib.sha256(historical_output).hexdigest(), evidence["bindings"]["expected_output_file_sha256"])

        all_scenarios = {row["scenario"]: row for row in evidence["route_trials"]}
        allowlists = {
            "default_off": [],
            "explicit_tool_only": [TOOL_ID],
            "broad_explicit_allowlist": all_ids,
            "other_candidates_only": [tool_id for tool_id in all_ids if tool_id != TOOL_ID],
            "unrelated_input_even_when_allowed": [TOOL_ID],
        }
        for scenario, allowlist in allowlists.items():
            task_profile = dict(profile)
            if scenario == "unrelated_input_even_when_allowed":
                task_profile["input_types"] = ["Unrelated prose document"]
            plan = planner.plan_tool_route(task_profile, include_experimental_tool_ids=allowlist)
            recorded = all_scenarios[scenario]
            expected_decision = "COMPLETE" if scenario in {"explicit_tool_only", "broad_explicit_allowlist"} else "INCOMPLETE"
            expected_ids = [TOOL_ID] if expected_decision == "COMPLETE" else []
            self.assertEqual(recorded["decision"], expected_decision, scenario)
            self.assertEqual(recorded["selected_tool_ids"], expected_ids, scenario)
            self.assertEqual(plan["decision"], expected_decision, scenario)
            self.assertEqual([row["tool_id"] for row in plan["selected_tools"]], expected_ids, scenario)
            self.assertEqual(plan["allowed_network_hosts"], [], scenario)
            self.assertFalse(plan["execution_authorized"], scenario)

        selected_plan = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])
        self.assertEqual(selected_plan["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in selected_plan["selected_tools"]], [TOOL_ID])
        self.assertFalse(evidence["selected_execution"]["execution_authorized_by_route_planner"])

        with tempfile.TemporaryDirectory(prefix="ignition-merge-r0-") as temporary_dir:
            historical_source_path = Path(temporary_dir) / "toolbox_merge_selected_index_search_results.py"
            historical_source_path.write_bytes(historical_tool)
            process = subprocess.run(
                [sys.executable, "-B", str(historical_source_path), "--stdin"],
                input=historical_input,
                capture_output=True,
                cwd=REPO_ROOT,
                check=False,
            )
        self.assertEqual(process.returncode, evidence["selected_execution"]["exit_code"])
        self.assertEqual(hashlib.sha256(process.stdout).hexdigest(), evidence["selected_execution"]["output_sha256"])
        self.assertEqual(
            json.loads(process.stdout),
            json.loads(ROUTED_EXPECTED_OUTPUT_PATH.read_text(encoding="utf-8")),
        )
        self.assertEqual(process.stderr, b"")
        self.assertEqual(evidence["selected_execution"]["cost_observation"]["network_calls"], 0)
        self.assertEqual(evidence["selected_execution"]["cost_observation"]["filesystem_writes_by_tool"], 0)

    def test_r2_route_and_real_task_replay_bind_exact_feature_commit(self) -> None:
        candidate_head = "0420927e5eb7fea1b6ae952d604917e50c2d3cef"
        current_ref = f"refs/heads/codex/toolbox-growth-20261025@{candidate_head}"
        profile_bytes = R2_PROFILE_PATH.read_bytes()
        profile = json.loads(profile_bytes)
        route_evidence = json.loads(R2_ROUTE_EVIDENCE_PATH.read_text(encoding="utf-8"))
        routed_profile = json.loads(R2_ROUTED_PROFILE_PATH.read_text(encoding="utf-8"))
        execution = json.loads(R2_EXECUTION_EVIDENCE_PATH.read_text(encoding="utf-8"))

        def historical_bytes(path: str) -> bytes:
            return subprocess.check_output(["git", "show", f"{candidate_head}:{path}"], cwd=REPO_ROOT)

        self.assertEqual(profile["current_ref"], current_ref)
        self.assertEqual(route_evidence["current_ref"], current_ref)
        self.assertEqual(execution["current_ref"], current_ref)
        self.assertEqual(routed_profile["current_ref"], current_ref)
        self.assertEqual(hashlib.sha256(profile_bytes).hexdigest(), route_evidence["route_profile_sha256"])
        self.assertEqual(route_evidence["route_profile_sha256"], routed_profile["route_profile_sha256"])

        historical_catalog = historical_bytes("ignition/data/operations/toolbox-candidate-cards-r0.json")
        historical_planner = historical_bytes("ignition/tools/operations/plan_ignition_operation_run.py")
        historical_source = historical_bytes("ignition/tools/toolbox_merge_selected_index_search_results.py")
        historical_input = historical_bytes("ignition/data/operations/toolbox-selected-index-search-result-merge-input-r0.json")
        historical_output = historical_bytes("ignition/data/operations/toolbox-selected-index-search-result-merge-output-r1.json")
        self.assertEqual(planner.git_blob_sha1(historical_catalog), route_evidence["candidate_catalog_git_blob_sha1"])
        self.assertEqual(hashlib.sha256(historical_planner).hexdigest(), route_evidence["planner_source_sha256"])
        self.assertEqual(hashlib.sha256(historical_source).hexdigest(), route_evidence["tool_source_sha256"])
        self.assertEqual(hashlib.sha256(historical_input).hexdigest(), route_evidence["input_sha256"])
        self.assertEqual(hashlib.sha256(historical_output).hexdigest(), route_evidence["expected_output_sha256"])
        self.assertEqual(route_evidence["candidate_count"], 71)
        self.assertEqual(hashlib.sha256(historical_source).hexdigest(), execution["source_sha256"])
        self.assertEqual(hashlib.sha256(historical_input).hexdigest(), execution["input_sha256"])
        self.assertEqual(hashlib.sha256(historical_output).hexdigest(), execution["expected_output_sha256"])
        self.assertEqual(hashlib.sha256(historical_output).hexdigest(), execution["observed_stdout_sha256"])

        scenarios = {row["scenario"]: row for row in route_evidence["scenarios"]}
        expected = {
            "default_off": ("INCOMPLETE", []),
            "tool_only": ("COMPLETE", [TOOL_ID]),
            "broad_allowlist": ("COMPLETE", [TOOL_ID]),
            "other_candidates_only": ("INCOMPLETE", []),
            "unrelated_input": ("INCOMPLETE", []),
        }
        self.assertEqual(set(scenarios), set(expected))
        for name, (decision, selected_ids) in expected.items():
            row = scenarios[name]
            plan = row["plan"]
            self.assertEqual(plan["decision"], decision, name)
            self.assertEqual([item["tool_id"] for item in plan["selected_tools"]], selected_ids, name)
            self.assertFalse(plan["execution_authorized"], name)
            self.assertEqual(plan["allowed_network_hosts"], [], name)
            canonical = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.assertEqual(hashlib.sha256(canonical).hexdigest(), row["plan_sha256"], name)
        self.assertFalse(route_evidence["safety_boundary"]["execution_authorized"])
        self.assertEqual(route_evidence["safety_boundary"]["tool_invocations_by_planner"], 0)
        self.assertEqual(route_evidence["route_profile_sha256"], hashlib.sha256(profile_bytes).hexdigest())
        self.assertEqual(routed_profile["route_evidence_sha256"], hashlib.sha256(R2_ROUTE_EVIDENCE_PATH.read_bytes()).hexdigest())

        self.assertEqual(routed_profile["input_sha256"], execution["input_sha256"])
        self.assertEqual(routed_profile["expected_output_sha256"], execution["expected_output_sha256"])
        self.assertEqual(execution["returncode"], 0)
        self.assertTrue(execution["observed_stdout_matches_saved_output"])
        self.assertEqual(execution["network_calls"], 0)
        self.assertEqual(execution["tool_file_writes"], 0)
        self.assertFalse(execution["execution_authorized_by_route_planner"])
        self.assertEqual(execution["route_profile_sha256"], route_evidence["route_profile_sha256"])
        self.assertEqual(execution["route_evidence_sha256"], hashlib.sha256(R2_ROUTE_EVIDENCE_PATH.read_bytes()).hexdigest())
        self.assertEqual(execution["routed_profile_sha256"], hashlib.sha256(R2_ROUTED_PROFILE_PATH.read_bytes()).hexdigest())

        with tempfile.TemporaryDirectory(prefix="ignition-merge-r2-") as temporary_dir:
            historical_source_path = Path(temporary_dir) / "toolbox_merge_selected_index_search_results.py"
            historical_source_path.write_bytes(historical_source)
            process = subprocess.run(
                [sys.executable, "-B", str(historical_source_path), "--stdin"],
                input=historical_input,
                capture_output=True,
                cwd=REPO_ROOT,
                check=False,
            )
        self.assertEqual(process.returncode, execution["returncode"])
        self.assertEqual(process.stdout, historical_output)
        self.assertEqual(hashlib.sha256(process.stdout).hexdigest(), execution["observed_stdout_sha256"])
        self.assertEqual(process.stderr, b"")


if __name__ == "__main__":
    unittest.main()
