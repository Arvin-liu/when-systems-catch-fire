import importlib.util
import hashlib
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

    def test_q1_editorial_proof_mentions_keep_source_ceiling_and_coverage(self):
        editorial_paths = {
            "docs/what-is-ignition/README.md",
            "docs/what-is-ignition/2026-10-13-gpt6-participant-reflection.md",
        }
        manifest_path = ROOT / "data/foundation/repository-path-classification/classification-manifest.jsonl"
        manifest = {
            row["path"][len("ignition/"):]: row["category"]
            for row in (json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines())
            if row["path"].startswith("ignition/")
        }
        self.assertEqual({path: manifest.get(path) for path in editorial_paths}, {
            path: "EDITORIAL_ARTICLE" for path in editorial_paths
        })

        reflection = "docs/what-is-ignition/2026-10-13-gpt6-participant-reflection.md"
        proof_limit_lines = [
            (reflection, 7),
            (reflection, 15),
            ("docs/what-is-ignition/README.md", 15),
        ]
        for path, line_number in proof_limit_lines:
            text = (ROOT / path).read_text(encoding="utf-8").splitlines()[line_number - 1]
            self.assertEqual(self.adjudicator.classify(text, source_path=path), "UNRESOLVED_CLAIM")
            self.assertEqual(self.adjudicator.classify(text), "THEOREM_OR_MATHEMATICAL_CLAIM")

        theorem = "Theorem: every finite graph has a spanning forest."
        self.assertEqual(
            self.adjudicator.classify(theorem, source_path="docs/what-is-ignition/README.md"),
            "THEOREM_OR_MATHEMATICAL_CLAIM",
        )

        outputs = self.adjudicator.build()
        summary = json.loads(outputs[ROOT / "data/foundation/nonfunction-claims/closure-summary.json"])
        discovery = [
            json.loads(line)
            for line in outputs[ROOT / "data/foundation/nonfunction-claims/source-discovery.jsonl"].splitlines()
            if line.strip()
        ]
        discovery_paths = [row["path"] for row in discovery]
        self.assertEqual(len(discovery_paths), len(set(discovery_paths)))
        self.assertEqual(summary["tracked_files_accounted"], len(discovery_paths))
        for path, expected_count in ((reflection, 13), ("docs/what-is-ignition/README.md", 3)):
            row = next(item for item in discovery if item["path"] == path)
            self.assertEqual(row["coverage_status"], "SCANNED_REGISTERED")
            self.assertEqual(row["candidate_fragments"], expected_count)

        registry = [
            json.loads(line)
            for line in outputs[ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"].splitlines()
            if line.strip()
        ]
        rows = [
            row for row in registry
            if any(anchor["path"] in editorial_paths for anchor in row["source_anchors"])
        ]
        self.assertEqual(len(rows), 16)
        quarantine = {"NFC-3e00c3b947c97890", "NFC-84ef1c09d7dd193e"}
        self.assertEqual({row["canonical_id"] for row in rows if row["final_disposition"] == "QUARANTINED_AMBIGUOUS"}, quarantine)
        for row in rows:
            self.assertEqual(row["external_evidence_maturity"], "E0")
            self.assertEqual(row["mathematical_maturity"], "M0")
            self.assertNotEqual(row["reviewer_state"], "TASK98_99_AUTHORITY_INHERITED")
            self.assertFalse(any(ref.get("supports_exact_claim") for ref in row["evidence_references"]))
            self.assertFalse(any(ref.get("kind") == "FUNCTION_ASSET_AUTHORITY" for ref in row["evidence_references"]))
            if row["canonical_id"] in quarantine:
                self.assertEqual(row["claim_ceiling"], "Unresolved historical or current claim candidate; it cannot appear as current knowledge.")
            else:
                self.assertEqual(row["final_disposition"], "HISTORICAL_ONLY")
                self.assertEqual(row["claim_ceiling"], "Historical source wording only; it is not a current repository endorsement.")

        false_theorem_ids = {"NFC-28ad745b599b9e9c", "NFC-79e4f2beeeb89ff9", "NFC-f41818a4a2bbdec4"}
        by_id = {row["canonical_id"]: row for row in rows}
        self.assertTrue(false_theorem_ids.issubset(by_id))
        for claim_id in false_theorem_ids:
            self.assertNotEqual(by_id[claim_id]["claim_class"], "THEOREM_OR_MATHEMATICAL_CLAIM")
            self.assertNotEqual(by_id[claim_id]["assertion_type"], "MATHEMATICAL")

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
            claim = "[This theorem proves a universal result.](https://example.test/old-source)"
            source.write_text(claim + "\n", encoding="utf-8")
            with patch.object(self.adjudicator, "repo_path", return_value=source):
                before, _ = self.adjudicator.text_fragments("SUMMARY.md")
                before_fragment = next(row for row in before if row.get("candidate", True))
                before_anchor = self.adjudicator.anchor("SUMMARY.md", before_fragment, "CURRENT_PUBLIC_SURFACE")
                updated_claim = claim.replace("old-source", "new-source")
                source.write_text("[Guide](https://example.test/theorem-proof)\n" + updated_claim + "\n", encoding="utf-8")
                after, _ = self.adjudicator.text_fragments("SUMMARY.md")
                after_fragment = next(row for row in after if row.get("candidate", True))
                after_anchor = self.adjudicator.anchor("SUMMARY.md", after_fragment, "CURRENT_PUBLIC_SURFACE")
            self.assertEqual(before_anchor, after_anchor)
            self.assertNotIn("first_line", after_anchor)
            self.assertEqual(after_fragment["line"], 2)
            self.assertTrue(any(row.get("impact_class") == "EDITORIAL_NAVIGATION_ONLY" for row in after))

    def test_link_destination_does_not_define_identity_but_visible_change_does(self):
        original = "[This theorem proves a universal result.](https://example.test/old-source)"
        moved = "[This theorem proves a universal result.](https://example.test/new-source)"
        changed = "[This theorem proves a different universal result.](https://example.test/new-source)"

        def candidate_id(text):
            normalized = self.adjudicator.normalize(text)
            return "NFC-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

        for text in (original, moved, changed):
            self.assertTrue(self.adjudicator.candidate(text, markdown=True))
        self.assertEqual(candidate_id(original), candidate_id(moved))
        self.assertNotEqual(candidate_id(original), candidate_id(changed))

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
