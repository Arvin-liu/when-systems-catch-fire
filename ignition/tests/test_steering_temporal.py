from __future__ import annotations

import unittest

from agent_runtime.steering import AuthorityProvenance, SteeringValidationError, TemporalWindow, evaluate_temporal


class TemporalTests(unittest.TestCase):
    def test_not_before_and_deadline_are_deterministic(self) -> None:
        window = TemporalWindow("window-1", "Asia/Shanghai", "OWNER_DECLARED", "owner-time", not_before="2026-08-22T12:00:00+08:00", deadline="2026-08-25T17:00:00+08:00")
        self.assertEqual(evaluate_temporal(window, now="2026-08-21T12:00:00+08:00").state, "NOT_YET")
        self.assertEqual(evaluate_temporal(window, now="2026-08-25T17:00:00+08:00").state, "DUE")

    def test_grace_and_stale_are_distinct(self) -> None:
        window = TemporalWindow("window-2", "UTC", "OWNER_DECLARED", "owner-time", deadline="2026-08-21T12:00:00+00:00", grace_seconds=3600)
        self.assertEqual(evaluate_temporal(window, now="2026-08-21T12:30:00+00:00").state, "GRACE")
        self.assertEqual(evaluate_temporal(window, now="2026-08-21T13:01:00+00:00").state, "STALE")

    def test_unknown_time_is_not_autofilled(self) -> None:
        window = TemporalWindow("window-3", "UTC", "SYSTEM_DERIVED_PROPOSAL", "unknown", unknown_time=True)
        self.assertEqual(evaluate_temporal(window, now="2026-08-21T12:00:00+00:00").state, "UNKNOWN")

    def test_invalid_order_is_rejected(self) -> None:
        with self.assertRaises(SteeringValidationError):
            TemporalWindow("window-4", "UTC", "OWNER_DECLARED", "owner-time", not_before="2026-08-25T00:00:00+00:00", deadline="2026-08-21T00:00:00+00:00")

    def test_recurrence_is_data_not_scheduler(self) -> None:
        window = TemporalWindow("window-5", "UTC", "OWNER_DECLARED", "owner-time", review_after="2026-08-22T00:00:00+00:00", recurrence={"frequency": "weekly", "interval": 1})
        self.assertEqual(window.recurrence["frequency"], "weekly")
        self.assertEqual(evaluate_temporal(window, now="2026-08-22T00:00:00+00:00").state, "REVIEW_DUE")


if __name__ == "__main__":
    unittest.main()
