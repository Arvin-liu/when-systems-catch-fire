#!/usr/bin/env python3
"""Validate the provider-neutral soft-context exposure contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_soft_governance_authority import scan_runtime_sources


DEFAULT_CONTRACT = ROOT / "data/agent-federation/soft-context-exposure-contract-r0.json"
DEFAULT_SCHEMA = ROOT / "schemas/agent-federation/soft-context-exposure-contract-r0.schema.json"


def validate(contract: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(contract)]
    capsule = contract.get("handoff_capsule", {})
    expected_none = ("capability_delta", "permission_delta", "authorization_delta", "truth_status_delta", "owner_status_delta", "epistemic_acceptance_delta", "external_side_effect_delta")
    for field in expected_none:
        if capsule.get(field) != "NONE":
            errors.append(f"handoff capsule {field} must remain NONE")
    prohibited = set(contract.get("exposure_event", {}).get("prohibited_fields", []))
    required_prohibited = {"hidden_reasoning", "vendor_session_state", "secret_or_credential", "permission_delta", "authorization_delta"}
    if not required_prohibited <= prohibited:
        errors.append("exposure event does not prohibit private or authority-bearing fields")
    if "data/epistemic-governance/soft-governance-non-authority-invariant-r0.json" not in capsule.get("hard_gate_refs", []):
        errors.append("handoff capsule must reference the soft non-authority invariant")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--skip-runtime-scan", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = validate(contract, schema)
    if not args.skip_runtime_scan:
        errors.extend(scan_runtime_sources())
    if errors:
        print("FAIL")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    print(f"SOFT_CONTEXT_EXPOSURE_OK status={contract['status']} runtime_scan={'SKIPPED' if args.skip_runtime_scan else 'PASS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
