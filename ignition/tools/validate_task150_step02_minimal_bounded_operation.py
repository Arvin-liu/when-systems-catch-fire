#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step02's minimal operation contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step02-minimal-bounded-operation.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step02-minimal-bounded-operation-r1.schema.json"
EXPECTED_BASELINE = "d7372c27abe456b5b8c058675630d8038f91b448"
EXPECTED_OPERATION_ID = "visualization.render_derived_system_view"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_baseline"]["sha"] != EXPECTED_BASELINE:
        errors.append("Step02 must bind the exact Task149 ordinary-merge main baseline")

    operation = document["operation"]
    if operation["operation_id"] != EXPECTED_OPERATION_ID:
        errors.append("operation id changed from the existing dotted taxonomy")
    if operation["current_status"] == "CURRENT":
        errors.append("Step02 operation cannot claim Current")
    if operation["registry_entry_status"] != "NOT_YET_REGISTERED_PENDING_STEP11":
        errors.append("Step02 must defer registry entry until Step11")
    if document["provider_selection"]["provider_binding"] != "UNBOUND_PROVIDER_SLOT_AT_STEP02":
        errors.append("Step02 must remain provider-neutral")
    if operation["allowed_flow"] != "CANONICAL_SOURCE -> PROVIDER_ADAPTER -> DERIVED_ARTIFACT":
        errors.append("provider flow is not the one-way canonical-to-derived flow")
    if operation["reverse_flow_forbidden"] is not True:
        errors.append("derived output must not flow back into canonical source")

    mutation = operation["repository_mutation"]
    if mutation["permission"] != "FORBIDDEN":
        errors.append("Step02 operation cannot authorize repository mutation")
    invocation = operation["provider_invocation"]
    if invocation["scope"] != "BOUNDED_PROVIDER_INVOCATION_FOR_DERIVED_ARTIFACT_ONLY":
        errors.append("provider invocation is broader than the derived-artifact boundary")
    if invocation["unrelated_external_action"] != "FORBIDDEN":
        errors.append("unrelated external action must remain forbidden")
    if invocation["credentials"] != "FORBIDDEN" or invocation["session_bearing_channels"] != "FORBIDDEN":
        errors.append("credentials and session-bearing channels must remain forbidden")

    authority = document["authority_boundary"]
    for key in (
        "derived_artifact_can_update_canonical_source",
        "provider_can_add_topology",
        "provider_can_delete_topology",
        "provider_can_change_semantic_relationships",
        "provider_can_decide_architecture_truth",
        "provider_can_decide_runtime_behavior",
        "provider_can_decide_impact_risk_correctness",
        "provider_output_is_external_truth",
    ):
        if authority[key] is not False:
            errors.append(f"authority boundary widened: {key}")
    if authority["provider_can_decide_geometry_route_theme_layout"] is not True:
        errors.append("provider may choose only derived geometry, route, theme and layout")
    if authority["authenticated_channel_admission"] != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("authenticated channel admission must remain closed")
    if authority["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live external invocation boundary changed")

    if document["provenance"]["missing_provenance_result"] != "REJECT_AS_UNVALIDATED":
        errors.append("missing provenance must fail closed")
    failure = document["failure_and_fallback"]
    if failure["canonical_source_remains_usable"] is not True or failure["last_known_canonical_map_remains_usable"] is not True:
        errors.append("provider failure must preserve canonical fallback surfaces")
    if document["installation_boundary"]["automatic_system_install"] is not False:
        errors.append("automatic system installation is forbidden")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP02_MINIMAL_BOUNDED_OPERATION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    document = load_json(ARTIFACT_PATH)
    print(
        "TASK150_STEP02_MINIMAL_BOUNDED_OPERATION_OK "
        f"operation={document['operation']['operation_id']} "
        f"status={document['operation']['current_status']} "
        "registry=DEFERRED_TO_STEP11 provider=UNBOUND"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
