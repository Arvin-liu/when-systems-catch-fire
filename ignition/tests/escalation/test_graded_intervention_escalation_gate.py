#!/usr/bin/env python3
"""CLI and evidence-integrity regressions for the Q43 escalation gate."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools/escalation/validate_graded_intervention_escalation_gate.py"
FIXTURES = ROOT / "data/escalation/fixtures"
PILOT = ROOT / "data/escalation/pilot-q43-i1.json"
Q42_HEAD = "3283ef6e76788b30a467467083f0d5ad7086b5a0"
HISTORICAL_EVIDENCE_HEAD = "2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98"


def run(bundle):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--bundle", str(bundle)],
        capture_output=True,
        text=True,
    )


class CapabilityGateTests(unittest.TestCase):
    def test_legacy_r2_fixture_matrix_fails_closed_on_stale_parent(self):
        paths = sorted(FIXTURES.glob("[0-9][0-9]-*.json"))
        self.assertEqual(len(paths), 24)
        for path in paths:
            result = run(path)
            if path.name == "02-schema-exit02.json":
                expected = 2  # Schema validation precedes parent binding.
            else:
                expected = 3  # Historical R2 parent head is not current Q42.
            self.assertEqual(
                result.returncode,
                expected,
                f"{path.name}: {result.stdout} {result.stderr}",
            )

    def test_historical_q43_pilot_fails_r3_semantic_role_check(self):
        result = run(PILOT)
        self.assertEqual(result.returncode, 30, result.stdout)
        self.assertIn("pilot_q42_i1", result.stdout)
        self.assertIn("RISK_CLASS", result.stdout)

    def test_typed_record_coverage(self):
        bundle = json.loads(PILOT.read_text())
        self.assertEqual(
            {record["record_type"] for record in bundle["records"]},
            {"REPOSITORY_LOCAL_REVERSIBLE", "HIGH_RISK_REQUEST_ONLY"},
        )
        self.assertEqual(
            set(bundle["facts"]),
            {
                "risk_class_required",
                "reversibility_required",
                "evidence_grade_required",
                "authority_required",
                "expertise_boundary_enforced",
                "automatic_only_repository_local",
                "confirmation_for_external",
                "high_risk_request_only",
                "prohibited_never_executed",
                "stop_rollback_return_present",
            },
        )

    def test_every_field_is_evidence_bound(self):
        bundle = json.loads(PILOT.read_text())
        fields = [
            "action_risk_class",
            "reversibility",
            "evidence_grade",
            "authority",
            "expertise_requirement",
            "automatic_repository_local_action",
            "user_confirmation_required",
            "expert_escalation",
            "institutional_approval",
            "prohibited_action",
            "request_only_external_action",
            "stop_rollback_result_return",
            "claim_ceiling",
        ]
        for record in bundle["records"]:
            for field in fields:
                self.assertTrue(record[field]["evidence_refs"], field)

    def test_git_object_binding_is_enforced(self):
        # The preserved Q43 sample has valid Git bindings but is not an R3 semantic pass.
        self.assertEqual(run(PILOT).returncode, 30)
        mutations = [
            ("sha256", "sha256:" + "0" * 64),
            ("blob_sha", "0" * 40),
            ("commit_sha", "0" * 40),
        ]
        for field, value in mutations:
            bundle = json.loads(PILOT.read_text())
            bundle["evidence_registry"][0][field] = value
            with tempfile.TemporaryDirectory(dir=FIXTURES) as tmpdir:
                path = Path(tmpdir) / "tampered.json"
                path.write_text(json.dumps(bundle, indent=2))
                self.assertEqual(run(path).returncode, 4, field)

    def test_q42_predecessor_and_historical_evidence_are_distinct(self):
        bundle = json.loads(PILOT.read_text())
        self.assertEqual(bundle["parent_binding"]["task_id"], "Q42-I1")
        self.assertEqual(bundle["parent_binding"]["exact_head"], Q42_HEAD)
        self.assertNotEqual(Q42_HEAD, HISTORICAL_EVIDENCE_HEAD)
        for evidence in bundle["evidence_registry"]:
            self.assertEqual(evidence.get("commit_sha"), HISTORICAL_EVIDENCE_HEAD)
            self.assertEqual(evidence.get("exact_head"), HISTORICAL_EVIDENCE_HEAD)
            self.assertTrue(evidence.get("repository_relative_path"))
            self.assertTrue(
                re.fullmatch(r"[0-9a-f]{40}", evidence.get("blob_sha", ""))
            )
            self.assertTrue(evidence.get("sha256", "").startswith("sha256:"))

        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", HISTORICAL_EVIDENCE_HEAD, Q42_HEAD],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(ancestor.returncode, 0, ancestor.stderr)

        # A wrong direct predecessor must be rejected before semantic evaluation.
        bundle["parent_binding"]["exact_head"] = "0" * 40
        with tempfile.TemporaryDirectory(dir=FIXTURES) as tmpdir:
            path = Path(tmpdir) / "wrong-parent.json"
            path.write_text(json.dumps(bundle, indent=2))
            self.assertEqual(run(path).returncode, 3)


if __name__ == "__main__":
    unittest.main()
