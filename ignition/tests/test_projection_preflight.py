"""Contract tests for the read-only deterministic projection preflight."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from tools import run_projection_preflight as preflight


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/135/step02-projection-preflight-fixtures-r1.json"


class ProjectionPreflightTests(unittest.TestCase):
    def test_contract_declares_only_read_only_commands(self) -> None:
        contract = preflight.load_contract()
        self.assertEqual(contract["mode"], "READ_ONLY_CHECKS")
        self.assertTrue(contract["clean_tree_required_before_full_suite"])
        self.assertTrue(all(row["read_only"] is True for row in contract["commands"]))
        self.assertGreaterEqual(len(contract["commands"]), 20)

    def test_stale_fixture_cannot_enter_release_gate(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for case in fixture["cases"]:
            run = {
                "projection_checks_pass": False,
                "side_effect_detected": False,
                "failed_checks": [case["check_id"]],
                "worktree_before": {"clean": True},
                "worktree_after": {"clean": True},
            }
            gate = preflight.gate_admission(run, require_clean=True)
            self.assertFalse(gate["projection_checks_pass"])
            self.assertFalse(gate["release_admission"])
            self.assertEqual(gate["result"], "FAIL")

    def test_clean_gate_rejects_dirty_tree(self) -> None:
        run = {
            "projection_checks_pass": True,
            "side_effect_detected": False,
            "failed_checks": [],
            "worktree_before": {"clean": False},
            "worktree_after": {"clean": True},
        }
        gate = preflight.gate_admission(run, require_clean=True)
        self.assertFalse(gate["clean_tree_gate_pass"])
        self.assertFalse(gate["release_admission"])

    def test_check_argv_has_no_regeneration_switch(self) -> None:
        contract = preflight.load_contract()
        for row in contract["commands"]:
            self.assertNotIn("--write", row["argv"], row["id"])
            self.assertNotIn("--generate", row["argv"], row["id"])

    def test_runner_uses_explicit_interpreter_and_application_root(self) -> None:
        self.assertEqual(preflight.ROOT.name, "ignition")
        self.assertEqual(preflight.command_line(["tools/example.py", "--check"])[0], sys.executable)


if __name__ == "__main__":
    unittest.main()
