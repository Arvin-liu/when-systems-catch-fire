from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any

IGNITION_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(IGNITION_ROOT))

from evaluation.tools import finalize_successor_read_ledger_r0_3 as r0_3_finalizer  # noqa: E402


COMPONENT_ID = "synthetic-branch-guard"
COMPONENT_PATH = "synthetic/branch-guard.py"
METHOD_PATH = "synthetic/method.md"
CASE_PATH = "synthetic/held-out-case.md"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def formatted_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def synthetic_manifest() -> dict[str, Any]:
    validator = {
        "component_id": r0_3_finalizer.VALIDATOR_COMPONENT_ID,
        "path": r0_3_finalizer.VALIDATOR_SOURCE_REL,
        "source_sha256": sha256(r0_3_finalizer.SOURCE_PATH.read_bytes()),
        "evidence_scope": "FINAL_ATTESTATION_SURFACE",
        "successor_access": "EXECUTE_STATUS_ONLY",
        "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
        "allowed_status_codes": list(r0_3_finalizer.STATUS_CODES),
    }
    return {
        "schema_version": r0_3_finalizer.MANIFEST_SCHEMA_VERSION,
        "manifest_path": r0_3_finalizer.MANIFEST_REL,
        "task_id": r0_3_finalizer.TASK_ID,
        "cognitive_evidence_surface": {
            "files": [
                {"path": METHOD_PATH, "sha256": "2" * 64},
                {"path": CASE_PATH, "sha256": "4" * 64},
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
                    "allowed_status_codes": ["PASS_BRANCH_AUTHORIZED"],
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
        "purpose": "synthetic R0.3 case-exposure reproduction",
        "content_exposure": content_exposure,
        "case_specific_information_exposed": case_specific,
        "digest": digest,
        "observed_status_code": status,
        "contamination_disposition": disposition,
    }


def open_ledger(manifest_bytes: bytes, entries: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "cognitive_reads": sum(row["action_kind"] == "COGNITIVE_READ" for row in entries),
        "operational_executions": sum(row["action_kind"] == "OPERATIONAL_EXECUTION" for row in entries),
        "operational_status_observations": sum(
            row["action_kind"] == "OPERATIONAL_STATUS_OBSERVED" for row in entries
        ),
        "prohibited_cognitive_reads": sum(
            row["action_kind"] == "PROHIBITED_COGNITIVE_READ" for row in entries
        ),
        "contaminated_entries": sum(row["contamination_disposition"] == "CONTAMINATED" for row in entries),
    }
    return {
        "schema_version": r0_3_finalizer.LEDGER_SCHEMA_VERSION,
        "task_id": r0_3_finalizer.TASK_ID,
        "manifest_path": r0_3_finalizer.MANIFEST_REL,
        "manifest_sha256": sha256(manifest_bytes),
        "ledger_state": "OPEN",
        "entries": entries,
        "summary": summary,
        "trial_disposition": "PROTOCOL_CONTAMINATED" if summary["contaminated_entries"] else "CLEAN",
        "closure": None,
    }


class Task188Step00ReproductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_bytes = formatted_json(synthetic_manifest())

    def status(self, entries: list[dict[str, Any]]) -> str:
        return r0_3_finalizer.finalize_ledger_bytes(
            formatted_json(open_ledger(self.manifest_bytes, entries)),
            self.manifest_bytes,
        )[1]

    def test_allowlisted_cognitive_non_case_is_clean(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "COGNITIVE_READ",
                        METHOD_PATH,
                        content_exposure="YES",
                        digest="2" * 64,
                    )
                ]
            ),
            r0_3_finalizer.PASS,
        )

    def test_allowlisted_case_read_marked_clean_is_invalid(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "COGNITIVE_READ",
                        CASE_PATH,
                        content_exposure="YES",
                        case_specific=True,
                        digest="4" * 64,
                    )
                ]
            ),
            r0_3_finalizer.INVALID,
        )

    def test_forcing_the_same_case_read_to_contaminated_exposes_overbroad_rule(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "COGNITIVE_READ",
                        CASE_PATH,
                        content_exposure="YES",
                        case_specific=True,
                        digest="4" * 64,
                        disposition="CONTAMINATED",
                    )
                ]
            ),
            r0_3_finalizer.CONTAMINATED,
        )

    def test_operational_status_case_specific_content_is_contaminated(self) -> None:
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
            r0_3_finalizer.CONTAMINATED,
        )

    def test_unlisted_cognitive_read_is_contaminated(self) -> None:
        self.assertEqual(
            self.status(
                [
                    ledger_entry(
                        "COGNITIVE_READ",
                        "synthetic/unlisted.md",
                        content_exposure="YES",
                        digest="3" * 64,
                        disposition="CONTAMINATED",
                    )
                ]
            ),
            r0_3_finalizer.CONTAMINATED,
        )


if __name__ == "__main__":
    unittest.main()
