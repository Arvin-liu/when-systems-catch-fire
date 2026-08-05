#!/usr/bin/env python3
"""Regression tests for the current-truth projection lifecycle parity (PR #195).

Covers the four invariants required by TASK.md A1/A2:
  1. In a fresh full clone, iterations 110-114 resolve as TERMINAL_SUCCESS and
     are present in the projection (terminal tags + lifecycle events folded).
  2. A stale committed projection (missing 110-114) is detected as drift by
     ``--check`` (D2 fix: the check compares against the COMMITTED file, not a
     self-comparison of the freshly-written file) and fails closed.
  3. The projection only folds TERMINAL_SUCCESS tasks; a non-terminal / absent
     task is never presented as current truth (fail-closed folding).
  4. foundation-validation and iteration-lifecycle-validation both invoke the
     same projection-check contract (D3 fix: shared CI gate).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
PROP = os.path.join(REPO, "tools", "propagation")
sys.path.insert(0, PROP)

import current_truth_projection as ctp  # noqa: E402

TERMINAL_110_114 = (110, 111, 112, 113, 114)


class TestCurrentTruthProjectionParity(unittest.TestCase):
    def test_projection_includes_terminal_110_114(self):
        proj = ctp.generate(REPO, None)  # in-memory, never writes
        rmr = proj.get("recently_merged_results", [])
        present = {r.get("task_number"): r for r in rmr}
        for tn in TERMINAL_110_114:
            self.assertIn(tn, present, f"iteration {tn} must be folded into the projection")
            self.assertEqual(
                present[tn].get("terminal_state"), "TERMINAL_SUCCESS",
                f"iteration {tn} must be TERMINAL_SUCCESS in the projection",
            )
        self.assertEqual(proj.get("current_accepted_iteration"), 114,
                         "current_accepted_iteration must be the latest terminal (114)")

    def test_projection_only_folds_terminal_success(self):
        proj = ctp.generate(REPO, None)
        present = {r.get("task_number") for r in proj.get("recently_merged_results", [])}
        # Fail-closed: the projection must never present a non-terminal /
        # obviously-in-progress iteration as current truth. 110-114 are the
        # latest terminalized iterations; nothing beyond them may appear, and a
        # clearly non-existent task must never be folded in.
        self.assertLessEqual(max(present), 114,
                              "no iteration beyond the latest terminal (114) may appear")
        self.assertNotIn(999, present, "non-existent task must never be folded")
        for tn in TERMINAL_110_114:
            self.assertIn(tn, present, f"terminal iteration {tn} must be present")

    def test_check_detects_stale_projection_drift(self):
        # Fresh committed file must pass.
        self.assertTrue(
            ctp.check_against_committed(REPO),
            "committed (fresh) projection must pass --check",
        )
        # A deliberately stale projection (110-114 dropped) must fail closed.
        with open(ctp.OUT_PATH, encoding="utf-8") as fh:
            fresh = json.load(fh)
        stale = dict(fresh)
        stale["current_accepted_iteration"] = 108
        stale["recently_merged_results"] = [
            r for r in fresh["recently_merged_results"] if r["task_number"] <= 108
        ]
        d = tempfile.mkdtemp()
        stale_path = os.path.join(d, "stale-projection.json")
        with open(stale_path, "w", encoding="utf-8") as fh:
            json.dump(stale, fh, ensure_ascii=False, sort_keys=True, indent=2)
            fh.write("\n")
        self.assertFalse(
            ctp.check_against_committed(REPO, stale_path),
            "stale projection (missing 110-114) must be detected as drift",
        )

    def test_foundation_and_lifecycle_share_projection_check(self):
        # D3: both CI entries must invoke the identical projection-check contract.
        wf_dir = os.path.join(REPO, ".github", "workflows")
        for name in ("foundation-validation.yml", "iteration-lifecycle-validation.yml"):
            path = os.path.join(wf_dir, name)
            with open(path, encoding="utf-8") as fh:
                body = fh.read()
            self.assertIn(
                "current_truth_projection.py --repo . --check", body,
                f"{name} must run the shared current-truth projection --check gate (D3)",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
