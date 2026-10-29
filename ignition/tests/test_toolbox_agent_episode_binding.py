from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-agent-episode-binding/valid-plan-r0.json"
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_agent_episode_binding.py"
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_agent_episode_binding as tool  # noqa: E402


def valid_plan() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def issue_codes(result: dict[str, Any]) -> set[str]:
    return {item["code"] for item in result["findings"]}


class AgentEpisodeBindingTests(unittest.TestCase):
    def test_valid_declarations_are_consistent_but_not_authorized_or_enforced(self) -> None:
        result = tool.validate_plan(valid_plan())

        self.assertEqual(result["status"], "BINDING_PLAN_DECLARATIONS_CONSISTENT")
        self.assertEqual(result["findings"], [])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["runtime_enforcement_status"], "NOT_EVALUATED")
        self.assertEqual(result["checks"]["aggregation_policy_interpretation"], "NOT_EVALUATED")
        self.assertIn("HARD_STOP_POLICY_REF_NOT_RESOLVED", issue_codes({**result, "findings": result["warnings"]}))

    def test_role_permission_widening_is_rejected(self) -> None:
        plan = valid_plan()
        plan["roles"][0]["allowed_tool_ids"].append("admin.shell")

        result = tool.validate_plan(plan)

        self.assertEqual(result["checks"]["input_schema"], "PASS")
        self.assertIn("ROLE_WIDENS_DECLARED_PERMISSION_CEILING", issue_codes(result))

    def test_private_context_cannot_be_added_to_another_role(self) -> None:
        plan = valid_plan()
        plan["roles"][1]["context_ids"].append("ctx-writer-private")

        result = tool.validate_plan(plan)

        self.assertIn("ROLE_CONTEXT_NOT_AUTHORIZED", issue_codes(result))

    def test_informational_edge_cannot_change_future_inputs(self) -> None:
        plan = valid_plan()
        plan["feedback_edges"][0]["can_change_future_inputs"] = True

        result = tool.validate_plan(plan)

        self.assertIn("ROLE_CANNOT_CHANGE_FUTURE_INPUTS", issue_codes(result))
        self.assertIn("INFORMATION_EDGE_DECLARES_CONTROL_EFFECT", issue_codes(result))

    def test_hard_stop_requires_role_capability_and_typed_policy(self) -> None:
        plan = valid_plan()
        plan["roles"][2]["can_signal_hard_stop"] = False
        plan["feedback_edges"][1]["hard_stop_policy_ref"] = None

        result = tool.validate_plan(plan)

        self.assertIn("ROLE_CANNOT_SIGNAL_HARD_STOP", issue_codes(result))
        self.assertIn("HARD_STOP_EDGE_INCOMPLETE_OR_OVERBROAD", issue_codes(result))
        self.assertIn("STOP_EFFECT_HAS_NO_POLICY_REFERENCE", issue_codes(result))

    def test_dag_cycle_is_rejected(self) -> None:
        plan = valid_plan()
        plan["work_units"][0]["depends_on"] = ["record-revision"]

        result = tool.validate_plan(plan)

        self.assertIn("WORK_UNIT_DEPENDENCY_CYCLE", issue_codes(result))

    def test_unordered_writers_cannot_share_an_exclusive_domain(self) -> None:
        plan = valid_plan()
        parallel_writer = copy.deepcopy(plan["work_units"][2])
        parallel_writer["work_unit_id"] = "record-parallel-revision"
        parallel_writer["depends_on"] = ["prepare-draft"]
        plan["work_units"].append(parallel_writer)

        result = tool.validate_plan(plan)

        self.assertIn("UNORDERED_EXCLUSIVE_WRITERS", issue_codes(result))

    def test_write_binding_must_belong_to_the_work_unit_role(self) -> None:
        plan = valid_plan()
        plan["work_units"][2]["role_id"] = "auditor"

        result = tool.validate_plan(plan)

        self.assertIn("WORK_UNIT_USES_ANOTHER_ROLE_WRITE_BINDING", issue_codes(result))
        self.assertIn("WORK_UNIT_OUTPUT_OUTSIDE_ROLE_DECLARATION", issue_codes(result))

    def test_unknown_dependency_is_rejected(self) -> None:
        plan = valid_plan()
        plan["work_units"][1]["depends_on"] = ["missing-unit"]

        result = tool.validate_plan(plan)

        self.assertIn("WORK_UNIT_DEPENDENCY_UNKNOWN", issue_codes(result))

    def test_invalid_digest_fails_schema_before_semantic_checks(self) -> None:
        plan = valid_plan()
        plan["contexts"][0]["sha256"] = "not-a-digest"

        result = tool.validate_plan(plan)

        self.assertEqual(result["checks"]["input_schema"], "FAIL")
        self.assertEqual(result["checks"]["cross_reference_consistency"], "NOT_RUN")
        self.assertIn("INPUT_SCHEMA_INVALID", issue_codes(result))

    def test_c1_schema_only_baseline_accepts_shape_valid_conflicts_rejected_by_tool(self) -> None:
        cases: dict[str, dict[str, Any]] = {}

        duplicate_role = valid_plan()
        duplicate_role["roles"].append(copy.deepcopy(duplicate_role["roles"][0]))
        cases["DUPLICATE_ROLE_ID"] = duplicate_role

        permission_widening = valid_plan()
        permission_widening["roles"][0]["allowed_tool_ids"].append("admin.shell")
        cases["ROLE_PERMISSION_WIDENING"] = permission_widening

        private_context_leak = valid_plan()
        private_context_leak["roles"][1]["context_ids"].append("ctx-writer-private")
        cases["PRIVATE_CONTEXT_CROSS_ROLE"] = private_context_leak

        undeclared_control = valid_plan()
        undeclared_control["feedback_edges"][0]["can_change_future_inputs"] = True
        cases["INFORMATION_EDGE_CONTROL_EFFECT"] = undeclared_control

        unauthorized_stop = valid_plan()
        unauthorized_stop["roles"][2]["can_signal_hard_stop"] = False
        cases["UNAUTHORIZED_HARD_STOP"] = unauthorized_stop

        dependency_cycle = valid_plan()
        dependency_cycle["work_units"][0]["depends_on"] = ["record-revision"]
        cases["DEPENDENCY_CYCLE"] = dependency_cycle

        unordered_writers = valid_plan()
        parallel_writer = copy.deepcopy(unordered_writers["work_units"][2])
        parallel_writer["work_unit_id"] = "record-parallel-revision"
        parallel_writer["depends_on"] = ["prepare-draft"]
        unordered_writers["work_units"].append(parallel_writer)
        cases["UNORDERED_EXCLUSIVE_WRITERS"] = unordered_writers

        for case_id, plan in cases.items():
            with self.subTest(case_id=case_id):
                self.assertEqual(tool._schema_findings(plan), [])
                result = tool.validate_plan(plan)
                self.assertEqual(result["status"], "BINDING_PLAN_INVALID")
                self.assertTrue(result["findings"])
                self.assertFalse(result["execution_authorized"])

    def test_cli_emits_json_for_valid_plan_without_authorizing_execution(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=FIXTURE.read_bytes(),
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        result = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(result["status"], "BINDING_PLAN_DECLARATIONS_CONSISTENT")
        self.assertFalse(result["execution_authorized"])

    def test_duplicate_json_keys_fail_closed(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=b'{"episode_id":"a","episode_id":"b"}',
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        result = json.loads(completed.stdout.decode("utf-8"))
        self.assertIn("DUPLICATE_JSON_KEY", issue_codes(result))
        self.assertFalse(result["execution_authorized"])

    def test_oversized_stdin_is_rejected(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=b" " * (tool.MAX_INPUT_BYTES + 1),
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        result = json.loads(completed.stdout.decode("utf-8"))
        self.assertIn("INPUT_UNAVAILABLE_OR_INVALID", issue_codes(result))


if __name__ == "__main__":
    unittest.main()
