#!/usr/bin/env python3
"""Validate the synthetic Intent Registry contract for IGNITION-129."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/intent-registry-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-intent-registry-r1.schema.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import IntentRegistry, SteeringValidationError  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    registry = IntentRegistry.from_dict(document)
    if registry.to_dict()["record_count"] != len(registry.records):
        errors.append("record_count mismatch")
    if registry.to_dict()["owner_authoritative_count"] != 1:
        errors.append("fixture must contain exactly one Owner-authoritative intent")
    if registry.to_dict()["proposal_count"] != 1:
        errors.append("fixture must contain exactly one proposal")
    try:
        registry.transition("intent-synthetic-proposal", "ACTIVE", provenance=registry.get("intent-synthetic-proposal").provenance, reason="invalid promotion", updated_at="2026-08-21T12:00:00+08:00")
    except SteeringValidationError:
        pass
    else:
        errors.append("proposal promotion was not rejected")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_INTENT_REGISTRY_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_INTENT_REGISTRY_OK records=2 owner=1 proposals=1 proposal_promotion=FAIL_CLOSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
