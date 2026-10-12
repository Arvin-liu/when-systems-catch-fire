import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_link_only_navigation_does_not_create_a_claim_or_url_signal(self):
        navigation = "[Guide](https://example.test/theorem-proof)"
        self.assertFalse(self.adjudicator.candidate(navigation, markdown=True))
        self.assertTrue(self.adjudicator.editorial_navigation_only_fragment(navigation))

    def test_public_surface_anchor_survives_inserted_navigation_line(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "SUMMARY.md"
            claim = "This theorem proves a universal result."
            source.write_text(claim + "\n", encoding="utf-8")
            with patch.object(self.adjudicator, "repo_path", return_value=source):
                before, _ = self.adjudicator.text_fragments("SUMMARY.md")
                before_fragment = next(row for row in before if row.get("candidate", True))
                before_anchor = self.adjudicator.anchor("SUMMARY.md", before_fragment, "CURRENT_PUBLIC_SURFACE")
                source.write_text("[Guide](https://example.test/theorem-proof)\n" + claim + "\n", encoding="utf-8")
                after, _ = self.adjudicator.text_fragments("SUMMARY.md")
                after_fragment = next(row for row in after if row.get("candidate", True))
                after_anchor = self.adjudicator.anchor("SUMMARY.md", after_fragment, "CURRENT_PUBLIC_SURFACE")
            self.assertEqual(before_anchor, after_anchor)
            self.assertNotIn("first_line", after_anchor)
            self.assertEqual(after_fragment["line"], 2)
            self.assertTrue(any(row.get("impact_class") == "EDITORIAL_NAVIGATION_ONLY" for row in after))

    def test_claim_bearing_link_label_remains_a_new_candidate_with_all_audits(self):
        linked_claim = "[This theorem proves a universal result.](https://example.test/source)"
        self.assertTrue(self.adjudicator.candidate(linked_claim, markdown=True))
        self.assertEqual(self.adjudicator.impact_class_for_fragment(linked_claim, is_new=True, markdown=True), "NEW_CLAIM_CANDIDATE")
        claim_class = self.adjudicator.classify(linked_claim)
        kind = self.adjudicator.assertion_type(claim_class)
        disposition = self.adjudicator.disposition_for(claim_class, "CURRENT_PUBLIC_SURFACE", linked_claim, None, None)
        audits = self.adjudicator.audits_for(claim_class, kind, linked_claim, disposition, "CURRENT_PUBLIC_SURFACE")
        self.assertEqual(set(audits), {
            "definition_audit", "quantifier_audit", "proof_audit", "counterexample_audit",
            "type_dimension_audit", "internal_external_audit", "model_class_audit",
            "cross_domain_audit", "evidence_audit", "novelty_audit", "prediction_audit",
            "conclusion_rebound_audit", "public_surface_audit",
        })

    def test_operational_state_record_marker_excludes_only_marked_lines(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        marked_lines = {index for index, line in enumerate(source, 1) if self.adjudicator.OPERATIONAL_RECORD_ONLY_MARKER in line}
        self.assertGreaterEqual(len(marked_lines), 6)
        fragments, status = self.adjudicator.text_fragments("STATE-CHANGELOG.md")
        self.assertIn(status, {"SCANNED_REGISTERED", "SCANNED_NO_CANDIDATE"})
        self.assertTrue(marked_lines.isdisjoint({fragment["line"] for fragment in fragments}))


if __name__ == "__main__":
    unittest.main()
