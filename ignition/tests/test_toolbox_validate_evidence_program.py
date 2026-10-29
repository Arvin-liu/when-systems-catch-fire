from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_validate_evidence_program.py"
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_validate_evidence_program as TOOL  # noqa: E402


class EvidenceProgramToolboxTests(unittest.TestCase):
    def test_compact_run_reports_current_preregistration_order_resolved(self) -> None:
        result = TOOL.build_validation_result()
        self.assertEqual(result["result_status"], "ALL_CHECKS_PASSED")
        self.assertEqual(result["exit_code"], 0)
        self.assertGreaterEqual(result["check_count"], 400)
        self.assertEqual(result["failure_count"], 0)
        self.assertTrue(result["git_metadata_read_only"])
        self.assertEqual(result["evidence_program_tree"]["path"], "ignition/evidence-program")
        self.assertEqual(len(result["validator_source"]["sha256"]), 64)
        self.assertIn("does not authenticate source origins", result["claim_ceiling"])


    def test_cli_emits_current_success_json_and_makes_no_repo_writes(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain", "--", "ignition/evidence-program"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--check"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        after = subprocess.run(
            ["git", "status", "--porcelain", "--", "ignition/evidence-program"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["result_status"], "ALL_CHECKS_PASSED")
        self.assertEqual(result["failure_count"], 0)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
