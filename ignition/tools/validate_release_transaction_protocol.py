#!/usr/bin/env python3
"""Validate the ordered release transaction protocol and self-witness boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
PROTOCOL_PATH = ROOT / "data/operations/release-transaction-protocol-r2.json"
SCHEMA_PATH = ROOT / "schemas/operations/release-transaction-protocol-r2.schema.json"
EXPECTED_STEPS = [
    "candidate",
    "task-branch-remote-check",
    "pre-publication-gates",
    "candidate-ref-simulation",
    "ordinary-main-fast-forward",
    "fresh-main-checkout",
    "remote-ref-witness",
    "current-semantic-recheck",
    "receipt-1111-witness",
    "final-marker",
]
EXPECTED_HARD_GATES = [
    "deterministic_projection_preflight",
    "current_path_manifest_exact",
    "residual_non_growth",
    "current_semantic_gates",
    "canonical_full_suite",
    "exact_candidate_sha_binding",
    "no_post_suite_tracked_mutation",
    "task_ordinal_binding",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    protocol = document if document is not None else load_json(PROTOCOL_PATH)
    schema_errors = sorted(Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(protocol), key=lambda error: list(error.path))
    errors = [f"{error.json_path}: {error.message}" for error in schema_errors]
    if errors:
        return errors
    steps = sorted(protocol["steps"], key=lambda step: step["sequence"])
    if [step["step_id"] for step in steps] != EXPECTED_STEPS:
        errors.append("release transaction step order does not match Step 1 through Step 10")
    if [step["sequence"] for step in steps] != list(range(1, 11)):
        errors.append("release transaction sequences must be exactly 1 through 10")
    main_step = next(step for step in steps if step["step_id"] == "ordinary-main-fast-forward")
    if main_step["creates_formal_commit"]:
        errors.append("ordinary main fast-forward must not create a new commit")
    witness_step = next(step for step in steps if step["step_id"] == "receipt-1111-witness")
    if witness_step["creates_formal_commit"]:
        errors.append("1111 receipt witness must not create a formal commit")
    if not witness_step["writes_receipt"]:
        errors.append("1111 receipt witness must write a receipt")
    final_step = next(step for step in steps if step["step_id"] == "final-marker")
    if final_step["action"].find("1111_RELAY_UPDATED") < 0:
        errors.append("final marker step must name 1111_RELAY_UPDATED")
    if protocol["main_mutation_policy"]["mode"] != "ORDINARY_FAST_FORWARD_ONLY":
        errors.append("main mutation policy is not ordinary fast-forward only")
    hard_gates = protocol.get("pre_publication_hard_gates", {})
    if hard_gates.get("contract_id") != "FULL_REGRESSION_RELEASE_HARD_GATE_R1":
        errors.append("pre-publication hard-gate contract id is missing or incorrect")
    if hard_gates.get("required_gate_ids") != EXPECTED_HARD_GATES:
        errors.append("pre-publication hard-gate set/order is incomplete")
    if hard_gates.get("fail_closed") is not True:
        errors.append("pre-publication hard gates must fail closed")
    suite = hard_gates.get("canonical_full_suite", {})
    expected_suite = {
        "required_runs": 2,
        "minimum_natural_window_seconds": 14400,
        "zero_failures_errors_skips": True,
        "clean_before_after": True,
        "exact_candidate_sha": True,
        "no_watchdog": True,
    }
    if suite != expected_suite:
        errors.append("canonical full-suite hard-gate contract is incomplete")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--transition-receipt", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--repository-owner-id", type=int)
    parser.add_argument("--transaction-record", type=Path)
    parser.add_argument("--expected-context", type=Path)
    parser.add_argument("--phase", choices=["prepublication", "postpublication"])
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")

    transition_arguments = (args.transition_receipt, args.observations, args.repository_owner_id)
    has_transition = any(value is not None for value in transition_arguments)
    if has_transition or args.transaction_record or args.expected_context or args.phase:
        if has_transition and not all(value is not None for value in transition_arguments):
            parser.error("transition selection requires --transition-receipt, --observations and --repository-owner-id")
        if args.transaction_record and (not args.expected_context or not args.phase):
            parser.error("--transaction-record requires --expected-context and --phase")
        if args.phase and not args.transaction_record:
            parser.error("--phase requires --transaction-record")
        try:
            from tools import validate_release_transaction_protocol_r3 as protocol_r3
        except ModuleNotFoundError:  # direct `python tools/...py` invocation
            import validate_release_transaction_protocol_r3 as protocol_r3

        contract_errors = protocol_r3.validate_contract()
        if contract_errors:
            print("RELEASE_TRANSACTION_PROTOCOL_R3_INVALID", file=sys.stderr)
            for error in contract_errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        active = "R2"
        activation_errors = ["no independent R3 transition receipt was supplied"]
        if has_transition:
            active, activation_errors = protocol_r3.resolve_effective_protocol(
                load_json(args.transition_receipt),
                observations=load_json(args.observations),
                repository_owner_id=args.repository_owner_id,
            )
        if args.transaction_record:
            if args.phase == "postpublication" and active != "R3":
                print("RELEASE_TRANSACTION_R3_RECORD_REJECTED: R2 remains effective", file=sys.stderr)
                for error in activation_errors:
                    print(f"- {error}", file=sys.stderr)
                return 2
            errors = protocol_r3.validate_transaction_record(
                load_json(args.transaction_record),
                phase=args.phase,
                expected=load_json(args.expected_context),
            )
            if errors:
                print("RELEASE_TRANSACTION_R3_RECORD_INVALID", file=sys.stderr)
                for error in errors:
                    print(f"- {error}", file=sys.stderr)
                return 1
            if args.phase == "prepublication":
                print(f"RELEASE_TRANSACTION_R3_PREFLIGHT_OK current={active}")
            else:
                print("RELEASE_TRANSACTION_R3_RECORD_OK phase=postpublication")
            return 0
        print(f"RELEASE_TRANSACTION_PROTOCOL_{active}_CURRENT")
        return 0

    errors = validate()
    if errors:
        print("RELEASE_TRANSACTION_PROTOCOL_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"RELEASE_TRANSACTION_PROTOCOL_OK path={relative(PROTOCOL_PATH)} steps=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
