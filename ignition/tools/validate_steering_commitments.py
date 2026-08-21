#!/usr/bin/env python3
"""Validate explicit authority for Commitment/Obligation transitions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/commitment-ledger-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-commitment-ledger-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, CommitmentLedger, CommitmentLedgerError  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    ledger = CommitmentLedger.from_dict(document)
    proposed = ledger.get("commitment-synthetic-deadline")
    agent = AuthorityProvenance("EXTERNAL_REQUESTED_PROPOSAL", "executor.synthetic", "exec-1", "executor suggestion")
    owner = AuthorityProvenance("OWNER_APPROVED_DERIVED", "owner.synthetic", "auth-commitment-001", "explicit acceptance", authorized=True)
    try:
        ledger.accept(proposed.commitment_id, authority=agent, reason="self accept", accepted_at=NOW)
    except CommitmentLedgerError:
        pass
    else:
        errors.append("executor self-accepted commitment")
    accepted = ledger.accept(proposed.commitment_id, authority=owner, reason="Owner explicitly accepts synthetic obligation", accepted_at=NOW)
    ledger.activate(accepted.commitment_id, authority=owner, reason="begin bounded fulfillment", updated_at=NOW)
    ledger.fulfill(accepted.commitment_id, authority=owner, evidence_refs=("validator-receipt-commitment",), reason="synthetic fulfillment receipt", fulfilled_at=NOW)
    if ledger.get(accepted.commitment_id).status != "FULFILLED":
        errors.append("commitment did not reach FULFILLED")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_COMMITMENT_LEDGER_INVALID")
        for error in errors: print(f"- {error}")
        return 1
    print("STEERING_COMMITMENT_LEDGER_OK self_acceptance=FAIL_CLOSED owner_accept=PASS fulfill=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
