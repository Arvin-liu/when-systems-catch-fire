"""Regression tests for the Task172 Step08 metadata-only pilot."""

import unittest
from pathlib import Path

from tools.research.validate_task172_step08 import validate


ROOT = Path(__file__).resolve().parents[1]


class Task172Step08Test(unittest.TestCase):
    def test_step08_packet_is_fail_closed_and_complete(self) -> None:
        validate(ROOT)


if __name__ == "__main__":
    unittest.main()
