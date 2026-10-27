#!/usr/bin/env python3
"""Validate Ignition-owned Task149 provider-selection authority."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/provider-selection-authority-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/provider-selection-authority-r0.schema.json"

EXPECTED_BASELINE = "c9c385dc713e866fbc8b61823a893a09e3f9f71b"
EXPECTED_CONTRACT_SHA = "9abb57273e34f98271394099a6ecefa250def26992e1f31d83b8824857ca4649"
EXPECTED_KEYS = {
    "explicit_user_provider",
    "current_capability_and_admission",
    "current_environment_availability",
    "operation_fit",
    "least_privilege",
    "least_side_effect",
    "credential_requirement",
    "provenance_and_validation",
    "fallback_allowed",
}
EXPECTED_RESEARCH_SCOPE = "EXPERIMENTAL_PROVIDER_ADMISSION_RESEARCH_ONLY"
EXPECTED_RUNTIME_INTERFACE_STATUS = "NOT_A_CURRENT_RUNTIME_PROVIDER_INTERFACE"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_baseline_sha") != EXPECTED_BASELINE:
        errors.append("selection policy must be based on the published Contract R0 commit")
    if document.get("contract_artifact", {}).get("sha256") != EXPECTED_CONTRACT_SHA:
        errors.append("selection policy must bind the exact Contract R0 artifact")
    if document.get("owner") != "IGNITION":
        errors.append("Ignition must own provider selection")
    if document.get("research_scope") != EXPECTED_RESEARCH_SCOPE:
        errors.append("selection policy must remain experimental provider-admission research only")
    if document.get("runtime_interface_status") != EXPECTED_RUNTIME_INTERFACE_STATUS:
        errors.append("selection policy must not be treated as a Current runtime provider interface")
    keys = {entry.get("key") for entry in document.get("selection_inputs", [])}
    if keys != EXPECTED_KEYS:
        errors.append("all nine required selection inputs must remain present")
    if any(entry.get("ordering") != "CONTEXT_DEPENDENT" for entry in document.get("selection_inputs", [])):
        errors.append("the task must not impose a universal total provider order")
    if document.get("selection_procedure", {}).get("total_order_hardcoded_by_task") is not False:
        errors.append("universal provider total order must remain false")
    local_policy = document.get("provider_local_policy_test", {})
    if local_policy.get("global_inheritance") is not False or local_policy.get("decision") != "REJECTED_PROVIDER_LOCAL_POLICY":
        errors.append("provider-local forced routing must remain rejected as global policy")
    impact = document.get("current_impact", {})
    for key in ("new_operation_registry_entry", "pack_permission_change", "architecture_identity_change"):
        if impact.get(key) is not False:
            errors.append(f"selection authority must not change {key}")
    if impact.get("authenticated_channel_admission") != "NOT_GRANTED":
        errors.append("authenticated channel admission must remain not granted")
    if impact.get("live_external_invocation") != "UNCHANGED_OPEN_OWNER_DEFERRED":
        errors.append("live external invocation must remain unchanged")
    for decision in document.get("candidate_decisions", []):
        if decision.get("current_capability") is not False or decision.get("permission_granted") is not False or decision.get("authenticated_channel_admitted") is not False:
            errors.append(f"candidate {decision.get('provider_id')} widened a capability, permission or auth state")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_PROVIDER_SELECTION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_PROVIDER_SELECTION_OK owner=IGNITION inputs=9 total_order=context_dependent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
