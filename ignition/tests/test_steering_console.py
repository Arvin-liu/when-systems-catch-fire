from __future__ import annotations

import unittest

from agent_runtime.driver_console import DriverConsoleError, STEERING_DRIVER_CONSOLE_SCHEMA, build_steering_console_snapshot, render_steering_console


def source() -> dict[str, object]:
    return {
        "current_state": "CURRENT_WITH_OPEN_OBLIGATIONS",
        "goals": [{"goal_id": "goal-important", "status": "ACTIVE", "statement": "Important synthetic Goal", "deadline_state": "DUE", "blockers": ["blocked-ref"]}],
        "intents": [{"intent_id": "intent-paused", "status": "PAUSED", "statement": "Paused direction"}, {"intent_id": "intent-old", "status": "SUPERSEDED", "statement": "Old direction"}],
        "why_next": {"goal_id": "goal-important", "why_now": "Due with explicit inputs", "suggestion": "Review blocker", "blockers": ["blocked-ref"], "permission_budget_resource": ["goal-important:permission=eligible"], "owner_override_ref": "none", "pack_ref": "pack-1", "executor_ref": "executor-1", "unknowns": ["unknown-1"]},
        "owner_decisions": [{"decision_id": "decision-1", "status": "PENDING", "summary": "Not accepted"}],
        "completed_runs": [{"run_id": "run-pass", "run_status": "PASS", "goal_id": "goal-important", "goal_status": "ACTIVE"}],
    }


class SteeringConsoleTests(unittest.TestCase):
    def test_human_surface_contains_steering_sections(self) -> None:
        snapshot = build_steering_console_snapshot(source())
        self.assertEqual(snapshot["schema"], STEERING_DRIVER_CONSOLE_SCHEMA)
        text = render_steering_console(snapshot)
        for phrase in ("Important Goal", "Why now", "Owner decisions", "Completed Runs with Goal still unsatisfied", "Paused Intents", "Superseded Intents", "Unknowns"):
            self.assertIn(phrase, text)

    def test_completed_run_does_not_imply_goal_satisfied(self) -> None:
        snapshot = build_steering_console_snapshot(source())
        self.assertEqual(snapshot["completed_runs_goal_unsatisfied"][0]["goal_status"], "ACTIVE")

    def test_private_display_content_is_rejected(self) -> None:
        value = source()
        value["why_next"] = {**value["why_next"], "why_now": "prompt body"}
        with self.assertRaises(DriverConsoleError):
            build_steering_console_snapshot(value)


if __name__ == "__main__":
    unittest.main()
