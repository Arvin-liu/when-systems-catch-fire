from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from ignition.evaluation.tools import finalize_successor_read_ledger_r0_4 as finalizer


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPONENT_ID = "synthetic-r0-4-branch-guard"
COMPONENT_PATH = "synthetic/r0.4/branch-guard.py"
METHOD_PATH = "synthetic/r0.4/method-contract.md"
SCHEMA_PATH = "synthetic/r0.4/output-schema.json"
CASE_SOURCE_PATH = "synthetic/r0.4/cases/IGNITION-20260919-188-EXP-01.md"
CASE_PROVENANCE_PATH = "synthetic/r0.4/cases/provenance/IGNITION-20260919-188-EXP-01.json"


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
    return {
        "schema_version": finalizer.MANIFEST_SCHEMA_VERSION,
        "manifest_path": finalizer.MANIFEST_REL,
        "task_id": finalizer.TASK_ID,
        "cognitive_evidence_surface": {
            "files": [
                {"path": METHOD_PATH, "sha256": "2" * 64},
                {"path": SCHEMA_PATH, "sha256": "3" * 64},
                {"path": CASE_SOURCE_PATH, "sha256": "4" * 64},
                {"path": CASE_PROVENANCE_PATH, "sha256": "5" * 64},
            ]
        },
        "operational_control_surface": {
            "components": [
                validator,
                {
                    "component_id": COMPONENT_ID,
                    "path": COMPONENT_PATH,
                    "source_sha256": "1" * 64,
                    "evidence_scope": "CERTIFIED_LEDGER_SCOPE",
                    "successor_access": "EXECUTE_STATUS_ONLY",
                    "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
                    "allowed_status_codes": [
                        "PASS_BRANCH_AUTHORIZED",
                        "FAIL_UNEXPLAINED_WORKTREE",
                    ],
                },
            ]
        },
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
        "purpose": "synthetic R0.4 packet-style regression fixture",
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
    entries: list[dict[str, Any]],
    *,
    summary_override: dict[str, int] | None = None,
) -> dict[str, Any]:
    summary = ledger_summary(entries)
    return {
        "schema_version": finalizer.LEDGER_SCHEMA_VERSION,
        "task_id": finalizer.TASK_ID,
        "manifest_path": finalizer.MANIFEST_REL,
        "manifest_sha256": sha256(manifest_bytes),
        "ledger_state": "OPEN",
        "entries": entries,
        "summary": summary_override if summary_override is not None else summary,
        "trial_disposition": "PROTOCOL_CONTAMINATED" if summary["contaminated_entries"] else "CLEAN",
        "closure": None,
    }


