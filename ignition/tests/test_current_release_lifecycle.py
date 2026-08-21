from __future__ import annotations

import unittest

from tools import validate_current_release_lifecycle as lifecycle


class CurrentReleaseLifecycleTests(unittest.TestCase):
    def test_current_lifecycle_is_running_and_unpublished(self) -> None:
        self.assertEqual(lifecycle.validate(), [])
        record = lifecycle.load_json(lifecycle.LIFECYCLE_PATH)
        self.assertEqual(record["current_phase"], "RUNNING")
        self.assertEqual(record["publication_state"], "NOT_PUBLISHED")

    def test_terminal_phase_requires_terminal_task(self) -> None:
        record = lifecycle.load_json(lifecycle.LIFECYCLE_PATH)
        record["current_phase"] = "TERMINAL"
        record["task_branch_projection"] = "RELEASE_READY"
        self.assertTrue(any("must be terminal" in error for error in lifecycle.validate(record)))


if __name__ == "__main__":
    unittest.main()
