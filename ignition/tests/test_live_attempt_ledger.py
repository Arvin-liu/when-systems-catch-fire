from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from agent_federation.live_attempt_ledger import (
    LiveAttemptBindingError,
    LiveAttemptDuplicateError,
    LiveAttemptLedger,
    LiveAttemptLedgerCorruption,
    LiveAttemptLedgerError,
    validate_record,
)


DIGEST = "a" * 64


def record(*, dispatch_id: str = "dispatch-1", attempt_id: str = "attempt-1", state: str = "COMPLETED_VALIDATED", completeness: str = "COMPLETE") -> dict:
    return {
        "task_id": "IGNITION-20260825-139",
        "dispatch_id": dispatch_id,
        "attempt_id": attempt_id,
        "executor_id": "external.synthetic",
        "adapter_id": "synthetic-live-r1",
        "executor_version": "1.0",
        "capability_lease_digest": DIGEST,
        "lease_binding_status": "BOUND",
        "workspace_ref": "fixture://ignition-139",
        "workspace_digest_before": DIGEST,
        "workspace_digest_after": DIGEST,
        "runtime_scratch_lifecycle_digest": DIGEST,
        "started_at": "2026-08-25T00:00:00Z",
        "ended_at": "2026-08-25T00:00:01Z",
        "process": {
            "state": state,
            "return_code": 0,
            "timed_out": False,
            "signal": None,
            "cleanup_status": "CLEANED",
            "process_group_status": "CONFIRMED_GONE",
        },
        "public_events": {
            "capture_ref": "capture://attempt-1",
            "capture_digest": DIGEST,
            "event_count": 2,
            "capture_completeness": completeness,
            "stdout_digest": DIGEST,
            "stderr_digest": DIGEST,
            "stdout_byte_count": 10,
            "stderr_byte_count": 0,
        },
        "structured_result": {"present": True, "ref": "result://attempt-1", "digest": DIGEST},
        "validator": {"status": "PASS", "ref": "validator://attempt-1", "digest": DIGEST},
        "reconciliation_status": "NOT_REQUIRED",
        "evidence_completeness": completeness,
        "claim_ceiling": "One bounded synthetic result independently validated; no external truth is inferred.",
        "source_refs": ["ignition/tests/test_live_attempt_ledger.py"],
        "history_classification": "CURRENT_ATTEMPT",
    }


class LiveAttemptLedgerTests(unittest.TestCase):
    def test_append_hash_chain_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = LiveAttemptLedger(Path(directory) / "attempts.jsonl")
            first = ledger.append(record())
            second = ledger.append(record(dispatch_id="dispatch-2", attempt_id="attempt-2"))
            self.assertEqual(first["sequence"], 0)
            self.assertEqual(second["sequence"], 1)
            self.assertEqual(second["previous_record_hash"], first["record_hash"])
            self.assertEqual(ledger.audit()["record_count"], 2)

    def test_duplicate_dispatch_and_attempt_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = LiveAttemptLedger(Path(directory) / "attempts.jsonl")
            ledger.append(record())
            with self.assertRaises(LiveAttemptDuplicateError):
                ledger.append(record(dispatch_id="dispatch-1", attempt_id="attempt-2"))
            with self.assertRaises(LiveAttemptDuplicateError):
                ledger.append(record(dispatch_id="dispatch-2", attempt_id="attempt-1"))

    def test_binding_guards_reject_wrong_task_executor_and_lease(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = LiveAttemptLedger(Path(directory) / "attempts.jsonl")
            with self.assertRaises(LiveAttemptBindingError):
                ledger.append(record(), expected_task_id="IGNITION-20260824-138")
            with self.assertRaises(LiveAttemptBindingError):
                ledger.append(record(), expected_executor_id="external.codex")
            with self.assertRaises(LiveAttemptBindingError):
                ledger.append(record(), expected_lease_digest="b" * 64)

    def test_incomplete_evidence_cannot_claim_success(self) -> None:
        candidate = record(state="OBSERVATION_INCOMPLETE", completeness="INCOMPLETE")
        with self.assertRaises(LiveAttemptLedgerError):
            validate_record(candidate, check_hash=False)
        candidate["structured_result"] = {"present": False, "ref": None, "digest": "UNRECOVERED"}
        candidate["validator"] = {"status": "UNKNOWN", "ref": None, "digest": "UNRECOVERED"}
        candidate["reconciliation_status"] = "REQUIRES_RECONCILIATION"
        candidate.update({
            "schema_version": "live-attempt-ledger-r1",
            "sequence": 0,
            "previous_record_hash": "0" * 64,
            "record_hash": "0" * 64,
        })
        self.assertEqual(validate_record(candidate, check_hash=False)["evidence_completeness"], "INCOMPLETE")

    def test_private_output_is_rejected(self) -> None:
        candidate = record()
        candidate["claim_ceiling"] = "raw_prompt must never be persisted"
        with self.assertRaises(LiveAttemptLedgerError):
            validate_record(candidate, check_hash=False)

    def test_unknown_state_and_hash_tampering_fail_closed(self) -> None:
        candidate = record()
        candidate["process"]["state"] = "NOT_A_STATE"
        with self.assertRaises(LiveAttemptLedgerError):
            validate_record(candidate, check_hash=False)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attempts.jsonl"
            ledger = LiveAttemptLedger(path)
            ledger.append(record())
            raw = path.read_text(encoding="utf-8").replace("external.synthetic", "external.tampered")
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(LiveAttemptLedgerCorruption):
                ledger.audit()


if __name__ == "__main__":
    unittest.main()
