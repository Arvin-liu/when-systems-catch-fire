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

TOOL_ID = "collaboration.build_portable_research_episode"
FEATURE_COMMIT = "0b261e82712a705c27cd00b74374a2f97c25240d"
PROFILE_PATH = IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-builder-route-profile-r0.json"
EVIDENCE_PATH = IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-builder-route-evidence-r0.json"
EXECUTION_PATH = IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-builder-route-execution-evidence-r0.json"
INPUT_PATH = IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-builder-real-task-input-r0.json"
OUTPUT_PATH = IGNITION_ROOT / "data/operations/toolbox-portable-research-episode-builder-real-task-output-r0.json"
SOURCE_PATH = IGNITION_ROOT / "tools/toolbox_build_portable_research_episode.py"
ROUTE_TEST_PATH = IGNITION_ROOT / "tests/test_toolbox_portable_research_episode_builder_routing.py"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _historical_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{FEATURE_COMMIT}:{path}"], cwd=REPO_ROOT)


class PortableResearchEpisodeBuilderRoutingTests(unittest.TestCase):
    def test_exact_head_routing_stays_default_off_and_local_replay_matches(self) -> None:
        profile_bytes = PROFILE_PATH.read_bytes()
        profile = json.loads(profile_bytes)
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        execution = json.loads(EXECUTION_PATH.read_text(encoding="utf-8"))
        catalog_bytes = planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes()
        catalog = json.loads(catalog_bytes)

        current_ref = f"refs/heads/codex/toolbox-growth-20261025@{FEATURE_COMMIT}"
        self.assertEqual(evidence["candidate_head"], FEATURE_COMMIT)
        self.assertEqual(profile["current_ref"], current_ref)
        self.assertEqual(evidence["current_ref"], current_ref)
        self.assertEqual(execution["current_ref"], current_ref)
        self.assertEqual(_sha256(profile_bytes), evidence["route_profile_sha256"])
        self.assertEqual(planner.git_blob_sha1(catalog_bytes), evidence["candidate_catalog_git_blob_sha1"])
        self.assertEqual(len(catalog["candidates"]), evidence["candidate_count"])
        self.assertEqual(_sha256(ROUTE_TEST_PATH.read_bytes()), evidence["route_test_source_sha256"])

        historical_catalog = json.loads(_historical_bytes("ignition/data/operations/toolbox-candidate-cards-r0.json"))
        historical_tool = _historical_bytes("ignition/tools/toolbox_build_portable_research_episode.py")
        historical_input = _historical_bytes("ignition/data/operations/toolbox-portable-research-episode-builder-real-task-input-r0.json")
        historical_output = _historical_bytes("ignition/data/operations/toolbox-portable-research-episode-builder-real-task-output-r0.json")
        self.assertIn(TOOL_ID, [row["tool_id"] for row in historical_catalog["candidates"]])
        self.assertEqual(len(historical_catalog["candidates"]), evidence["feature_commit_candidate_count"])
        self.assertEqual(_sha256(historical_tool), evidence["tool_source_sha256"])
        self.assertEqual(_sha256(historical_input), evidence["input_sha256"])
        self.assertEqual(_sha256(historical_output), evidence["expected_output_sha256"])
        self.assertEqual(_sha256(historical_tool), _sha256(SOURCE_PATH.read_bytes()))

        all_ids = sorted(row["tool_id"] for row in catalog["candidates"])
        allowlists = {
            "default_off": [],
            "tool_only": [TOOL_ID],
            "broad_allowlist": all_ids,
            "other_candidates_only": [tool_id for tool_id in all_ids if tool_id != TOOL_ID],
            "unrelated_input": [TOOL_ID],
        }
        expected = {
            "default_off": ("INCOMPLETE", []),
            "tool_only": ("COMPLETE", [TOOL_ID]),
            "broad_allowlist": ("COMPLETE", [TOOL_ID]),
            "other_candidates_only": ("INCOMPLETE", []),
            "unrelated_input": ("INCOMPLETE", []),
        }
        recorded = {row["scenario"]: row for row in evidence["route_trials"]}
        self.assertEqual(set(recorded), set(expected))
        for scenario, allowlist in allowlists.items():
            task_profile = dict(profile)
            if scenario == "unrelated_input":
                task_profile["input_types"] = ["Unrelated prose document"]
            plan = planner.plan_tool_route(task_profile, include_experimental_tool_ids=allowlist)
            decision, selected_ids = expected[scenario]
            row = recorded[scenario]
            self.assertEqual(plan["decision"], decision, scenario)
            self.assertEqual([tool["tool_id"] for tool in plan["selected_tools"]], selected_ids, scenario)
            self.assertEqual(row["decision"], decision, scenario)
            self.assertEqual(row["selected_tool_ids"], selected_ids, scenario)
            self.assertEqual(row["plan_sha256"], _sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")), scenario)
            self.assertEqual(plan["allowed_network_hosts"], [], scenario)
            self.assertFalse(plan["execution_authorized"], scenario)
            self.assertFalse(row["execution_authorized"], scenario)
        self.assertEqual(evidence["safety_boundary"]["tool_invocations_by_planner"], 0)
        self.assertFalse(evidence["safety_boundary"]["execution_authorized"])

        self.assertEqual(execution["tool_id"], TOOL_ID)
        self.assertEqual(execution["tool_version"], "0.1.0")
        self.assertEqual(execution["route_profile_sha256"], _sha256(profile_bytes))
        self.assertEqual(execution["route_evidence_sha256"], _sha256(EVIDENCE_PATH.read_bytes()))
        self.assertEqual(execution["expected_output_sha256"], _sha256(historical_output))
        self.assertEqual(execution["observed_stdout_matches_saved_output"], True)
        self.assertEqual(execution["returncode"], 0)
        self.assertTrue(execution["stderr_empty"])
        self.assertFalse(execution["execution_authorized_by_route_planner"])
        self.assertFalse(execution["network_permission"])
        self.assertFalse(execution["tool_file_writes"])

        process = subprocess.run(
            [sys.executable, "-B", str(SOURCE_PATH), "--stdin", "--workspace-root", "ignition"],
            input=historical_input,
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(process.returncode, execution["returncode"])
        self.assertEqual(process.stdout, historical_output)
        self.assertEqual(_sha256(process.stdout), execution["observed_stdout_sha256"])
        self.assertEqual(process.stderr, b"")


if __name__ == "__main__":
    unittest.main()
