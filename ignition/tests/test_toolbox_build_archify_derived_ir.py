from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_build_archify_derived_ir.py"
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_build_archify_derived_ir as TOOL  # noqa: E402


class ArchifyDerivedIRToolboxTests(unittest.TestCase):
    def test_emits_complete_ir_and_source_bindings_without_provider_invocation(self) -> None:
        result = TOOL.build_derived_ir_result("a" * 40)
        self.assertEqual(result["result_status"], "DERIVED_IR_READY")
        self.assertFalse(result["provider_invoked"])
        self.assertEqual(result["formal_revision_binding"], "CALLER_SUPPLIED_NOT_RESOLVED_BY_THIS_TOOL")
        self.assertEqual(result["counts"]["components"], len(result["ir"]["components"]))
        self.assertEqual(result["counts"]["connections"], len(result["ir"]["connections"]))
        self.assertEqual(len(result["source_refs"]), 4)
        self.assertEqual(result["ir"]["meta"]["repository"]["revision"], "a" * 40)
        self.assertIn("does not establish external Archify validation", result["claim_ceiling"])

    def test_rejects_moving_or_malformed_revision(self) -> None:
        for revision in ("main", "refs/heads/main", "A" * 40, "0" * 39):
            with self.subTest(revision=revision):
                with self.assertRaisesRegex(TOOL.DerivedIRRunError, "exact lowercase"):
                    TOOL.build_derived_ir_result(revision)

    def test_cli_rejects_duplicate_keys_without_partial_stdout(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input='{"formal_revision":"' + "a" * 40 + '","formal_revision":"' + "b" * 40 + '"}',
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("duplicate JSON key", completed.stderr)

    def test_cli_rejects_oversized_request_without_partial_stdout(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=" " * (TOOL.MAX_REQUEST_BYTES + 1),
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("exceeds 4 KiB", completed.stderr)


if __name__ == "__main__":
    unittest.main()
