from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))
sys.path.insert(0, str(IGNITION_ROOT / "evaluation" / "tests"))

from evaluation.tools import finalize_successor_read_ledger_r0_3 as finalizer  # noqa: E402
from test_task187_r0_2_synthetic_reproduction import run_guard_staging_fixture  # noqa: E402


SYNTHETIC_COMPONENT_ID = "synthetic-branch-guard"
SYNTHETIC_COMPONENT_PATH = "synthetic/branch-guard.py"
SYNTHETIC_COGNITIVE_PATH = "synthetic/cognitive-source.txt"
TASK187_STEP00_HARNESS_SHA256 = "2679e3674dc8c8812ec2538b4dbc51b4b64f8c6ace8d20ca1dd1ec37a4a9e8f3"
TASK187_STEP00_REPORT_MD_SHA256 = "3d967c518363f266a3a0be29ce990f49660354f4f389dad71fdb482f573ada48"
TASK187_STEP00_REPORT_JSON_SHA256 = "3e3bb78ad9a429323c69fa71e35d418419314ef0763bc26dd926b78ca81e52fa"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def formatted_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def synthetic_manifest() -> dict[str, Any]:
    validator = {
        "component_id": finalizer.VALIDATOR_COMPONENT_ID,
        "path": finalizer.VALIDATOR_SOURCE_REL,
        "source_sha256": sha256(finalizer.SOURCE_PATH.read_bytes()),
        "evidence_scope": "FINAL_ATTESTATION_SURFACE",
        "successor_access": "EXECUTE_STATUS_ONLY",
        "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
        "allowed_status_codes": list(finalizer.STATUS_CODES),
    }
    operational_control = {
        "component_id": SYNTHETIC_COMPONENT_ID,
        "path": SYNTHETIC_COMPONENT_PATH,
        "source_sha256": "1" * 64,
        "evidence_scope": "CERTIFIED_LEDGER_SCOPE",
        "successor_access": "EXECUTE_STATUS_ONLY",
        "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
        "allowed_status_codes": ["PASS_BRANCH_AUTHORIZED", "FAIL_UNEXPLAINED_WORKTREE"],
    }
    return {
        "schema_version": finalizer.MANIFEST_SCHEMA_VERSION,
        "manifest_path": finalizer.MANIFEST_REL,
        "task_id": finalizer.TASK_ID,
        "cognitive_evidence_surface": {
            "files": [{"path": SYNTHETIC_COGNITIVE_PATH, "sha256": "2" * 64}]
        },
        "operational_control_surface": {"components": [validator, operational_control]},
    }


def ledger_entry(
    action: str,
    path: str,
    *,
    component_id: str | None = None,
    content_exposure: str = "NO",
    case_specific: bool = False,
    digest: str | None = None,
    status: str | None = None,
    disposition: str = "CLEAN",
) -> dict[str, Any]:
    return {
        "path": path,
        "component_id": component_id,
        "action_kind": action,
        "purpose": "synthetic R0.3 regression fixture",
        "content_exposure": content_exposure,
        "case_specific_information_exposed": case_specific,
        "digest": digest,
        "observed_status_code": status,
        "contamination_disposition": disposition,
    }


def ledger_summary(entries: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "cognitive_reads": sum(row["action_kind"] == "COGNITIVE_READ" for row in entries),
        "operational_executions": sum(row["action_kind"] == "OPERATIONAL_EXECUTION" for row in entries),
        "operational_status_observations": sum(
            row["action_kind"] == "OPERATIONAL_STATUS_OBSERVED" for row in entries
        ),
        "prohibited_cognitive_reads": sum(
            row["action_kind"] == "PROHIBITED_COGNITIVE_READ" for row in entries
        ),
        "contaminated_entries": sum(
            row["contamination_disposition"] == "CONTAMINATED" for row in entries
        ),
    }


