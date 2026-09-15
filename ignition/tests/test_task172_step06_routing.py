"""Regression tests for the Task172 Step06 full nonfunction routing overlay."""

import unittest
from pathlib import Path

from tools.research.validate_task172_full_routing import validate


ROOT = Path(__file__).resolve().parents[1]


class Task172Step06RoutingTest(unittest.TestCase):
    def test_nonfunction_overlay_is_complete_and_deterministic(self) -> None:
        validate(ROOT, "NONFUNCTION_CLAIM", "06")


if __name__ == "__main__":
    unittest.main()
