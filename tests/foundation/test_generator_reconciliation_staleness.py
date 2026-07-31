#!/usr/bin/env python3
"""Generator determinism & task-106 reconciliation staleness (Task 107 §4, 6-8).

These are the heavy, Layer-B-negative fixtures.  They prove:
  * 6  no stale deep-adjudication / nonfunction output is committed
        (the generator --check is byte-deterministic against committed outputs);
  * 7  two-pass fixed point -- re-running the generator after one pass does not
        drift again (correct generation order, contract §3.3);
  * 8  task-106 current-truth / propagation products are not stale
        (contract §6 propagation proof prerequisite).
All commands are read-only (--check / unit tests); nothing is written to the tree.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run(args: list[str]) -> int:
    cp = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
    if cp.returncode != 0:
        print(cp.stdout)
        print(cp.stderr)
    return cp.returncode


class GeneratorDeterminismTest(unittest.TestCase):
    # Scenario 6: committed outputs are not stale.
    def test_nonfunction_output_not_stale(self) -> None:
        self.assertEqual(
            _run(["tools/foundation/adjudicate_nonfunction_claims.py", "--check"]), 0,
            "nonfunction generator --check reported drift (stale committed output)",
        )

    # Scenario 7: two-pass fixed point (a second --check after the first must also pass).
    def test_two_pass_fixed_point(self) -> None:
        first = _run(["tools/foundation/adjudicate_nonfunction_claims.py", "--check"])
        second = _run(["tools/foundation/adjudicate_nonfunction_claims.py", "--check"])
        self.assertEqual(first, 0, "first generator --check failed")
        self.assertEqual(second, 0, "second generator --check drifted (not at fixed point)")


class Task106ReconciliationStalenessTest(unittest.TestCase):
    # Scenario 8: task-106 current-truth / propagation products are current.
    def test_propagation_reconciliation_unit(self) -> None:
        self.assertEqual(
            _run(["-m", "unittest", "tests.test_propagation_reconciliation", "-v"]), 0,
            "task-106 propagation reconciliation unit tests failed",
        )

    def test_propagation_reconciliation_check(self) -> None:
        self.assertEqual(
            _run(["tools/propagation/validate_reconciliation.py", "--check"]), 0,
            "task-106 propagation reconciliation --check reported drift",
        )


if __name__ == "__main__":
    unittest.main()
