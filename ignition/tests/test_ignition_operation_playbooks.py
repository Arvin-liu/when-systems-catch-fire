from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import validate_ignition_operation_playbooks as validator  # noqa: E402


class IgnitionOperationPlaybooksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.playbooks = validator.load_json(validator.PLAYBOOKS_PATH)
        self.registry = validator.load_json(validator.REGISTRY_PATH)

    def test_current_playbooks_and_generated_view_pass(self) -> None:
        self.assertEqual(validator.validate(copy.deepcopy(self.playbooks)), [])
        self.assertEqual(len(self.playbooks["playbooks"]), 15)
        self.assertEqual(len(self.playbooks["excluded_status_only"]), 4)
        self.assertEqual(len(self.playbooks["category_audit"]), 11)

    def test_callable_registry_coverage_is_exact(self) -> None:
        operations = {row["operation_id"]: row for row in self.registry["operations"]}
        expected = sorted(
            operation_id
            for operation_id, row in operations.items()
            if row["current_status"] in validator.CALLABLE_STATUSES
            and row["ai_callability"] in validator.CALLABLE_AI
        )
        actual = [row["operation_id"] for row in self.playbooks["playbooks"]]
        self.assertEqual(actual, expected)
        self.assertNotIn("external.live_invocation", actual)
        self.assertNotIn("executor.reference_conformance", actual)

    def test_missing_callable_playbook_fails_closed(self) -> None:
        candidate = copy.deepcopy(self.playbooks)
        candidate["playbooks"] = candidate["playbooks"][1:]
        errors = validator.validate(candidate, check_human_view=False)
        self.assertTrue(any("callable playbook coverage mismatch" in error for error in errors))

    def test_status_only_operation_cannot_receive_playbook(self) -> None:
        candidate = copy.deepcopy(self.playbooks)
        extra = copy.deepcopy(candidate["playbooks"][0])
        extra["operation_id"] = "external.live_invocation"
        candidate["playbooks"].append(extra)
        candidate["playbooks"].sort(key=lambda row: row["operation_id"])
        errors = validator.validate(candidate, check_human_view=False)
        self.assertTrue(any("callable playbook coverage mismatch" in error for error in errors))
        self.assertTrue(any("non-callable operation" in error for error in errors))

    def test_category_cannot_reference_unknown_operation(self) -> None:
        candidate = copy.deepcopy(self.playbooks)
        candidate["category_audit"][0]["operation_ids"].append("knowledge.imagined_retrieval")
        errors = validator.validate(candidate, check_human_view=False)
        self.assertTrue(any("unknown operation IDs" in error for error in errors))

    def test_covered_current_requires_current_operation(self) -> None:
        candidate = copy.deepcopy(self.playbooks)
        row = next(item for item in candidate["category_audit"] if item["category_id"] == "translation_language_thought")
        row["coverage_status"] = "COVERED_CURRENT"
        errors = validator.validate(candidate, check_human_view=False)
        self.assertTrue(any("COVERED_CURRENT requires a CURRENT operation" in error for error in errors))

    def test_human_view_projects_required_playbook_fields(self) -> None:
        rendered = validator.render_markdown(self.playbooks, self.registry)
        self.assertEqual(rendered, validator.HUMAN_VIEW_PATH.read_text(encoding="utf-8"))
        self.assertEqual(rendered.count("### `"), 15)
        for heading in (
            "用户常见意图：",
            "输入（registry-derived）：",
            "最小 Current read set：",
            "执行步骤：",
            "必须检查的 authority：",
            "允许的最大输出：",
            "Stop conditions：",
            "不得做什么：",
        ):
            self.assertEqual(rendered.count(heading), 15)
        self.assertEqual(rendered.count("ignition/data/operations/ignition-run-output-contract-r1.json"), 15)

    def test_authored_playbooks_do_not_duplicate_registry_fields(self) -> None:
        allowed = {
            "operation_id",
            "common_natural_language_intents",
            "execution_steps",
            "stop_conditions",
            "prohibitions",
        }
        self.assertTrue(all(set(row) == allowed for row in self.playbooks["playbooks"]))


if __name__ == "__main__":
    unittest.main()
