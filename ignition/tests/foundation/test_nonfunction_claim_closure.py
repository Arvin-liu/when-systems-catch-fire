import importlib.util
import json
import subprocess
import sys
import unittest
from unittest import mock
from pathlib import Path

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

    def test_operational_state_record_marker_excludes_only_marked_lines(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        marked_lines = {index for index, line in enumerate(source, 1) if self.adjudicator.OPERATIONAL_RECORD_ONLY_MARKER in line}
        self.assertGreaterEqual(len(marked_lines), 6)
        fragments, status = self.adjudicator.text_fragments("STATE-CHANGELOG.md")
        self.assertIn(status, {"SCANNED_REGISTERED", "SCANNED_NO_CANDIDATE"})
        self.assertTrue(marked_lines.isdisjoint({fragment["line"] for fragment in fragments}))

    def test_task186_research_and_evaluation_exclusions_are_recorded_before_source_reads(self):
        fixture = json.loads((ROOT / "tests/foundation/fixtures/task186_research_surface_isolation.json").read_text(encoding="utf-8"))
        cases = (
            (fixture["external_research_report_path"], fixture["admission_classification"], fixture["nonfunction_coverage_status"]),
            (fixture["evaluation_plane_fixture_path"], fixture["evaluation_admission_classification"], fixture["evaluation_nonfunction_coverage_status"]),
        )
        for path, expected_class, expected_status in cases:
            admission = self.adjudicator.admission_for_path(path)
            self.assertEqual(admission.classification, expected_class)
            self.assertTrue(admission.provenance_only)
            self.assertFalse(admission.auto_discovery)
            with mock.patch.object(self.adjudicator, "repo_path", side_effect=AssertionError("excluded sources must not be opened")):
                fragments, status = self.adjudicator.text_fragments(path)
            self.assertEqual(fragments, [])
            self.assertEqual(status, expected_status)

        patches = (
            mock.patch.object(self.adjudicator, "tracked_paths", return_value=[path for path, _, _ in cases]),
            mock.patch.object(self.adjudicator, "load_jsonl", return_value=[]),
            mock.patch.object(
                self.adjudicator,
                "repo_path",
                side_effect=AssertionError("excluded sources must not be opened"),
            ),
        )
        with patches[0], patches[1], patches[2]:
            outputs = self.adjudicator.build()
        rows = [json.loads(line) for line in outputs[self.adjudicator.OUT / "source-discovery.jsonl"].splitlines() if line.strip()]
        by_path = {row["path"]: row for row in rows}
        for path, _, expected_status in cases:
            self.assertEqual(by_path[path]["coverage_status"], expected_status)
            self.assertEqual(by_path[path]["exclusion_reason"], expected_status)
            self.assertEqual(by_path[path]["candidate_fragments"], 0)
            self.assertEqual(by_path[path]["canonical_claim_ids"], [])


if __name__ == "__main__":
    unittest.main()
