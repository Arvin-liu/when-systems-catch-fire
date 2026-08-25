from __future__ import annotations

import copy
import unittest

from agent_federation.live_attempt_ledger import LiveAttemptLedger
from agent_federation.live_reconciliation import LiveReconciliationError, derive_reconciliation_state, validate_reconciliation_state


class LiveReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        self.records = LiveAttemptLedger(root / "ignition/data/operations/iterations/139/live-attempt-ledger.jsonl").records()

    def audit(self, index: int, *, recovery: str, observation: str, reason: str) -> dict:
        record = self.records[index]
        return {
            "task_id": record["task_id"],
            "attempt_id": record["attempt_id"],
            "prior_record_hash": record["record_hash"],
            "prior_process_state": record["process"]["state"],
            "process_observation": observation,
            "evidence_recovery_status": recovery,
            "evidence_refs": [f"ignition/data/operations/iterations/139/source-{index}.json"],
            "terminal_reason": reason,
        }

    def test_terminal_effect_unknown_retains_unknown(self) -> None:
        state = derive_reconciliation_state(self.audit(0, recovery="EXHAUSTED", observation="UNKNOWN", reason="timeout evidence cannot be recovered"))
        self.assertEqual(state["reconciliation_status"], "TERMINAL_UNRECOVERABLE_EFFECT_UNKNOWN")
        self.assertEqual(state["external_effect_knowledge"], "UNKNOWN")
        self.assertFalse(state["validated_completion_eligible"])
        self.assertEqual(validate_reconciliation_state(state)["state_digest"], state["state_digest"])

    def test_terminal_observation_incomplete_retains_unknown(self) -> None:
        state = derive_reconciliation_state(self.audit(3, recovery="EXHAUSTED", observation="LIVE_PROCESS_OBSERVED_OUTCOME_UNKNOWN", reason="capture and structured result cannot be recovered"))
        self.assertEqual(state["reconciliation_status"], "TERMINAL_UNRECOVERABLE_OBSERVATION_INCOMPLETE")
        self.assertEqual(state["external_effect_knowledge"], "UNKNOWN")

    def test_no_live_dispatch_is_a_process_boundary_not_no_effect_claim(self) -> None:
        state = derive_reconciliation_state(self.audit(4, recovery="CONCLUSIVE", observation="NO_LIVE_PROCESS_OBSERVED", reason="public probe and transport audit prove live dispatch count zero"))
        self.assertEqual(state["reconciliation_status"], "CLOSED_NO_LIVE_DISPATCH")
        self.assertEqual(state["process_observation"], "NO_LIVE_PROCESS_OBSERVED")
        self.assertEqual(state["external_effect_knowledge"], "UNKNOWN")

    def test_recoverable_evidence_remains_open(self) -> None:
        state = derive_reconciliation_state(self.audit(3, recovery="RECOVERABLE", observation="UNKNOWN", reason="durable capture source still available"))
        self.assertEqual(state["reconciliation_status"], "OPEN_REQUIRES_EVIDENCE")
        self.assertFalse(state["evidence_exhausted"])

    def test_terminal_state_cannot_be_upgraded(self) -> None:
        state = derive_reconciliation_state(self.audit(0, recovery="EXHAUSTED", observation="UNKNOWN", reason="irrecoverable timeout"))
        tampered = copy.deepcopy(state)
        tampered["external_effect_knowledge"] = "KNOWN_NO_EXTERNAL_EFFECT"
        tampered["state_digest"] = state["state_digest"]
        with self.assertRaises(LiveReconciliationError):
            validate_reconciliation_state(tampered)
        tampered = copy.deepcopy(state)
        tampered["validated_completion_eligible"] = True
        tampered["state_digest"] = state["state_digest"]
        with self.assertRaises(LiveReconciliationError):
            validate_reconciliation_state(tampered)


if __name__ == "__main__":
    unittest.main()
