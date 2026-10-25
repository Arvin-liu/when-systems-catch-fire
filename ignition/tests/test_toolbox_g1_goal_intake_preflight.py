from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


IGNITION = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION.parent
FIXTURE = IGNITION / "research_os_v1/g1_goal_intake/fixtures/structurally-valid-proposal.json"
TOOL_PATH = IGNITION / "tools/toolbox_g1_goal_intake_preflight.py"
sys.path.insert(0, str(IGNITION / "tools"))
import toolbox_g1_goal_intake_preflight as tool  # noqa: E402


class ToolboxG1GoalIntakeTests(unittest.TestCase):
    def test_valid_proposal_remains_owner_gated_and_noncanonical(self) -> None:
        receipt = tool.build_receipt(FIXTURE.read_bytes())
        report = receipt["preflight_report"]
        self.assertEqual(receipt["tool_id"], "research.preflight_g1_goal_intake")
        self.assertFalse(receipt["execution_authorized"])
        self.assertEqual(report["preflight_status"], "REQUIRES_OWNER_AUTHORITY")
        self.assertEqual(report["structural_outcome"], "CANDIDATE_STRUCTURALLY_VALID_PROPOSAL_ONLY")
        self.assertEqual(report["authority"]["owner_identity"], "NOT_AUTHENTICATED")
        self.assertFalse(report["effects"]["canonical_records_written"])
        self.assertFalse(report["effects"]["goal_lifecycle_mutated"])
        self.assertFalse(report["effects"]["completion_decision_evaluated"])
        self.assertFalse(report["effects"]["dispatch"])

    def test_forged_owner_claim_is_reported_without_authentication(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["request"]["declared_origin"] = "OWNER_DECLARED"
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        report = tool.build_receipt(raw)["preflight_report"]
        self.assertEqual(report["preflight_status"], "REQUIRES_OWNER_AUTHORITY")
        self.assertEqual(report["authority"]["owner_identity"], "NOT_AUTHENTICATED")
        self.assertIn("owner_claim_unverified", {item["code"] for item in report["findings"]})

    def test_malformed_and_oversized_inputs_stay_machine_readable(self) -> None:
        malformed = tool.build_receipt(b"{broken")
        oversized = tool.build_receipt(b" " * (tool.MAX_INPUT_BYTES + 1))
        self.assertEqual(malformed["preflight_report"]["preflight_status"], "INVALID_INPUT")
        self.assertEqual(oversized["preflight_report"]["preflight_status"], "INVALID_INPUT")
        self.assertFalse(malformed["execution_authorized"])
        self.assertFalse(oversized["execution_authorized"])

    def test_cli_emits_deterministic_json_to_stdout_without_report_path(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain", "--", "ignition/research_os_v1/g1_goal_intake"],
            cwd=REPO_ROOT, text=True, capture_output=True, check=True,
        ).stdout
        env = dict(os.environ)
        env["PYTHONPATH"] = str(IGNITION)
        runs = [
            subprocess.run(
                [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
                cwd=REPO_ROOT, env=env, input=FIXTURE.read_bytes(), capture_output=True, check=False,
            )
            for _ in range(2)
        ]
        after = subprocess.run(
            ["git", "status", "--porcelain", "--", "ignition/research_os_v1/g1_goal_intake"],
            cwd=REPO_ROOT, text=True, capture_output=True, check=True,
        ).stdout
        self.assertEqual([r.returncode for r in runs], [0, 0])
        self.assertEqual(runs[0].stdout, runs[1].stdout)
        receipt = json.loads(runs[0].stdout)
        self.assertEqual(receipt["preflight_report"]["preflight_status"], "REQUIRES_OWNER_AUTHORITY")
        self.assertEqual(after, before)

    def test_unknown_cli_options_cannot_select_input_or_output_paths(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            forbidden_output = Path(temp_dir) / "unexpected-report"
            result = subprocess.run(
                [sys.executable, "-B", str(TOOL_PATH), "--stdin", "--report-dir", str(forbidden_output)],
                cwd=REPO_ROOT, input=FIXTURE.read_bytes(), capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b"")
            self.assertFalse(forbidden_output.exists())


if __name__ == "__main__":
    unittest.main()
