from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CurrentSurfaceDeterminismTests(unittest.TestCase):
    def test_current_facts_snapshot_and_surfaces_are_deterministic(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/check_current_projection_determinism.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
