"""Expose the existing RPE pytest suites through the Foundation unittest router."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class IgnitionRuntimeR1ConsumerTests(unittest.TestCase):
    def test_existing_fix_and_scenario_suites(self) -> None:
        suites = [
            REPO_ROOT / "tests/ignition_runtime/test_fix_regressions.py",
            REPO_ROOT / "tests/ignition_runtime/test_scenarios.py",
        ]
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-ra", *(str(path) for path in suites)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"existing Ignition RPE pytest suites failed:\n{completed.stdout}{completed.stderr}",
        )
