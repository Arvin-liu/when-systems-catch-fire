#!/usr/bin/env python3
"""Run the independent completion/non-inference fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/completion-contract-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-completion-contract-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, CompletionContract, GoalRecord, evaluate_completion  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    contract = CompletionContract(**document["contract"])
    goal = GoalRecord("goal-completion-fixture", "intent-completion-fixture", "Independent completion", "fixture.public", contract.contract_id, AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-1", "synthetic", authorized=True), "ACTIVE", 1, None, NOW, NOW)
    validator = AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "validator.synthetic", "validator-1", "validator receipt")
    cases = {
        "run-pass-only": ({"run_pass": True}, validator),
        "missing-predicate": ({"evidence_types": ["VALIDATOR_RECEIPT"], "predicate_results": {}}, validator),
        "forbidden-shortcut": ({"evidence_types": ["VALIDATOR_RECEIPT"], "predicate_results": {"independent_validator_receipt_present": True}, "shortcut_flags": ["run_pass"]}, validator),
        "independent-validator": ({"evidence_types": ["VALIDATOR_RECEIPT"], "evidence_refs": ["receipt-fixture"], "predicate_results": {"independent_validator_receipt_present": True}}, validator),
    }
    for case in document["cases"]:
        decision = evaluate_completion(goal, contract, cases[case["id"]][0], authority=cases[case["id"]][1], decided_at=NOW)
        if decision.outcome != case["expected_outcome"]:
            errors.append(f"{case['id']} expected {case['expected_outcome']} got {decision.outcome}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_COMPLETION_INVALID")
        for error in errors: print(f"- {error}")
        return 1
    print("STEERING_COMPLETION_OK cases=4 run_pass_non_inference=PASS independent_validator=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
