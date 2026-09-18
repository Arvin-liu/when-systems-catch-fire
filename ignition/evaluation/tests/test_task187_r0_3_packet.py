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
PACKET_DIR = IGNITION_ROOT / "evaluation/heldout/r0.3/successor-visible"
sys.path.insert(0, str(IGNITION_ROOT))

from evaluation.tools import finalize_successor_read_ledger_r0_3 as finalizer  # noqa: E402


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_bytes())


def schema_errors(value: Any, schema: dict[str, Any]) -> list[Any]:
    import jsonschema

    jsonschema.Draft202012Validator.check_schema(schema)
    return list(jsonschema.Draft202012Validator(schema).iter_errors(value))


class Task187R03PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packet_manifest_path = PACKET_DIR / "packet-manifest-r0.3.json"
        cls.packet_manifest_bytes = cls.packet_manifest_path.read_bytes()
        cls.packet_manifest = json.loads(cls.packet_manifest_bytes)
        cls.cases_manifest_path = PACKET_DIR / "cases-manifest-r0.3.json"
        cls.cases_manifest_bytes = cls.cases_manifest_path.read_bytes()
        cls.cases_manifest = json.loads(cls.cases_manifest_bytes)

    def test_packet_manifest_schema_hashes_and_surface_separation(self) -> None:
        schema_path = PACKET_DIR / "packet-manifest-r0.3.schema.json"
        schema = read_json(schema_path)
        self.assertEqual(schema_errors(self.packet_manifest, schema), [])
        self.assertEqual(self.packet_manifest["manifest_path"], finalizer.MANIFEST_REL)
        self.assertEqual(self.packet_manifest["task_id"], finalizer.TASK_ID)
        self.assertEqual(
            self.packet_manifest["cases_manifest_sha256"],
            sha256(self.cases_manifest_bytes),
        )

        cognitive_rows = self.packet_manifest["cognitive_evidence_surface"]["files"]
        cognitive_paths = [row["path"] for row in cognitive_rows]
        self.assertEqual(len(cognitive_paths), len(set(cognitive_paths)))
        self.assertNotIn(finalizer.MANIFEST_REL, cognitive_paths)
        excluded = self.packet_manifest["sealed_evidence_surface"]["excluded_path_prefixes"]
        for row in cognitive_rows:
            self.assertFalse(any(row["path"].startswith(prefix) for prefix in excluded), row["path"])
            self.assertEqual(sha256((REPO_ROOT / row["path"]).read_bytes()), row["sha256"], row["path"])

        components = self.packet_manifest["operational_control_surface"]["components"]
        component_ids = [row["component_id"] for row in components]
        component_paths = [row["path"] for row in components]
        self.assertEqual(len(component_ids), len(set(component_ids)))
        self.assertEqual(len(component_paths), len(set(component_paths)))
        self.assertTrue(set(component_paths).isdisjoint(cognitive_paths))
        for row in components:
            self.assertEqual(sha256((REPO_ROOT / row["path"]).read_bytes()), row["source_sha256"], row["path"])
            self.assertEqual(row["successor_access"], "EXECUTE_STATUS_ONLY")
            self.assertEqual(set(row["permitted_actions"]), {"EXECUTE", "OBSERVE_STATUS"})

        finalizer_rows = [row for row in components if row["component_id"] == finalizer.VALIDATOR_COMPONENT_ID]
        self.assertEqual(len(finalizer_rows), 1)
        self.assertEqual(finalizer_rows[0]["evidence_scope"], "FINAL_ATTESTATION_SURFACE")
        self.assertEqual(finalizer_rows[0]["path"], finalizer.VALIDATOR_SOURCE_REL)
        self.assertTrue(set(finalizer.STATUS_CODES).issubset(set(finalizer_rows[0]["allowed_status_codes"])))

        resources = self.packet_manifest["operational_control_surface"]["resources"]
        resource_paths = [row["path"] for row in resources]
        self.assertTrue(set(resource_paths).isdisjoint(cognitive_paths))
        for row in resources:
            self.assertEqual(sha256((REPO_ROOT / row["path"]).read_bytes()), row["sha256"], row["path"])
            self.assertEqual(row["successor_access"], "GUARD_INTERNAL_ONLY")

    def test_two_case_provenance_and_frozen_case_manifest(self) -> None:
        schema = read_json(PACKET_DIR / "cases-manifest-r0.3.schema.json")
        self.assertEqual(schema_errors(self.cases_manifest, schema), [])
        self.assertEqual(self.cases_manifest["case_count"], 2)
        self.assertEqual(
            (PACKET_DIR / "cases-manifest-r0.3.sha256").read_text(encoding="utf-8").strip(),
            f"{sha256(self.cases_manifest_bytes)}  cases-manifest-r0.3.json",
        )
        case_ids = {row["case_id"] for row in self.cases_manifest["cases"]}
        self.assertEqual(case_ids, {"IGNITION-20260918-187-EXP-01", "IGNITION-20260918-187-GOV-01"})
        self.assertEqual(
            {row["category"] for row in self.cases_manifest["cases"]},
            {"CONTENT_EXPERIENCE_RESEARCH", "ENGINEERING_GOVERNANCE"},
        )
        for row in self.cases_manifest["cases"]:
            source = (REPO_ROOT / row["source_path"]).read_bytes()
            provenance_bytes = (REPO_ROOT / row["provenance_path"]).read_bytes()
            provenance = json.loads(provenance_bytes)
            self.assertEqual(sha256(source), row["source_sha256"])
            self.assertEqual(sha256(provenance_bytes), row["provenance_sha256"])
            self.assertEqual(provenance["case_id"], row["case_id"])
            self.assertEqual(provenance["source_sha256"], row["source_sha256"])
            self.assertFalse(provenance["real_personal_data_used"])
            for field in (
                "contains_gold_ir",
                "contains_expected_relations",
                "contains_expected_continuation",
                "contains_evaluator_answer",
            ):
                self.assertFalse(row[field], f"{row['case_id']} {field}")
                self.assertFalse(provenance[field], f"{row['case_id']} {field}")

    def test_output_schema_accepts_two_provider_neutral_responses_only(self) -> None:
        schema = read_json(PACKET_DIR / "successor-output-r0.3.schema.json")
        valid = {
            "schema_version": "successor-output-r0.3",
            "task_id": finalizer.TASK_ID,
            "case_responses": [
                {
                    "case_id": "IGNITION-20260918-187-EXP-01",
                    "account": "synthetic schema fixture placeholder",
                    "uncertainties": [],
                    "additional_evidence_needed": [],
                },
                {
                    "case_id": "IGNITION-20260918-187-GOV-01",
                    "account": "synthetic schema fixture placeholder",
                    "uncertainties": [],
                    "additional_evidence_needed": [],
                },
            ],
        }
        self.assertEqual(schema_errors(valid, schema), [])
        duplicate = json.loads(json.dumps(valid))
        duplicate["case_responses"][1]["case_id"] = duplicate["case_responses"][0]["case_id"]
        self.assertTrue(schema_errors(duplicate, schema))
        extra_evaluation = json.loads(json.dumps(valid))
        extra_evaluation["case_responses"][0]["score"] = 1
        self.assertTrue(schema_errors(extra_evaluation, schema))

    def test_real_packet_manifest_supports_clean_synthetic_closure_and_receipt(self) -> None:
        summary = {
            "cognitive_reads": 0,
            "operational_executions": 0,
            "operational_status_observations": 0,
            "prohibited_cognitive_reads": 0,
            "contaminated_entries": 0,
        }
        ledger = {
            "schema_version": finalizer.LEDGER_SCHEMA_VERSION,
            "task_id": finalizer.TASK_ID,
            "manifest_path": finalizer.MANIFEST_REL,
            "manifest_sha256": sha256(self.packet_manifest_bytes),
            "ledger_state": "OPEN",
            "entries": [],
            "summary": summary,
            "trial_disposition": "CLEAN",
            "closure": None,
        }
        closed, status = finalizer.finalize_ledger_bytes(
            json.dumps(ledger, sort_keys=True, indent=2).encode() + b"\n",
            self.packet_manifest_bytes,
        )
        self.assertEqual(status, finalizer.PASS)
        self.assertIsNotNone(closed)
        assert closed is not None
        receipt = finalizer.receipt_bytes_for(closed, self.packet_manifest_bytes, status)
        self.assertTrue(finalizer.verify_receipt_bytes(receipt, closed, self.packet_manifest_bytes))

    def test_bootstrap_is_syntax_valid_and_returns_only_guard_status(self) -> None:
        path = PACKET_DIR / "bootstrap-r0.3.sh"
        self.assertTrue(path.stat().st_mode & 0o111)
        result = __import__("subprocess").run(["sh", "-n", str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        content = path.read_text(encoding="utf-8")
        self.assertIn("task_branch_guard_r0_3.py", content)
        self.assertNotIn("finalize_successor_read_ledger", content)
        self.assertNotIn("evaluator", content.casefold())


if __name__ == "__main__":
    unittest.main()
