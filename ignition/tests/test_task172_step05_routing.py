"""Regression tests for the Task172 Step05 full function routing overlay."""

import unittest
from pathlib import Path

from tools.research.validate_task172_full_routing import validate


ROOT = Path(__file__).resolve().parents[1]


class Task172Step05RoutingTest(unittest.TestCase):
    def test_function_overlay_is_complete_and_deterministic(self) -> None:
        validate(ROOT, "FUNCTION_ASSET", "05")


if __name__ == "__main__":
    unittest.main()