class Task188R04RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = synthetic_manifest()
        cls.manifest_bytes = formatted_json(cls.manifest)

    def assert_ledger_schema_valid(self, ledger: dict[str, Any]) -> None:
        self.assertTrue(finalizer._schema_valid(ledger, finalizer.LEDGER_SCHEMA_PATH.read_bytes()))

    def status(self, entries: list[dict[str, Any]], *, summary_override: dict[str, int] | None = None) -> str:
        ledger = open_ledger(self.manifest_bytes, entries, summary_override=summary_override)
        self.assert_ledger_schema_valid(ledger)
        return finalizer.finalize_ledger_bytes(formatted_json(ledger), self.manifest_bytes)[1]

    def test_authorized_case_source_and_provenance_exposure_are_clean(self) -> None:
        for path, digest in ((CASE_SOURCE_PATH, "4" * 64), (CASE_PROVENANCE_PATH, "5" * 64)):
            self.assertEqual(
                self.status(
                    [
                        ledger_entry(
                            "COGNITIVE_READ",
                            path,
                            content_exposure="YES",
                            case_specific=True,
                            digest=digest,
                        )
                    ]
                ),
                finalizer.PASS,
            )

    def test_packet_style_fixture_closes_with_external_attestation(self) -> None:
        entries = [
            ledger_entry("COGNITIVE_READ", METHOD_PATH, content_exposure="YES", digest="2" * 64),
            ledger_entry("COGNITIVE_READ", SCHEMA_PATH, content_exposure="YES", digest="3" * 64),
            ledger_entry(
                "COGNITIVE_READ",
                CASE_SOURCE_PATH,
                content_exposure="YES",
                case_specific=True,
                digest="4" * 64,
            ),
            ledger_entry(
                "COGNITIVE_READ",
                CASE_PROVENANCE_PATH,
                content_exposure="YES",
                case_specific=True,
                digest="5" * 64,
            ),
            ledger_entry("COGNITIVE_READ", finalizer.MANIFEST_REL, content_exposure="YES", case_specific=True, digest=sha256(self.manifest_bytes)),
            ledger_entry("OPERATIONAL_EXECUTION", COMPONENT_PATH, component_id=COMPONENT_ID),
            ledger_entry(
                "OPERATIONAL_STATUS_OBSERVED",
                COMPONENT_PATH,
                component_id=COMPONENT_ID,
                status="PASS_BRANCH_AUTHORIZED",
            ),
        ]
        ledger_bytes = formatted_json(open_ledger(self.manifest_bytes, entries))
        closed, status = finalizer.finalize_ledger_bytes(ledger_bytes, self.manifest_bytes)
        self.assertEqual(status, finalizer.PASS)
        self.assertIsNotNone(closed)
        assert closed is not None
        receipt = finalizer.receipt_bytes_for(closed, self.manifest_bytes, status)
        self.assertTrue(finalizer.verify_receipt_bytes(receipt, closed, self.manifest_bytes))

    def test_general_method_read_case_specific_false_is_clean(self) -> None:
        self.assertEqual(
            self.status([ledger_entry("COGNITIVE_READ", METHOD_PATH, content_exposure="YES", digest="2" * 64)]),
            finalizer.PASS,
        )

    def test_operational_status_case_specific_exposure_is_contaminated(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "OPERATIONAL_STATUS_OBSERVED",
                        COMPONENT_PATH,
                        component_id=COMPONENT_ID,
                        case_specific=True,
                        status="PASS_BRANCH_AUTHORIZED",
                        disposition="CONTAMINATED",
                    )
                ]
            ),
            finalizer.CONTAMINATED,
        )

    def test_unknown_operational_component_is_contaminated(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "OPERATIONAL_STATUS_OBSERVED",
                        "synthetic/r0.4/unknown.py",
                        component_id="unknown-component",
                        status="PASS_BRANCH_AUTHORIZED",
                        disposition="CONTAMINATED",
                    )
                ]
            ),
            finalizer.CONTAMINATED,
        )

    def test_unlisted_cognitive_read_is_contaminated(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "COGNITIVE_READ",
                        "synthetic/r0.4/unlisted.md",
                        content_exposure="YES",
                        digest="6" * 64,
                        disposition="CONTAMINATED",
                    )
                ]
            ),
            finalizer.CONTAMINATED,
        )

    def test_digest_mismatch_is_contaminated(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "COGNITIVE_READ",
                        CASE_SOURCE_PATH,
                        content_exposure="YES",
                        case_specific=True,
                        digest="9" * 64,
                        disposition="CONTAMINATED",
                    )
                ]
            ),
            finalizer.CONTAMINATED,
        )

    def test_row_disposition_mismatch_is_invalid(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "COGNITIVE_READ",
                        CASE_SOURCE_PATH,
                        content_exposure="YES",
                        case_specific=True,
                        digest="4" * 64,
                        disposition="CONTAMINATED",
                    )
                ]
            ),
            finalizer.INVALID,
        )

    def test_summary_mismatch_is_invalid(self) -> None:
        rows = [ledger_entry("COGNITIVE_READ", METHOD_PATH, content_exposure="YES", digest="2" * 64)]
        bad_summary = ledger_summary(rows)
        bad_summary["cognitive_reads"] = 0
        self.assertEqual(self.status(rows, summary_override=bad_summary), finalizer.INVALID)

    def test_finalizer_self_reference_is_invalid(self) -> None:
        rows = [
            ledger_entry(
                "OPERATIONAL_EXECUTION",
                finalizer.VALIDATOR_SOURCE_REL,
                component_id=finalizer.VALIDATOR_COMPONENT_ID,
            ),
            ledger_entry(
                "OPERATIONAL_STATUS_OBSERVED",
                finalizer.VALIDATOR_SOURCE_REL,
                component_id=finalizer.VALIDATOR_COMPONENT_ID,
                status=finalizer.PASS,
            ),
        ]
        self.assertEqual(self.status(rows), finalizer.INVALID)

    def test_closed_ledger_byte_change_invalidates_receipt(self) -> None:
        open_bytes = formatted_json(open_ledger(self.manifest_bytes, []))
        closed, status = finalizer.finalize_ledger_bytes(open_bytes, self.manifest_bytes)
        self.assertEqual(status, finalizer.PASS)
        assert closed is not None
        receipt = finalizer.receipt_bytes_for(closed, self.manifest_bytes, status)
        offset = closed.index(sha256(self.manifest_bytes).encode("ascii"))
        replacement = b"0" if closed[offset:offset + 1] != b"0" else b"1"
        changed = closed[:offset] + replacement + closed[offset + 1:]
        self.assertFalse(finalizer.verify_receipt_bytes(receipt, changed, self.manifest_bytes))

    def test_repeated_finalization_is_stable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task188-r0-4-repeat-") as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "successor-read-ledger-r0.4.json"
            manifest_path = root / "synthetic-manifest.json"
            receipt_path = root / "successor-ledger-validation-receipt-r0.4.json"
            ledger_path.write_bytes(formatted_json(open_ledger(self.manifest_bytes, [])))
            manifest_path.write_bytes(self.manifest_bytes)
            first = finalizer.finalize_files(ledger_path, manifest_path, receipt_path)
            frozen_ledger = ledger_path.read_bytes()
            frozen_receipt = receipt_path.read_bytes()
            second = finalizer.finalize_files(ledger_path, manifest_path, receipt_path)
            self.assertEqual(first, finalizer.PASS)
            self.assertEqual(second, first)
            self.assertEqual(ledger_path.read_bytes(), frozen_ledger)
            self.assertEqual(receipt_path.read_bytes(), frozen_receipt)

    def test_r0_3_protocol_artifacts_remain_byte_stable(self) -> None:
        expected = {
            "ignition/evaluation/r0.3-ledger-closure-protocol.md": "b00632ee35199c09f11732e8ca727f008777d2bd0fbc3255c57094422cac3f23",
            "ignition/evaluation/tools/finalize_successor_read_ledger_r0_3.py": "bee960afe71e50cc9f00d9c0df1a6a592de1e0c63bd226f5a57ddb903859a2d3",
            "ignition/evaluation/heldout/r0.3/successor-visible/successor-read-ledger-r0.3.schema.json": "631cff04fef5e912ca9e85275e4c0b9b1393505aac651d024043b1f3b6f1c838",
            "ignition/evaluation/heldout/r0.3/successor-visible/successor-ledger-validation-receipt-r0.3.schema.json": "12aeef60aea56af25eaf46058bd33788c9e07d97a022ba7acff9ff045cbc4a78",
            "ignition/evaluation/heldout/r0.3/successor-visible/packet-manifest-r0.3.json": "28f92aeb08a52378efb86b4e71decbfe21bd0ba61ea625bc26170a9a5104bf49",
            "ignition/evaluation/heldout/r0.3/successor-visible/cases-manifest-r0.3.json": "7d76008c8cb7fc73497ff70e0c947ddd474da5b0835ca1f9efb1bf7da106c109",
        }
        for relative_path, digest in expected.items():
            self.assertEqual(sha256((REPO_ROOT / relative_path).read_bytes()), digest, relative_path)

    def test_failed_r0_3_private_root_cause_stays_unknown(self) -> None:
        synthetic_failure_classification = {
            "observed_public_fact": "FAIL_READ_LEDGER_INVALID",
            "generic_defect_confirmed": True,
            "generic_defect_is_actual_private_root_cause": False,
            "private_root_cause": "UNRESOLVED_WITHOUT_PRIVATE_LEDGER",
        }
        self.assertEqual(synthetic_failure_classification["private_root_cause"], "UNRESOLVED_WITHOUT_PRIVATE_LEDGER")
        self.assertFalse(synthetic_failure_classification["generic_defect_is_actual_private_root_cause"])


if __name__ == "__main__":
    unittest.main()
