from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


IGNITION = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION / "tools/toolbox_audit_finding_comparator.py"
sys.path.insert(0, str(IGNITION / "tools"))
import toolbox_audit_finding_comparator as tool  # noqa: E402


def review(audit_id: str, reviewer_ref: str, findings: list[dict]) -> dict:
    return {
        "audit_id": audit_id,
        "reviewer_ref": reviewer_ref,
        "scope_ref": "formal-main-to-candidate-route",
        "target_ref": "Arvin-liu/when-systems-catch-fire",
        "target_revision": "213e386e0b4cbb4d7ba35ac4267b7aaa2e1c9872",
        "findings": findings,
    }


def finding(finding_id: str, disposition: str, ref: str = "receipt.json", digest: str = "a" * 64) -> dict:
    return {
        "finding_id": finding_id,
        "disposition": disposition,
        "evidence_refs": [{"ref": ref, "sha256": digest}],
    }


def request(primary: dict | None = None, second: dict | None = None) -> dict:
    return {
        "schema_version": tool.REQUEST_SCHEMA_VERSION,
        "comparison_id": "route-audit-compare-213e",
        "primary_audit": primary or review("route-receipt", "route-validator", [finding("unmapped-paths", "CONFIRMED")]),
        "second_review": second or review("evidence-review", "evidence-reader", [finding("unmapped-paths", "CONFIRMED")]),
    }


class AuditFindingComparatorTests(unittest.TestCase):
    def test_reports_agreement_without_claiming_independent_review_or_truth(self) -> None:
        raw = json.dumps(request(), ensure_ascii=False).encode()
        result = tool.compare_audit_findings(
            json.loads(raw), raw_input_sha256=hashlib.sha256(raw).hexdigest(),
        )
        self.assertEqual(result["comparison_status"], "CALLER_DECLARED_AUDIT_RECORDS_COMPARED")
        self.assertEqual(result["findings"][0]["record_relation"], "DISPOSITION_AGREES")
        self.assertEqual(result["reviewer_binding"]["relation"], "DISTINCT_CALLER_DECLARED_REVIEWER_REFERENCES_IDENTITY_UNVERIFIED")
        self.assertFalse(result["reviewer_binding"]["reviewer_independence_established"])
        self.assertEqual(result["interpretation"]["claim_truth"], "NOT_EVALUATED")
        self.assertEqual(result["interpretation"]["decision_authority"], "NONE")
        self.assertFalse(result["interpretation"]["execution_authorized"])

    def test_reports_new_missing_and_disagreeing_findings_and_evidence_refs(self) -> None:
        primary = review("audit-a", "reviewer-a", [
            finding("shared", "NEEDS_VALIDATION", "primary.json", "a" * 64),
            finding("primary-only", "REJECTED"),
        ])
        second = review("audit-b", "reviewer-b", [
            finding("shared", "CONFIRMED", "second.json", "b" * 64),
            finding("second-only", "OUT_OF_SCOPE"),
        ])
        result = tool.compare_audit_findings(request(primary, second), raw_input_sha256="c" * 64)
        rows = {row["finding_id"]: row for row in result["findings"]}
        self.assertEqual(rows["shared"]["record_relation"], "DISPOSITION_DIFFERS")
        self.assertEqual(rows["primary-only"]["record_relation"], "ONLY_IN_PRIMARY_AUDIT")
        self.assertEqual(rows["second-only"]["record_relation"], "ONLY_IN_SECOND_REVIEW")
        self.assertEqual(result["summary"]["disposition_disagreements"], 1)
        self.assertEqual(result["summary"]["evidence_reference_sets_different"], 1)

    def test_same_reviewer_reference_is_not_reported_as_independent(self) -> None:
        primary = review("audit-a", "same-reviewer", [])
        second = review("audit-b", "same-reviewer", [])
        result = tool.compare_audit_findings(request(primary, second), raw_input_sha256="d" * 64)
        self.assertEqual(result["reviewer_binding"]["relation"], "SAME_CALLER_DECLARED_REVIEWER_REFERENCE")
        self.assertFalse(result["reviewer_binding"]["reviewer_independence_established"])

    def test_incompatible_scope_or_target_is_rejected(self) -> None:
        primary = review("audit-a", "reviewer-a", [])
        second = review("audit-b", "reviewer-b", [])
        second["target_revision"] = "different-revision"
        with self.assertRaisesRegex(tool.AuditFindingComparisonError, "identical target_revision"):
            tool.compare_audit_findings(request(primary, second), raw_input_sha256="e" * 64)
        second["target_revision"] = primary["target_revision"]
        second["scope_ref"] = "different-scope"
        with self.assertRaisesRegex(tool.AuditFindingComparisonError, "identical scope_ref"):
            tool.compare_audit_findings(request(primary, second), raw_input_sha256="f" * 64)

    def test_duplicate_finding_ids_and_evidence_references_are_rejected(self) -> None:
        primary = review("audit-a", "reviewer-a", [finding("dup", "CONFIRMED"), finding("dup", "REJECTED")])
        with self.assertRaisesRegex(tool.AuditFindingComparisonError, "finding_id values must be unique"):
            tool.compare_audit_findings(request(primary), raw_input_sha256="1" * 64)
        primary = review("audit-a", "reviewer-a", [finding("dup", "CONFIRMED")])
        primary["findings"][0]["evidence_refs"].append(dict(primary["findings"][0]["evidence_refs"][0]))
        with self.assertRaisesRegex(tool.AuditFindingComparisonError, "duplicate reference identities"):
            tool.compare_audit_findings(request(primary), raw_input_sha256="2" * 64)

    def test_bad_digests_dispositions_and_unknown_fields_are_rejected(self) -> None:
        primary = review("audit-a", "reviewer-a", [finding("f", "CONFIRMED", digest="not-a-sha")])
        with self.assertRaisesRegex(tool.AuditFindingComparisonError, "lowercase SHA-256"):
            tool.compare_audit_findings(request(primary), raw_input_sha256="3" * 64)
        primary = review("audit-a", "reviewer-a", [finding("f", "PASS")])
        with self.assertRaisesRegex(tool.AuditFindingComparisonError, "disposition is unsupported"):
            tool.compare_audit_findings(request(primary), raw_input_sha256="4" * 64)
        malformed = request()
        malformed["unexpected"] = True
        with self.assertRaisesRegex(tool.AuditFindingComparisonError, "request must contain exactly"):
            tool.compare_audit_findings(malformed, raw_input_sha256="5" * 64)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        raw = b'{"schema_version":"a","schema_version":"b"}'
        with self.assertRaisesRegex(tool.AuditFindingComparisonError, "duplicate JSON input key"):
            json.loads(raw, object_pairs_hook=tool._reject_duplicate_keys)

    def test_cli_emits_comparison_without_input_notes(self) -> None:
        raw = json.dumps(request(), ensure_ascii=False).encode()
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=raw,
            cwd=IGNITION.parent,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        result = json.loads(completed.stdout)
        self.assertEqual(result["input_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotIn("confidential", completed.stdout.decode("utf-8"))
        self.assertFalse(result["interpretation"]["execution_authorized"])

    def test_cli_rejects_oversized_input_without_partial_output(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=b" " * (tool.MAX_REQUEST_BYTES + 1),
            cwd=IGNITION.parent,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, b"")
        self.assertIn(b"256000-byte limit", completed.stderr)


if __name__ == "__main__":
    unittest.main()
