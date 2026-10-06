import builtins
import io
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def load_module(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class NonFunctionClaimClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adjudicator = load_module("tools/foundation/adjudicate_nonfunction_claims.py", "task100_adjudicator")
        cls.fixtures = [json.loads(line) for line in (ROOT / "tests/foundation/fixtures/nonfunction_claim_gate_cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

    def run_ok(self, *args):
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_closure_validator(self):
        self.run_ok(sys.executable, "tools/foundation/validate_nonfunction_claim_closure.py")

    def test_generator_is_deterministic(self):
        self.run_ok(sys.executable, "tools/foundation/adjudicate_nonfunction_claims.py", "--check")

    def test_regression_gate_cases(self):
        for row in self.fixtures:
            claim_class = self.adjudicator.classify(row["text"])
            kind = self.adjudicator.assertion_type(claim_class)
            disposition = self.adjudicator.disposition_for(claim_class, "CURRENT_REPOSITORY_RECORD", row["text"], None, None)
            audits = self.adjudicator.audits_for(claim_class, kind, row["text"], disposition, "CURRENT_REPOSITORY_RECORD")
            self.assertEqual(audits[row["expected_gate"]], row["expected_result"], row["case_id"])
            self.assertEqual(disposition, row["expected_disposition"], row["case_id"])

    def test_rebound_normalization_removes_renaming_adjectives(self):
        left = self.adjudicator.semantic_rebound_text("Physical grand unification proved impossible")
        right = self.adjudicator.semantic_rebound_text("Structural grand unification proved impossible")
        self.assertEqual(left, right)

    def test_candidate_discovery_is_conservative_but_multilingual(self):
        self.assertTrue(self.adjudicator.candidate("This theorem proves a universal result."))
        self.assertTrue(self.adjudicator.candidate("该机制导致普遍结果。"))
        self.assertFalse(self.adjudicator.candidate("ordinary navigation entry"))

    def test_all_task229_r4_paths_are_excluded_before_any_body_open(self):
        prefix = self.adjudicator.TASK229_R4_PROTECTED_PREFIX
        protected_paths = [path for path in self.adjudicator.tracked_paths() if path.startswith(prefix)]
        self.assertEqual(len(protected_paths), 55)

        ignition_root = self.adjudicator.ROOT.resolve()
        opened = []

        def is_protected(file):
            if isinstance(file, int):
                return False
            try:
                candidate = Path(os.fspath(file))
                if not candidate.is_absolute():
                    candidate = ignition_root / candidate
                relative = candidate.resolve().relative_to(ignition_root).as_posix()
            except (OSError, TypeError, ValueError):
                return False
            return relative.startswith(prefix)

        def reject_open(file):
            if is_protected(file):
                opened.append(os.fspath(file))
                raise AssertionError("protected Task229/R4 body was opened")

        real_path_open = Path.open
        real_path_read_text = Path.read_text
        real_path_read_bytes = Path.read_bytes
        real_builtin_open = builtins.open
        real_io_open = io.open
        real_os_open = os.open

        def guarded_path_open(path, *args, **kwargs):
            reject_open(path)
            return real_path_open(path, *args, **kwargs)

        def guarded_path_read_text(path, *args, **kwargs):
            reject_open(path)
            return real_path_read_text(path, *args, **kwargs)

        def guarded_path_read_bytes(path, *args, **kwargs):
            reject_open(path)
            return real_path_read_bytes(path, *args, **kwargs)

        def guarded_builtin_open(file, *args, **kwargs):
            reject_open(file)
            return real_builtin_open(file, *args, **kwargs)

        def guarded_io_open(file, *args, **kwargs):
            reject_open(file)
            return real_io_open(file, *args, **kwargs)

        def guarded_os_open(file, *args, **kwargs):
            reject_open(file)
            return real_os_open(file, *args, **kwargs)

        with (
            mock.patch.object(self.adjudicator, "tracked_paths", return_value=protected_paths),
            mock.patch.object(self.adjudicator, "load_jsonl", return_value=[]),
            mock.patch.object(self.adjudicator, "admission_for_path", return_value=SimpleNamespace(auto_discovery=True, classification="TEST")) as admission,
            mock.patch.object(self.adjudicator, "current_or_archived_text", side_effect=AssertionError("protected archive fallback was used")),
            mock.patch.object(Path, "open", guarded_path_open),
            mock.patch.object(Path, "read_text", guarded_path_read_text),
            mock.patch.object(Path, "read_bytes", guarded_path_read_bytes),
            mock.patch.object(builtins, "open", guarded_builtin_open),
            mock.patch.object(io, "open", guarded_io_open),
            mock.patch.object(os, "open", guarded_os_open),
        ):
            outputs = self.adjudicator.build()

        self.assertEqual(opened, [])
        self.assertEqual(admission.call_count, 0)
        rows = [
            json.loads(line)
            for line in outputs[self.adjudicator.OUT / "source-discovery.jsonl"].splitlines()
            if line.strip()
        ]
        protected_rows = [row for row in rows if row["path"].startswith(prefix)]
        self.assertEqual({row["path"] for row in protected_rows}, set(protected_paths))
        self.assertEqual(len(protected_rows), 55)
        self.assertTrue(all(row["coverage_status"] == "EXCLUDED_NON_AUTHORITATIVE_RUNTIME_EVIDENCE" for row in protected_rows))
        self.assertTrue(all(row["candidate_fragments"] == 0 and row["canonical_claim_ids"] == [] for row in protected_rows))
        self.assertTrue(all(row["exclusion_reason"] == "EXCLUDED_NON_AUTHORITATIVE_RUNTIME_EVIDENCE" for row in protected_rows))

    def test_task229_r4_path_is_excluded_before_any_body_open(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            ignition_root = repo_root / "ignition"
            protected = ignition_root / "evaluation/ignition-229-r4-synthetic-probe.json"
            protected.parent.mkdir(parents=True)
            protected.write_text('{"claim":"This theorem proves a universal result."}\n', encoding="utf-8")

            real_path_open = Path.open
            opened = []

            def guarded_path_open(path, *args, **kwargs):
                if path == protected:
                    opened.append(str(path))
                    raise AssertionError("protected Task229/R4 body was opened")
                return real_path_open(path, *args, **kwargs)

            with (
                mock.patch.object(self.adjudicator, "ROOT", ignition_root),
                mock.patch.object(self.adjudicator, "REPO_ROOT", repo_root),
                mock.patch.object(self.adjudicator, "GIT_ROOT", repo_root),
                mock.patch.object(
                    self.adjudicator,
                    "admission_for_path",
                    return_value=SimpleNamespace(auto_discovery=True, classification="TEST"),
                ),
                mock.patch.object(Path, "open", guarded_path_open),
            ):
                fragments, status = self.adjudicator.text_fragments(
                    "evaluation/ignition-229-r4-synthetic-probe.json"
                )

            self.assertEqual(fragments, [])
            self.assertEqual(status, "EXCLUDED_NON_AUTHORITATIVE_RUNTIME_EVIDENCE")
            self.assertEqual(opened, [])

    def test_operational_state_record_marker_excludes_only_marked_lines(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        marked_lines = {index for index, line in enumerate(source, 1) if self.adjudicator.OPERATIONAL_RECORD_ONLY_MARKER in line}
        self.assertGreaterEqual(len(marked_lines), 6)
        fragments, status = self.adjudicator.text_fragments("STATE-CHANGELOG.md")
        self.assertIn(status, {"SCANNED_REGISTERED", "SCANNED_NO_CANDIDATE"})
        self.assertTrue(marked_lines.isdisjoint({fragment["line"] for fragment in fragments}))


if __name__ == "__main__":
    unittest.main()
