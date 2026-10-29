from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_compare_evidence_update_snapshots as tool  # noqa: E402


FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-evidence-update-snapshot-comparison/valid-input-r0.json"
INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-evidence-update-snapshot-comparison-input-r0.schema.json"
OUTPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-evidence-update-snapshot-comparison-output-r0.schema.json"


class EvidenceUpdateSnapshotComparatorTests(unittest.TestCase):
    def request(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def analyze(self, request: dict) -> dict:
        raw = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return tool.analyze_bytes(raw)

    def test_schema_and_matched_update_report_structural_deltas_only(self) -> None:
        request = self.request()
        input_schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(input_schema).iter_errors(request)), [])

        result = self.analyze(request)

        self.assertEqual(result["status"], "UPDATE_DELTA_REPORTED")
        self.assertEqual(result["comparison_status"], "COMPARABLE_AS_DECLARED")
        self.assertEqual(result["evidence_delta"]["added_ids"], ["EVIDENCE-004"])
        self.assertEqual(result["evidence_delta"]["absent_from_candidate_ids"], ["EVIDENCE-005"])
        self.assertEqual(result["evidence_delta"]["retained_exact_ids"], ["EVIDENCE-001", "EVIDENCE-002"])
        self.assertEqual(result["evidence_delta"]["changed_records"][0]["evidence_id"], "EVIDENCE-003")
        self.assertEqual(result["evidence_delta"]["declared_withdrawal_or_retraction_transitions"], [
            {"evidence_id": "EVIDENCE-003", "before_state": "LINKED", "after_state": "WITHDRAWN"}
        ])
        self.assertEqual(result["declared_claim_state_delta"]["before"], "OPEN")
        self.assertEqual(result["declared_claim_state_delta"]["after"], "CONTESTED")
        self.assertIn("ACCUMULATION_BIAS_REVIEW_NOT_EVALUATED", result["review_triggers"])
        self.assertEqual(result["claim_truth"], "NOT_ADJUDICATED")
        self.assertEqual(result["evidence_quality"], "NOT_ASSESSED")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(list(Draft202012Validator(output_schema).iter_errors(result)), [])

    def test_explicit_no_change_is_distinguished_from_missing_metadata(self) -> None:
        request = self.request()
        baseline = copy.deepcopy(request["baseline_snapshot"])
        successor = copy.deepcopy(baseline)
        successor["snapshot_id"] = "snapshot-2026-10-02"
        successor["as_of"] = {"reference": "snapshot:successor", "observed_at_utc": "2026-10-02T00:00:00Z"}
        successor["change_reason"] = {"code": "NO_CHANGE_RECORDED", "reference": "task:claim-update-review-001"}
        baseline["acquisition_dependence"] = successor["acquisition_dependence"] = "INDEPENDENT"
        request["baseline_snapshot"] = baseline
        request["candidate_snapshot"] = successor

        result = self.analyze(request)

        self.assertEqual(result["status"], "EXPLICIT_NO_CHANGE")
        self.assertEqual(result["comparison_status"], "COMPARABLE_AS_DECLARED")
        self.assertEqual(result["evidence_delta"]["added_ids"], [])
        self.assertEqual(result["evidence_delta"]["absent_from_candidate_ids"], [])

        successor["evidence_items"][0]["record_sha256"] = None
        request["candidate_snapshot"] = successor
        unknown = self.analyze(request)
        self.assertEqual(unknown["status"], "NO_CHANGE_NOT_ESTABLISHED")
        self.assertEqual(unknown["comparison_status"], "COMPARISON_UNKNOWN")

    def test_scope_and_evaluator_drift_are_reported_as_unknown_not_hidden(self) -> None:
        request = self.request()
        request["candidate_snapshot"]["scope_digest"] = "d" * 64
        request["candidate_snapshot"]["evaluation_instrument"]["revision_digest"] = "e" * 64

        result = self.analyze(request)

        self.assertEqual(result["comparison_status"], "COMPARISON_UNKNOWN")
        self.assertTrue(result["scope_delta"]["changed"])
        self.assertIn("SCOPE_CHANGED_OR_UNKNOWN", result["comparison_unknown_reasons"])
        self.assertIn("EVALUATION_INSTRUMENT_CHANGED_OR_UNKNOWN", result["comparison_unknown_reasons"])

    def test_task_or_claim_mismatch_and_reversed_time_fail_closed(self) -> None:
        request = self.request()
        request["candidate_snapshot"]["task_ref"]["task_id"] = "different-task"
        result = self.analyze(request)
        self.assertEqual(result["status"], "INPUT_INVALID")
        self.assertEqual(result["errors"][0]["code"], "TASK_BINDING_MISMATCH")

        request = self.request()
        request["candidate_snapshot"]["claim_id"] = "CLAIM-OTHER"
        self.assertEqual(self.analyze(request)["errors"][0]["code"], "CLAIM_BINDING_MISMATCH")

        request = self.request()
        request["candidate_snapshot"]["as_of"]["observed_at_utc"] = "2026-09-30T00:00:00Z"
        self.assertEqual(self.analyze(request)["errors"][0]["code"], "CANDIDATE_AS_OF_NOT_LATER")

    def test_duplicate_evidence_ids_unknown_fields_and_bad_digests_are_rejected(self) -> None:
        request = self.request()
        request["candidate_snapshot"]["evidence_items"].append(copy.deepcopy(request["candidate_snapshot"]["evidence_items"][0]))
        self.assertEqual(self.analyze(request)["errors"][0]["code"], "DUPLICATE_EVIDENCE_ID")

        request = self.request()
        request["candidate_snapshot"]["scientific_verdict"] = "PASS"
        self.assertEqual(self.analyze(request)["errors"][0]["code"], "UNKNOWN_FIELD")

        request = self.request()
        request["candidate_snapshot"]["scope_digest"] = "not-a-sha256"
        self.assertEqual(self.analyze(request)["errors"][0]["code"], "SHA256_INVALID")

    def test_duplicate_json_keys_nonstandard_numbers_and_oversize_input_are_rejected(self) -> None:
        duplicate = tool.analyze_bytes(b'{"schema_version":"bad","schema_version":"bad"}')
        self.assertEqual(duplicate["status"], "INPUT_INVALID")
        self.assertEqual(duplicate["errors"][0]["code"], "DUPLICATE_JSON_KEY")

        nonstandard = tool.analyze_bytes(b'{"value":NaN}')
        self.assertEqual(nonstandard["errors"][0]["code"], "NONSTANDARD_JSON_NUMBER")

        oversized = tool.analyze_bytes(b" " * (tool.MAX_INPUT_BYTES + 1))
        self.assertEqual(oversized["errors"][0]["code"], "INPUT_LIMIT_EXCEEDED")

    def test_cli_is_deterministic_and_does_not_echo_source_or_reason_text(self) -> None:
        command = [sys.executable, str(IGNITION_ROOT / "tools/toolbox_compare_evidence_update_snapshots.py"), "--stdin"]
        payload = FIXTURE.read_bytes()
        first = subprocess.run(command, input=payload, capture_output=True, check=False)
        second = subprocess.run(command, input=payload, capture_output=True, check=False)

        self.assertEqual(first.returncode, 0, first.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(first.stdout, second.stdout)
        self.assertNotIn(b"secret source excerpt", first.stdout)
        self.assertLessEqual(len(first.stdout), tool.MAX_OUTPUT_BYTES)
        self.assertEqual(json.loads(first.stdout)["input_sha256"], hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    unittest.main()
