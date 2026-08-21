from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_runtime.steering import AuthorityProvenance, CommitmentLedger, CommitmentLedgerError


NOW = "2026-08-21T12:00:00+08:00"


class CommitmentLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data/operations/iterations/129/fixtures/commitment-ledger-r1.json"
        self.ledger = CommitmentLedger.from_dict(json.loads(path.read_text(encoding="utf-8")))
        self.owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "synthetic", authorized=True)
        self.proposal = AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "system.fixture", "proposal-1", "synthetic")

    def test_commitment_is_distinct_from_goal_and_has_time_fields(self) -> None:
        item = self.ledger.get("commitment-synthetic-deadline")
        self.assertEqual(item.status, "PROPOSED")
        self.assertIsNotNone(item.due_at)
        self.assertNotEqual(item.commitment_id, item.goal_id)

    def test_agent_cannot_self_accept(self) -> None:
        with self.assertRaises(CommitmentLedgerError):
            self.ledger.accept("commitment-synthetic-deadline", authority=self.proposal, reason="self accept", accepted_at=NOW)

    def test_owner_accept_activate_and_fulfill(self) -> None:
        accepted = self.ledger.accept("commitment-synthetic-deadline", authority=self.owner, reason="explicit acceptance", accepted_at=NOW)
        active = self.ledger.activate(accepted.commitment_id, authority=self.owner, reason="start", updated_at=NOW)
        fulfilled = self.ledger.fulfill(active.commitment_id, authority=self.owner, evidence_refs=("receipt-1",), reason="evidence", fulfilled_at=NOW)
        self.assertEqual(fulfilled.status, "FULFILLED")

    def test_fulfillment_needs_evidence(self) -> None:
        accepted = self.ledger.accept("commitment-synthetic-deadline", authority=self.owner, reason="explicit acceptance", accepted_at=NOW)
        with self.assertRaises(CommitmentLedgerError):
            self.ledger.fulfill(accepted.commitment_id, authority=self.owner, evidence_refs=(), reason="no evidence", fulfilled_at=NOW)

    def test_waive_requires_owner(self) -> None:
        with self.assertRaises(CommitmentLedgerError):
            self.ledger.waive("commitment-synthetic-deadline", authority=self.proposal, reason="agent waiver", waived_at=NOW)


if __name__ == "__main__":
    unittest.main()
