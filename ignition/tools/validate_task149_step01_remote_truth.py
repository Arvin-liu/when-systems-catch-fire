#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step01 remote truth and contract gap audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
AUDIT_PATH = ROOT / "data/operations/iterations/149/step01-remote-truth-audit.json"
AUDIT_SCHEMA_PATH = ROOT / "schemas/operations/task149-step01-remote-truth-audit-r0.schema.json"
CONTRACT_PATH = ROOT / "data/operations/iterations/149/step01-provider-contract-boundary-r0.json"
CONTRACT_SCHEMA_PATH = ROOT / "schemas/operations/provider-contract-boundary-r0.schema.json"
EXPECTED_BASELINE = "14c2595d796494286caf31378173fd9dd027edcf"
BOUNDARIES = [
    "EXTERNAL_PROVIDER ≠ IGNITION_AUTHORITY",
    "PROVIDER_CAPABILITY ≠ PERMISSION",
    "PROVIDER_OUTPUT ≠ EXTERNAL_TRUTH",
    "PROVIDER_LOCAL_POLICY ≠ IGNITION_GLOBAL_POLICY",
    "ADAPTER_SPIKE_PASS ≠ CURRENT_CAPABILITY",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(audit: dict[str, Any] | None = None, contract: dict[str, Any] | None = None) -> list[str]:
    audit = audit if audit is not None else load_json(AUDIT_PATH)
    contract = contract if contract is not None else load_json(CONTRACT_PATH)
    errors: list[str] = []
    for label, document, schema_path in (
        ("audit", audit, AUDIT_SCHEMA_PATH),
        ("contract", contract, CONTRACT_SCHEMA_PATH),
    ):
        schema = load_json(schema_path)
        errors.extend(f"{label}{error.json_path}: {error.message}" for error in Draft202012Validator(schema).iter_errors(document))

    if audit.get("formal_remote_observation", {}).get("observed_sha") != EXPECTED_BASELINE:
        errors.append("Step01 baseline must remain the fresh post-Task148 main SHA")
    if audit.get("formal_remote_observation", {}).get("ref") != "refs/heads/main":
        errors.append("Step01 must be bound to refs/heads/main")
    if contract.get("formal_baseline_sha") != EXPECTED_BASELINE:
        errors.append("minimal provider contract must use the Step01 formal baseline")
    if audit.get("authority_boundaries") != BOUNDARIES or contract.get("authority_invariants") != BOUNDARIES:
        errors.append("provider authority boundaries are incomplete or reordered")
    if contract.get("provider_records") != []:
        errors.append("Step01 minimal contract must not contain provider records")

    identity = load_json(ROOT / "data/architecture/current-system-identity.json")
    facts = load_json(ROOT / "data/architecture/current-facts.json")
    registry = load_json(ROOT / "data/operations/ignition-operation-capability-registry-r1.json")
    playbooks = load_json(ROOT / "data/operations/ignition-operation-playbooks-r1.json")
    if identity.get("current_formal_task_id") != "IGNITION-20260829-148":
        errors.append("Current identity no longer proves Task148 as the formal current task")
    if identity.get("current_operating_method", {}).get("identity_marker") != "Identity: `IGNITION_OPERATING_METHOD_R1`":
        errors.append("Current identity does not prove the Operating Method identity")
    if identity.get("current_operating_method", {}).get("status") != "CURRENT":
        errors.append("Operating Method is not Current")
    if facts.get("facts", {}).get("operating_method", {}).get("status") != "CURRENT":
        errors.append("Current Facts does not prove the Operating Method is Current")
    if registry.get("registry_lifecycle", {}).get("current_on_main") is not True:
        errors.append("Capability Registry is not Current on main")
    if len(registry.get("operations", [])) != 19:
        errors.append("unexpected capability operation count")
    if len(playbooks.get("playbooks", [])) != 15 or len(playbooks.get("excluded_status_only", [])) != 4:
        errors.append("unexpected operation playbook projection counts")
    obligations = facts.get("facts", {}).get("open_obligations", {})
    if obligations.get("open_obligation_ids") != ["LIVE_EXTERNAL_INVOCATION"]:
        errors.append("LIVE_EXTERNAL_INVOCATION is not the sole open obligation projection")
    federation = facts.get("facts", {}).get("federation", {})
    if federation.get("live_attempt_projection", {}).get("next_action_status") != "OWNER_DEFERRED":
        errors.append("live external invocation is not still OWNER_DEFERRED")

    for fingerprint in audit.get("source_fingerprints", []):
        path = ROOT.parent / fingerprint["path"]
        if not path.is_file():
            errors.append(f"source fingerprint path missing: {fingerprint['path']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != fingerprint["sha256"]:
            errors.append(f"source fingerprint drift: {fingerprint['path']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP01_REMOTE_TRUTH_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP01_REMOTE_TRUTH_OK baseline=14c2595d796494286caf31378173fd9dd027edcf provider_records=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
