from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Task172GateTTests(unittest.TestCase):
    def test_gate_t_artifacts_are_closed(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/research/validate_task172_gate_t.py", "--repo-root", str(ROOT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("TASK172_GATE_T_VALIDATION_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
