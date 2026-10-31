from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from unittest import mock

from tools import run_task139_live_admission as admission_gate


class Task139LiveAdmissionTests(unittest.TestCase):
    def test_single_live_attempt_admission_is_bounded_without_inference(self) -> None:
        # This Foundation probe exercises lease/admission boundaries only. Use
        # a disposable CLI contract and metadata-only auth reference so the
        # test is independent of a developer's local Codex install or secrets.
        with tempfile.TemporaryDirectory(prefix="task139-admission-fixture-") as temporary:
            root = Path(temporary)
            codex = root / "codex"
            codex.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"--version\" ]; then printf 'codex synthetic-r3-1\\n'; exit 0; fi\n"
                "if [ \"$1\" = \"exec\" ] && [ \"$2\" = \"--help\" ]; then\n"
                "  printf '%s\\n' '--json --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox --cd --output-schema'; exit 0;\n"
                "fi\n"
                "exit 2\n",
                encoding="utf-8",
            )
            codex.chmod(0o755)
            auth_source = root / "auth-source"
            auth_source.mkdir()
            control_repo = root / "control-repo"
            control_repo.mkdir()
            document_root = root / "documents"
            document_root.mkdir()
            with mock.patch.multiple(
                admission_gate,
                CODEX=codex,
                AUTH_SOURCE=auth_source,
                CONTROL_REPO=control_repo,
                DOCUMENT_ROOT=document_root,
            ):
                report = admission_gate.run_gate()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["census"]["selected_executor_id"], "external.codex")
        self.assertEqual(report["admission"]["status"], "ADMITTED")
        self.assertEqual(report["admission"]["effective_capabilities"], ["repo.read"])
        self.assertEqual(report["probe_calls"], 2)
        self.assertFalse(report["dispatch"]["inference_started"])
        self.assertTrue(report["filesystem"]["runtime_parent_separate_from_capture_parent"])
        self.assertTrue(report["filesystem"]["workspace_read_only_guard"])
        self.assertEqual(report["child_depth_guard"], "PASS_ONE_LEVEL_ONLY")
        self.assertEqual(report["validator_freeze"]["status"], "PASS")
        self.assertTrue(report["validator_freeze"]["self_test_is_not_live_result"])


if __name__ == "__main__":
    unittest.main()