def open_ledger(
    manifest_bytes: bytes,
    entries: list[dict[str, Any]] | None = None,
    *,
    summary_override: dict[str, int] | None = None,
    trial_override: str | None = None,
) -> dict[str, Any]:
    rows = list(entries or [])
    summary = ledger_summary(rows)
    trial = "PROTOCOL_CONTAMINATED" if summary["contaminated_entries"] else "CLEAN"
    return {
        "schema_version": finalizer.LEDGER_SCHEMA_VERSION,
        "task_id": finalizer.TASK_ID,
        "manifest_path": finalizer.MANIFEST_REL,
        "manifest_sha256": sha256(manifest_bytes),
        "ledger_state": "OPEN",
        "entries": rows,
        "summary": summary_override if summary_override is not None else summary,
        "trial_disposition": trial_override if trial_override is not None else trial,
        "closure": None,
    }


class Task187R03RegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = synthetic_manifest()
        self.manifest_bytes = formatted_json(self.manifest)

    def assert_ledger_schema_valid(self, ledger: dict[str, Any]) -> None:
        schema_bytes = finalizer.LEDGER_SCHEMA_PATH.read_bytes()
        self.assertTrue(finalizer._schema_valid(ledger, schema_bytes))

    def test_clean_frozen_ledger_gets_tool_bound_pass_receipt(self) -> None:
        ledger_bytes = formatted_json(open_ledger(self.manifest_bytes))
        with tempfile.TemporaryDirectory(prefix="task187-r0-3-receipt-") as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "successor-read-ledger-r0.3.json"
            manifest_path = root / "synthetic-manifest.json"
            receipt_path = root / "successor-ledger-validation-receipt-r0.3.json"
            ledger_path.write_bytes(ledger_bytes)
            manifest_path.write_bytes(self.manifest_bytes)

            status = finalizer.finalize_files(ledger_path, manifest_path, receipt_path)
            closed_bytes = ledger_path.read_bytes()
            receipt_bytes = receipt_path.read_bytes()
            receipt = json.loads(receipt_bytes)

            self.assertEqual(status, finalizer.PASS)
            self.assertEqual(receipt["validator_status"], finalizer.PASS)
            self.assertEqual(receipt["ledger_sha256"], sha256(closed_bytes))
            self.assertEqual(receipt["manifest_sha256"], sha256(self.manifest_bytes))
            self.assertEqual(receipt["validator_component_id"], finalizer.VALIDATOR_COMPONENT_ID)
            self.assertEqual(receipt["validator_source_sha256"], sha256(finalizer.SOURCE_PATH.read_bytes()))
            self.assertEqual(receipt["final_validator_scope"], finalizer.FINAL_SCOPE)
            self.assertTrue(finalizer.verify_receipt_bytes(receipt_bytes, closed_bytes, self.manifest_bytes))

    def test_one_byte_change_after_receipt_invalidates_attestation(self) -> None:
        ledger_bytes = formatted_json(open_ledger(self.manifest_bytes))
        closed, status = finalizer.finalize_ledger_bytes(ledger_bytes, self.manifest_bytes)
        self.assertEqual(status, finalizer.PASS)
        assert closed is not None
        receipt = finalizer.receipt_bytes_for(closed, self.manifest_bytes, status)

        digest = sha256(self.manifest_bytes).encode("ascii")
        offset = closed.index(digest)
        replacement = b"0" if closed[offset:offset + 1] != b"0" else b"1"
        changed = closed[:offset] + replacement + closed[offset + 1:]
        self.assertEqual(len(changed), len(closed))
        self.assertEqual(sum(left != right for left, right in zip(changed, closed)), 1)
        self.assertFalse(finalizer.verify_receipt_bytes(receipt, changed, self.manifest_bytes))

    def test_schema_valid_summary_mismatch_fails(self) -> None:
        bad = open_ledger(self.manifest_bytes, summary_override={
            "cognitive_reads": 1,
            "operational_executions": 0,
            "operational_status_observations": 0,
            "prohibited_cognitive_reads": 0,
            "contaminated_entries": 0,
        })
        self.assert_ledger_schema_valid(bad)
        status = finalizer.finalize_ledger_bytes(formatted_json(bad), self.manifest_bytes)[1]
        self.assertEqual(status, finalizer.INVALID)

    def test_forbidden_cognitive_read_is_contaminated(self) -> None:
        row = ledger_entry(
            "PROHIBITED_COGNITIVE_READ",
            "synthetic/forbidden-source.txt",
            content_exposure="YES",
            digest="3" * 64,
            disposition="CONTAMINATED",
        )
        ledger = open_ledger(self.manifest_bytes, [row])
        self.assert_ledger_schema_valid(ledger)
        closed, status = finalizer.finalize_ledger_bytes(formatted_json(ledger), self.manifest_bytes)
        self.assertEqual(status, finalizer.CONTAMINATED)
        self.assertIsNotNone(closed)

    def test_unknown_operational_component_is_contaminated(self) -> None:
        row = ledger_entry(
            "OPERATIONAL_STATUS_OBSERVED",
            "synthetic/unknown-guard.py",
            component_id="not-in-manifest",
            status="PASS_BRANCH_AUTHORIZED",
            disposition="CONTAMINATED",
        )
        ledger = open_ledger(self.manifest_bytes, [row])
        self.assert_ledger_schema_valid(ledger)
        status = finalizer.finalize_ledger_bytes(formatted_json(ledger), self.manifest_bytes)[1]
        self.assertEqual(status, finalizer.CONTAMINATED)

    def test_case_specific_information_in_operational_status_is_contaminated(self) -> None:
        row = ledger_entry(
            "OPERATIONAL_STATUS_OBSERVED",
            SYNTHETIC_COMPONENT_PATH,
            component_id=SYNTHETIC_COMPONENT_ID,
            case_specific=True,
            status="PASS_BRANCH_AUTHORIZED",
            disposition="CONTAMINATED",
        )
        ledger = open_ledger(self.manifest_bytes, [row])
        self.assert_ledger_schema_valid(ledger)
        status = finalizer.finalize_ledger_bytes(formatted_json(ledger), self.manifest_bytes)[1]
        self.assertEqual(status, finalizer.CONTAMINATED)

    def test_minimal_forged_pass_receipt_is_rejected_and_not_overwritten(self) -> None:
        ledger_bytes = formatted_json(open_ledger(self.manifest_bytes))
        closed, status = finalizer.finalize_ledger_bytes(ledger_bytes, self.manifest_bytes)
        self.assertEqual(status, finalizer.PASS)
        assert closed is not None
        forged = formatted_json({"validator_status": finalizer.PASS})
        self.assertFalse(finalizer.verify_receipt_bytes(forged, closed, self.manifest_bytes))

        with tempfile.TemporaryDirectory(prefix="task187-r0-3-forged-receipt-") as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "closed-ledger.json"
            manifest_path = root / "synthetic-manifest.json"
            receipt_path = root / "successor-ledger-validation-receipt-r0.3.json"
            ledger_path.write_bytes(closed)
            manifest_path.write_bytes(self.manifest_bytes)
            receipt_path.write_bytes(forged)
            self.assertEqual(finalizer.finalize_files(ledger_path, manifest_path, receipt_path), finalizer.INVALID)
            self.assertEqual(receipt_path.read_bytes(), forged)

    def test_repeated_finalization_returns_same_attestation_without_ledger_growth(self) -> None:
        ledger_bytes = formatted_json(open_ledger(self.manifest_bytes))
        with tempfile.TemporaryDirectory(prefix="task187-r0-3-repeat-") as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "successor-read-ledger-r0.3.json"
            manifest_path = root / "synthetic-manifest.json"
            receipt_path = root / "successor-ledger-validation-receipt-r0.3.json"
            ledger_path.write_bytes(ledger_bytes)
            manifest_path.write_bytes(self.manifest_bytes)

            first_status = finalizer.finalize_files(ledger_path, manifest_path, receipt_path)
            frozen_ledger = ledger_path.read_bytes()
            first_receipt = receipt_path.read_bytes()
            first_receipt_object = json.loads(first_receipt)
            second_status = finalizer.finalize_files(ledger_path, manifest_path, receipt_path)

            self.assertEqual(first_status, finalizer.PASS)
            self.assertEqual(second_status, first_status)
            self.assertEqual(ledger_path.read_bytes(), frozen_ledger)
            self.assertEqual(receipt_path.read_bytes(), first_receipt)
            self.assertEqual(json.loads(ledger_path.read_bytes())["entries"], [])
            self.assertEqual(first_receipt_object["ledger_sha256"], sha256(frozen_ledger))

    def test_final_validator_cannot_log_itself_into_certified_ledger(self) -> None:
        component = finalizer.VALIDATOR_COMPONENT_ID
        path = finalizer.VALIDATOR_SOURCE_REL
        rows = [
            ledger_entry("OPERATIONAL_EXECUTION", path, component_id=component),
            ledger_entry(
                "OPERATIONAL_STATUS_OBSERVED",
                path,
                component_id=component,
                status=finalizer.PASS,
            ),
        ]
        ledger = open_ledger(self.manifest_bytes, rows)
        self.assert_ledger_schema_valid(ledger)
        self.assertEqual(
            finalizer.finalize_ledger_bytes(formatted_json(ledger), self.manifest_bytes)[1],
            finalizer.INVALID,
        )

    def test_branch_guard_staging_lifecycle_does_not_change_cognitive_disposition(self) -> None:
        result = run_guard_staging_fixture()
        self.assertEqual(result["untracked_evidence_status"], "FAIL_UNEXPLAINED_WORKTREE")
        self.assertEqual(result["staged_evidence_status"], "PASS_BRANCH_AUTHORIZED")
        self.assertEqual(result["new_status_record_unstaged_status"], "FAIL_UNEXPLAINED_WORKTREE")
        self.assertEqual(result["new_status_record_staged_status"], "PASS_BRANCH_AUTHORIZED")
        self.assertEqual(result["cognitive_disposition_before_and_after"], "CLEAN")

    def test_r0_2_sources_and_synthetic_fixture_remain_historical(self) -> None:
        report_path = (
            REPO_ROOT
            / "ignition/reports/evaluations/ignition-187-r0-3-protocol-repair/r0-2-invalid-reproduction.json"
        )
        report = json.loads(report_path.read_bytes())
        historical_sources = {
            "read_ledger_schema": REPO_ROOT
            / "ignition/evaluation/heldout/r0.2/successor-visible/successor-read-ledger-r0.2.schema.json",
            "validator": REPO_ROOT / "ignition/evaluation/tools/validate_successor_read_ledger_r0_2.py",
            "branch_guard": REPO_ROOT / "ignition/evaluation/tools/task_branch_guard_r0_2.py",
            "authorization_schema": REPO_ROOT
            / "ignition/evaluation/operational-control/r0.2/task-branch-authorization-r0.2.schema.json",
        }
        for name, path in historical_sources.items():
            self.assertEqual(sha256(path.read_bytes()), report["source_sha256"][name], name)

        frozen_artifacts = {
            "ignition/evaluation/tests/test_task187_r0_2_synthetic_reproduction.py": TASK187_STEP00_HARNESS_SHA256,
            "ignition/reports/evaluations/ignition-187-r0-3-protocol-repair/r0-2-invalid-reproduction.md": TASK187_STEP00_REPORT_MD_SHA256,
            "ignition/reports/evaluations/ignition-187-r0-3-protocol-repair/r0-2-invalid-reproduction.json": TASK187_STEP00_REPORT_JSON_SHA256,
        }
        for relative_path, expected_sha256 in frozen_artifacts.items():
            self.assertEqual(sha256((REPO_ROOT / relative_path).read_bytes()), expected_sha256, relative_path)
        self.assertEqual(
            report["root_cause_classification"]["UNRESOLVED_WITHOUT_PRIVATE_LEDGER"],
            "RETAINED_FOR_THE_ACTUAL_TASK182_R2_INVALID_RESULT",
        )


if __name__ == "__main__":
    unittest.main()
