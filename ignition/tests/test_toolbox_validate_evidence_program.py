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
    def test_compact_run_preserves_current_preregistration_order_failures(self) -> None:
        result = TOOL.build_validation_result()
        self.assertEqual(result["result_status"], "VALIDATION_FAILURES_PRESENT")
        self.assertEqual(result["exit_code"], 1)
        self.assertGreaterEqual(result["check_count"], 400)
        self.assertEqual(result["failure_count"], 2)
        self.assertTrue(result["git_metadata_read_only"])
        self.assertEqual(result["evidence_program_tree"]["path"], "ignition/evidence-program")
        self.assertEqual(len(result["validator_source"]["sha256"]), 64)
        self.assertIn("does not authenticate source origins", result["claim_ceiling"])
        self.assertEqual(
            [line for line in result["failure_details"] if line.startswith("[FAIL]")],
            [
                "[FAIL] ordering:IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION:prereg-ancestor-of-head — prereg a4d13a69ac ancestor of HEAD",
                "[FAIL] ordering:IGNITION-EVIDENCE-PILOT-R1-OPENALEX-DOI-REPLICATION-20260801:prereg-ancestor-of-head — prereg a830664c1a ancestor of HEAD",
            ],
        )

    def test_cli_emits_failure_json_and_makes_no_repo_writes(self) -> None:
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
        self.assertEqual(completed.returncode, 1, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["result_status"], "VALIDATION_FAILURES_PRESENT")
        self.assertEqual(result["failure_count"], 2)
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
