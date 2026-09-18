from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evaluation" / "heldout" / "r0.2"))

import build_packet_manifest  # noqa: E402
from evaluation.tools import validate_successor_read_ledger_r0_2 as ledger_validator  # noqa: E402


MANIFEST_PATH = build_packet_manifest.MANIFEST
BUILDER = build_packet_manifest.PACKET / "build_packet_manifest.py"
REPO_ROOT = ROOT.parent


class Task182R02ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_bytes = MANIFEST_PATH.read_bytes()
        cls.manifest = json.loads(cls.manifest_bytes.decode("utf-8"))
        cls.manifest_sha = hashlib.sha256(cls.manifest_bytes).hexdigest()

    def entry(
        self,
        *,
        path: str,
        action: str,
        component_id: str | None = None,
        content_exposure: str = "YES",
        case_specific: bool = False,
        digest: str | None = None,
        status: str | None = None,
        disposition: str = "CLEAN",
    ) -> dict:
        return {
            "path": path,
            "component_id": component_id,
            "action_kind": action,
            "purpose": "protocol fixture",
            "content_exposure": content_exposure,
            "case_specific_information_exposed": case_specific,
            "digest": digest,
            "observed_status_code": status,
            "contamination_disposition": disposition,
        }

    def ledger(self, entries: list[dict], disposition: str = "CLEAN") -> dict:
        contaminated = sum(row["contamination_disposition"] == "CONTAMINATED" for row in entries)
        counts = {
            "cognitive_reads": sum(row["action_kind"] == "COGNITIVE_READ" for row in entries),
            "operational_executions": sum(row["action_kind"] == "OPERATIONAL_EXECUTION" for row in entries),
            "operational_status_observations": sum(row["action_kind"] == "OPERATIONAL_STATUS_OBSERVED" for row in entries),
            "prohibited_cognitive_reads": sum(row["action_kind"] == "PROHIBITED_COGNITIVE_READ" for row in entries),
            "contaminated_entries": contaminated,
        }
        return {
            "schema_version": "successor-read-ledger-r0.2",
            "task_id": "IGNITION-20260918-182-R2",
            "allowed_manifest_sha256": self.manifest_sha,
            "entries": entries,
            "summary": counts,
            "trial_disposition": disposition,
        }

    def contamination_entry(self, path: str) -> dict:
        return self.entry(
            path=path,
            action="PROHIBITED_COGNITIVE_READ",
            content_exposure="YES",
            digest="a" * 64,
            disposition="CONTAMINATED",
        )

    def test_packet_manifest_has_distinct_surfaces_and_two_fresh_case_ids(self) -> None:
        cognitive = self.manifest["cognitive_evidence_surface"]["files"]
        operational = self.manifest["operational_control_surface"]["components"]
        cognitive_paths = {row["path"] for row in cognitive}
        operational_paths = {row["path"] for row in operational}
        self.assertEqual(
            self.manifest["case_ids"],
            ["coastal-meter-study-r02-01", "harbor-export-policy-r02-01"],
        )
        self.assertTrue(cognitive_paths.isdisjoint(operational_paths))
        self.assertNotIn("content-research-01", self.manifest["case_ids"])
        self.assertNotIn("engineering-governance-01", self.manifest["case_ids"])
        self.assertEqual(
            self.manifest["operational_control_surface"]["read_policy"],
            "EXECUTE_ONLY; STATUS_ONLY; SOURCE_AND_RECEIPT_CONTENT_READ_PROHIBITED",
        )

    def test_packet_validator_accepts_provenance_and_surface_hashes(self) -> None:
        build_packet_manifest.validate_packet(self.manifest)

    def test_manifest_second_build_is_byte_fixed_point(self) -> None:
        first = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, str(BUILDER)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(first, hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest())

    def test_cognitive_read_of_allowlisted_manifest_and_file_passes(self) -> None:
        file_path = "ignition/evaluation/heldout/r0.2/successor-visible/bootstrap.md"
        file_digest = next(
            row["sha256"] for row in self.manifest["cognitive_evidence_surface"]["files"]
            if row["path"] == file_path
        )
        entries = [
            self.entry(
                path=self.manifest["manifest_path"],
                action="COGNITIVE_READ",
                digest=self.manifest_sha,
            ),
            self.entry(path=file_path, action="COGNITIVE_READ", digest=file_digest),
        ]
        self.assertEqual(
            ledger_validator.validate_payload(self.ledger(entries), self.manifest, self.manifest_bytes),
            ledger_validator.PASS,
        )

    def test_hook_execution_and_finite_status_are_not_cognitive_contamination(self) -> None:
        hook_path = "ignition/evaluation/hooks/pre-push"
        entries = [
            self.entry(
                path=hook_path,
                action="OPERATIONAL_EXECUTION",
                component_id="git-pre-push-hook",
                content_exposure="NO",
            ),
            self.entry(
                path=hook_path,
                action="OPERATIONAL_STATUS_OBSERVED",
                component_id="git-pre-push-hook",
                content_exposure="NO",
                status="PASS_BRANCH_AUTHORIZED",
            ),
        ]
        self.assertEqual(
            ledger_validator.validate_payload(self.ledger(entries), self.manifest, self.manifest_bytes),
            ledger_validator.PASS,
        )

    def test_direct_hook_source_read_is_contaminated(self) -> None:
        row = self.contamination_entry("ignition/evaluation/hooks/pre-push")
        row["component_id"] = "git-pre-push-hook"
        self.assertEqual(
            ledger_validator.validate_payload(
                self.ledger([row], "PROTOCOL_CONTAMINATED"), self.manifest, self.manifest_bytes
            ),
            ledger_validator.CONTAMINATED,
        )

    def test_evaluator_sealed_or_gold_path_read_is_contaminated(self) -> None:
        row = self.contamination_entry(
            "ignition/evaluation/heldout/r0.2/evaluator-sealed/gold.json"
        )
        self.assertEqual(
            ledger_validator.validate_payload(
                self.ledger([row], "PROTOCOL_CONTAMINATED"), self.manifest, self.manifest_bytes
            ),
            ledger_validator.CONTAMINATED,
        )

    def test_unlisted_cognitive_content_read_is_contaminated(self) -> None:
        row = self.entry(
            path="ignition/reports/evaluations/previous-trial/result.json",
            action="COGNITIVE_READ",
            digest="b" * 64,
            disposition="CONTAMINATED",
        )
        self.assertEqual(
            ledger_validator.validate_payload(
                self.ledger([row], "PROTOCOL_CONTAMINATED"), self.manifest, self.manifest_bytes
            ),
            ledger_validator.CONTAMINATED,
        )

    def test_case_specific_operational_output_leak_is_contaminated(self) -> None:
        row = self.entry(
            path="ignition/evaluation/tools/task_branch_guard_r0_2.py",
            action="OPERATIONAL_STATUS_OBSERVED",
            component_id="task-branch-guard",
            content_exposure="NO",
            case_specific=True,
            status="PASS_BRANCH_AUTHORIZED",
            disposition="CONTAMINATED",
        )
        self.assertEqual(
            ledger_validator.validate_payload(
                self.ledger([row], "PROTOCOL_CONTAMINATED"), self.manifest, self.manifest_bytes
            ),
            ledger_validator.CONTAMINATED,
        )

    def test_allowed_cognitive_file_hash_mismatch_is_contaminated(self) -> None:
        row = self.entry(
            path="ignition/evaluation/heldout/r0.2/successor-visible/bootstrap.md",
            action="COGNITIVE_READ",
            digest="f" * 64,
            disposition="CONTAMINATED",
        )
        self.assertEqual(
            ledger_validator.validate_payload(
                self.ledger([row], "PROTOCOL_CONTAMINATED"), self.manifest, self.manifest_bytes
            ),
            ledger_validator.CONTAMINATED,
        )

    def test_unlisted_status_code_cannot_pass_schema(self) -> None:
        row = self.entry(
            path="ignition/evaluation/hooks/pre-push",
            action="OPERATIONAL_STATUS_OBSERVED",
            component_id="git-pre-push-hook",
            content_exposure="NO",
            status="PASS_WITH_CASE_DETAILS",
        )
        self.assertEqual(
            ledger_validator.validate_payload(self.ledger([row]), self.manifest, self.manifest_bytes),
            ledger_validator.INVALID,
        )

    def test_status_only_component_cannot_be_executed_under_prohibited_component(self) -> None:
        row = self.entry(
            path="ignition/evaluation/operational-control/r0.2/task182-r2-branch-authorization-template.json",
            action="OPERATIONAL_EXECUTION",
            component_id="task182-r2-authorization-template",
            content_exposure="NO",
        )
        self.assertEqual(
            ledger_validator.validate_payload(
                self.ledger([row], "PROTOCOL_CONTAMINATED"), self.manifest, self.manifest_bytes
            ),
            ledger_validator.CONTAMINATED,
        )

    def test_manifest_digest_mismatch_is_invalid_fail_closed(self) -> None:
        ledger = self.ledger([])
        ledger["allowed_manifest_sha256"] = "0" * 64
        self.assertEqual(
            ledger_validator.validate_payload(ledger, self.manifest, self.manifest_bytes),
            ledger_validator.INVALID,
        )

    def test_clean_ledger_requires_exact_recomputed_summary(self) -> None:
        ledger = self.ledger([])
        ledger["summary"]["cognitive_reads"] = 1
        self.assertEqual(
            ledger_validator.validate_payload(ledger, self.manifest, self.manifest_bytes),
            ledger_validator.INVALID,
        )

    def test_contaminated_trial_receipt_preserves_quarantine_without_cognition_claim(self) -> None:
        receipt_path = ROOT / "reports" / "evaluations" / "ignition-182-protocol-repair-r1" / "task182-contamination-adjudication.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        ancestry = receipt["remote_ancestry"]
        handling = receipt["forensic_handling"]
        self.assertEqual(ancestry["branch_tip_sha"], "985ad8953a0eb7777817bee86ef086a739303f45")
        self.assertEqual(ancestry["disclosure_commit_parent_sha"], "5aecee5d4b6becaa954e5882d6869a292d393725")
        self.assertEqual(ancestry["s1_candidate_parent_sha"], "7cab7541895620d68d5bce2d16c46871ebd03ac0")
        self.assertEqual(handling["contamination_branch_disposition"], "PERMANENTLY_QUARANTINED_AS_CLEAN_TRIAL_EVIDENCE")
        self.assertFalse(handling["rewrite_amend_or_force_push_attempted"])
        self.assertEqual(receipt["cognitive_conclusion"]["r0_1_successor_cognitive_outcome"], "NOT_ADJUDICATED_FROM_CONTAMINATED_TRIAL")


if __name__ == "__main__":
    unittest.main()
