#!/usr/bin/env python3
"""Validate memory/profile advisory and proposal-only boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-memory-profile-boundary-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-memory-profile-boundary-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, ContextBoundaryDecision, IntentRecord, MemoryProfileBoundary, MemoryProfileObservation  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-memory-owner", "canonical synthetic intent", authorized=True)
    canonical = IntentRecord("canonical-intent-1", "Canonical synthetic direction", "owner.synthetic", owner, status="ACTIVE", created_at=NOW, updated_at=NOW)
    boundary = MemoryProfileBoundary()
    for row in document["cases"]:
        observation = MemoryProfileObservation(row["observation_id"], row["source_kind"], row["summary"], row["preference_signal"], row["repeated_preference"], row["stale"], row["conflict_with_canonical"], NOW)
        decision = boundary.evaluate(observation, canonical_intent=canonical if row["canonical_mode"] == "OWNER" else None)
        if decision.decision != row["expected_decision"]:
            errors.append(f"{row['observation_id']} decision={decision.decision} expected={row['expected_decision']}")
        if decision.priority_effect != row["expected_priority_effect"]:
            errors.append(f"{row['observation_id']} priority effect mismatch")
        if row["expected_decision"] == "PROPOSAL_ONLY" and (decision.proposal is None or decision.proposal.owner_authoritative or decision.proposal.status != "PROPOSED"):
            errors.append(f"{row['observation_id']} proposal crossed authority boundary")
        if row["expected_decision"] == "CANONICAL_INTENT_WINS" and decision.canonical_intent_id != canonical.intent_id:
            errors.append(f"{row['observation_id']} canonical intent was not retained")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_MEMORY_PROFILE_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_MEMORY_PROFILE_OK cases=5 repeated=PROPOSAL_ONLY esi=ADVISORY_ONLY stale_canonical=CANONICAL_WINS priority_effect=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
