#!/usr/bin/env python3
"""Validate fail-closed objective, authority, memory, and handoff drift checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-drift-guard-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-drift-guard-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, GoalDriftGuard, GoalRecord, sha256_json  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-drift-owner", "synthetic Owner authority", authorized=True)
    guard = GoalDriftGuard()
    for row in document["cases"]:
        source = row["authority_source"]
        provenance = owner if source == "OWNER_DECLARED" else AuthorityProvenance(source, "system.synthetic", f"auth-{row['case_id']}", "synthetic proposal", authorized=False)
        goal = GoalRecord(row["goal_id"], f"intent-{row['case_id']}", f"Synthetic objective {row['case_id']}", "owner.synthetic", f"contract-{row['case_id']}", provenance, status="ACTIVE" if source == "OWNER_DECLARED" else "PROPOSED", created_at=NOW, updated_at=NOW)
        expected_handoff = sha256_json({"handoff": row["case_id"]})
        observed_handoff = expected_handoff if row["handoff_state"] == "MATCH" else sha256_json({"handoff": "mismatch"})
        observed_objective = goal.objective_digest() if row["objective_state"] == "MATCH" else sha256_json({"objective": "drift"})
        observed_provenance = owner if row["observed_owner_authority"] else None
        report = guard.inspect(row["case_id"], goal, observed_objective, row["expected_acceptance"], row["observed_acceptance"], observed_provenance=observed_provenance, superseded_reference=row["superseded_reference"], memory_conflict=row["memory_conflict"], expected_handoff_identity_digest=expected_handoff, observed_handoff_identity_digest=observed_handoff, created_at=NOW)
        if report.outcome != row["expected_outcome"]:
            errors.append(f"{row['case_id']} outcome={report.outcome} expected={row['expected_outcome']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_DRIFT_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_DRIFT_OK cases=6 objective=PAUSE_RECONCILE authority=HUMAN_REVIEW memory=HUMAN_REVIEW handoff=PAUSE_RECONCILE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
