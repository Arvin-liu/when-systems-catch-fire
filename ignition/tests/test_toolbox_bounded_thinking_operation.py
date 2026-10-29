from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tools.toolbox_bounded_thinking_operation import (
    MAX_STDIN_BYTES,
    DecisionError,
    select_bounded_thinking_operation,
)


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-bounded-thinking-operation/verify-needed-r0.json"
FRESHNESS_TRANSFER_FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-bounded-thinking-operation/freshness-verification-transfer-r0.json"
TOOL = IGNITION_ROOT / "tools/toolbox_bounded_thinking_operation.py"


def example() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def assessment(operation: str, *, value: str = "POSITIVE", cost: int = 1, capabilities=None) -> dict:
    return {
        "operation": operation,
        "expected_state_delta": f"Resolve the declared {operation} gap.",
        "expected_value_status": value,
        "expected_value_band": "MEDIUM" if value == "POSITIVE" else None,
        "expected_cost_band": "LOW",
        "estimated_cost_units": cost,
        "reason_refs": ["obligation:current"],
        "required_capabilities": capabilities or [],
        "return_condition": "Re-evaluate after recording an observable outcome.",
    }


class BoundedThinkingOperationTests(unittest.TestCase):
    def test_required_verification_selects_one_operation_and_never_executes(self) -> None:
        result = select_bounded_thinking_operation(example())
        self.assertEqual(result["selected_operation"], "VERIFY")
        self.assertIsNone(result["terminal_disposition"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["permission_expanded"])
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["cost_basis"], "CALLER_DECLARED_ABSTRACT_UNITS_NOT_MEASURED")

    def test_freshness_read_reveals_verification_then_reselects(self) -> None:
        initial = json.loads(FRESHNESS_TRANSFER_FIXTURE.read_text(encoding="utf-8"))
        first = select_bounded_thinking_operation(initial)
        self.assertEqual(first["selected_operation"], "READ_MORE")
        self.assertFalse(first["execution_authorized"])

        observed = copy.deepcopy(initial)
        observed["state"]["state_ref"] = "state:F13:after-fresh-read"
        observed["state"]["freshness_gap"] = False
        observed["state"]["remaining_budget_units"] = 4
        observed["state"]["required_obligations"] = [
            {
                "obligation_ref": "fresh:f13:claim",
                "status": "RESOLVED",
                "required": True,
                "verification_required": False,
                "evidence_refs": ["evidence:f13:fresh"],
            },
            {
                "obligation_ref": "verify:f13:follow-up",
                "status": "OPEN",
                "required": True,
                "verification_required": True,
                "evidence_refs": ["evidence:f13:fresh"],
            },
        ]
        observed["state"]["uncertainty_refs"] = ["uncertainty:f13:follow-up"]
        observed["state"]["operation_history"].append(
            {
                "operation": "READ_MORE",
                "outcome": "STATE_CHANGED",
                "state_ref": "state:F13:initial",
                "failure_ref": None,
            }
        )
        second = select_bounded_thinking_operation(observed)
        self.assertEqual(second["selected_operation"], "VERIFY")
        self.assertEqual(second["state_ref"], "state:F13:after-fresh-read")
        self.assertFalse(second["execution_authorized"])

    def test_missing_authority_wins_over_capacity_escalation(self) -> None:
        data = example()
        data["state"]["authority_missing"] = True
        data["state"]["capability_missing"] = True
        data["available_operations"] = [
            "REQUEST_OWNER_DECISION",
            "CAPACITY_OR_EXECUTOR_ESCALATE",
            "VERIFY",
            "READ_MORE",
        ]
        data["candidate_assessments"] = [
            assessment("REQUEST_OWNER_DECISION"),
            assessment("CAPACITY_OR_EXECUTOR_ESCALATE"),
            assessment("VERIFY"),
            assessment("READ_MORE"),
        ]
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["selected_operation"], "REQUEST_OWNER_DECISION")
        self.assertIn("AUTHORITY_DEFICIT", result["reason_codes"])
        self.assertFalse(result["permission_expanded"])

    def test_missing_verifier_stops_at_verification_ceiling(self) -> None:
        data = example()
        data["available_operations"] = ["READ_MORE"]
        data["candidate_assessments"] = [assessment("READ_MORE")]
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["selected_operation"], "STOP")
        self.assertEqual(result["terminal_disposition"], "VERIFICATION_CEILING")

    def test_insufficient_declared_budget_stops_before_recommendation(self) -> None:
        data = example()
        data["state"]["remaining_budget_units"] = 0
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["selected_operation"], "STOP")
        self.assertEqual(result["terminal_disposition"], "BUDGET_EXHAUSTED")
        self.assertEqual(result["estimated_cost_units"], None)

    def test_nonpositive_or_unknown_value_does_not_recommend_more_thinking(self) -> None:
        for value in ("NON_POSITIVE", "UNKNOWN"):
            with self.subTest(value=value):
                data = example()
                data["candidate_assessments"][0] = assessment("VERIFY", value=value)
                result = select_bounded_thinking_operation(data)
                self.assertEqual(result["selected_operation"], "STOP")
                self.assertIn("EXPECTED_VALUE_NOT_POSITIVE", result["reason_codes"])

    def test_undeclared_capability_blocks_recommendation(self) -> None:
        data = example()
        data["candidate_assessments"][0]["required_capabilities"] = ["unavailable-verifier"]
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["selected_operation"], "STOP")
        self.assertEqual(result["terminal_disposition"], "CAPABILITY_BLOCKED")

    def test_unresolved_frame_without_reframer_is_explicitly_stopped(self) -> None:
        data = example()
        data["state"]["frame_unresolved"] = True
        data["available_operations"] = ["VERIFY", "READ_MORE"]
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["selected_operation"], "STOP")
        self.assertEqual(result["terminal_disposition"], "FRAME_UNRESOLVED")

    def test_first_failure_is_preserved_on_a_later_recommendation(self) -> None:
        data = example()
        data["state"]["failure_refs"] = ["failure:first", "failure:later"]
        data["state"]["first_failure_ref"] = "failure:first"
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["first_failure_ref"], "failure:first")
        self.assertIn("failure:first", result["reason_refs"])
        self.assertIn("FIRST_FAILURE_PRESERVED", result["reason_codes"])

    def test_repeating_failed_operation_on_same_state_stops(self) -> None:
        data = example()
        data["state"]["operation_history"] = [
            {
                "operation": "VERIFY",
                "outcome": "FAILED",
                "state_ref": "state:initial",
                "failure_ref": "failure:verify-timeout",
            }
        ]
        data["state"]["failure_refs"] = ["failure:verify-timeout"]
        data["state"]["first_failure_ref"] = "failure:verify-timeout"
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["selected_operation"], "STOP")
        self.assertIn("REPEATED_OPERATION_WITHOUT_STATE_CHANGE", result["reason_codes"])
        self.assertEqual(result["first_failure_ref"], "failure:verify-timeout")

    def test_sufficient_is_only_a_caller_declared_terminal_label(self) -> None:
        data = example()
        data["state"]["required_obligations"][0]["status"] = "RESOLVED"
        data["available_operations"] = []
        data["candidate_assessments"] = []
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["selected_operation"], "STOP")
        self.assertEqual(result["terminal_disposition"], "SUFFICIENT")
        self.assertEqual(result["claim_ceiling"], "CALLER_STATE_BASED_OPERATION_RECOMMENDATION_ONLY")
        self.assertFalse(result["execution_authorized"])

    def test_optional_open_obligation_is_not_silently_dropped(self) -> None:
        data = example()
        data["state"]["required_obligations"][0]["required"] = False
        data["state"]["required_obligations"][0]["verification_required"] = False
        result = select_bounded_thinking_operation(data)
        self.assertEqual(result["selected_operation"], "STOP")
        self.assertEqual(result["terminal_disposition"], "EXPLICIT_GAP")

    def test_wrong_first_failure_order_is_rejected(self) -> None:
        data = example()
        data["state"]["failure_refs"] = ["failure:first", "failure:later"]
        data["state"]["first_failure_ref"] = "failure:later"
        with self.assertRaisesRegex(DecisionError, "earliest failure"):
            select_bounded_thinking_operation(data)

    def test_candidate_assessments_must_be_unique_and_available(self) -> None:
        data = example()
        data["candidate_assessments"].append(copy.deepcopy(data["candidate_assessments"][0]))
        with self.assertRaisesRegex(DecisionError, "at most one"):
            select_bounded_thinking_operation(data)
        data = example()
        data["candidate_assessments"] = [assessment("DECOMPOSE")]
        with self.assertRaisesRegex(DecisionError, "subset of available_operations"):
            select_bounded_thinking_operation(data)

    def test_cli_rejects_duplicate_json_keys(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL), "--stdin"],
            input=b'{"schema_version":"wrong","schema_version":"wrong"}',
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn(b"duplicate JSON key", completed.stdout)

    def test_cli_rejects_oversized_stdin(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL), "--stdin"],
            input=b" " * (MAX_STDIN_BYTES + 1),
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn(b"exceeds", completed.stdout)


if __name__ == "__main__":
    unittest.main()
