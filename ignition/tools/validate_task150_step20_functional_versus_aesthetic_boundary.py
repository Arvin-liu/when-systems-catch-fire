#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step20's functional/aesthetic boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step20-functional-versus-aesthetic-boundary.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step20-functional-versus-aesthetic-boundary-r1.schema.json"

FUNCTIONAL_IDS = [
    "declared_technical_readability",
    "viewport_containment",
    "topology_fidelity",
    "label_edge_collision_behavior",
    "provenance",
    "deterministic_bounded_generation",
    "failure_behavior",
]
AESTHETIC_IDS = [
    "official_ignition_visual_style",
    "homepage_or_publication_suitability",
    "branded_asset_suitability",
    "owner_aesthetic_endorsement",
]
FORBIDDEN_CLAIM_LABELS = {"OWNER_REJECTED_VISUAL", "OWNER_VISUAL_ACCEPTED"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _paths_with_value(value: Any, target: str, path: str = "$") -> list[str]:
    """Find a forbidden decision label outside the explicit label declaration."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.extend(_paths_with_value(child, target, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            # The receipt is allowed to name the two prohibited labels in the
            # dedicated declaration; they must not appear as a decision value.
            if path == "$.forbidden_claim_labels":
                continue
            found.extend(_paths_with_value(child, target, f"{path}[{index}]"))
    elif value == target:
        found.append(path)
    return found


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != "4913e428094d22fb9356d9e132a6e1d2687b68a6":
        errors.append("Step20 must start from the proven Step19 formal head")

    owner = document["owner_decision"]
    if owner["functional_visual_admission"] != "ALLOWED_TO_PROCEED":
        errors.append("functional visual admission must be allowed to proceed")
    if owner["owner_aesthetic_endorsement"] != "NOT_GRANTED":
        errors.append("Owner aesthetic endorsement must remain not granted")
    if owner["owner_rejected_visual"] or owner["owner_visual_accepted"]:
        errors.append("Owner aesthetic state was relabelled as rejection or acceptance")

    operation = document["operation"]
    if operation["operation_id"] != "visualization.render_derived_system_view":
        errors.append("operation identity must remain provider-neutral")
    if operation["operation_definition_is_provider_neutral"] is not True:
        errors.append("provider cannot redefine the operation")

    functional = operation["functional_boundary"]
    if functional["decision"] != "ALLOWED_TO_PROCEED":
        errors.append("functional boundary decision drifted")
    if functional["admission_state"] != "PROCEED_TO_FRESH_STANDALONE_EVIDENCE":
        errors.append("Step20 must authorize an attempt, not claim an admission")
    if functional["current_status"] != "NOT_ADMITTED_PENDING_STEP21":
        errors.append("Step20 cannot claim Current before Step21")
    observed_functional_ids = [item["id"] for item in functional["criteria"]]
    if observed_functional_ids != FUNCTIONAL_IDS:
        errors.append(f"functional criteria drifted: {observed_functional_ids!r}")
    if any(item["status"] != "REQUIRES_STEP21_EVIDENCE" for item in functional["criteria"]):
        errors.append("Step20 cannot turn functional criteria into fresh passes")

    aesthetic = operation["aesthetic_boundary"]
    if aesthetic["decision"] != "NOT_GRANTED" or aesthetic["claimed"] is not False:
        errors.append("aesthetic endorsement must be ungranted and unclaimed")
    if aesthetic["required_for_current_technical_scope"] is not False:
        errors.append("aesthetic endorsement must not block the declared technical scope")
    observed_aesthetic_ids = [item["id"] for item in aesthetic["criteria"]]
    if observed_aesthetic_ids != AESTHETIC_IDS:
        errors.append(f"aesthetic criteria drifted: {observed_aesthetic_ids!r}")
    if aesthetic["future_use_requires_separate_gate"] is not True:
        errors.append("future public or branded use must require a separate gate")

    for label in FORBIDDEN_CLAIM_LABELS:
        paths = _paths_with_value(document, label)
        if paths:
            errors.append(f"forbidden decision label {label} appears at {paths!r}")

    matrix = document["boundary_matrix"]
    expected_cases = {
        "functional_evidence_not_yet_proven_aesthetic_endorsement_absent",
        "functional_evidence_passes_aesthetic_endorsement_absent",
        "aesthetic_endorsement_present_without_functional_evidence",
        "future_publication_or_branded_use",
    }
    observed_cases = {item["case"] for item in matrix}
    if observed_cases != expected_cases:
        errors.append(f"boundary matrix cases drifted: {observed_cases!r}")
    case_map = {item["case"]: item for item in matrix}
    if case_map["functional_evidence_passes_aesthetic_endorsement_absent"]["permitted_use"] != "DECLARED_TECHNICAL_BOUNDED_USE_ONLY":
        errors.append("functional pass without aesthetic endorsement must remain technical-use bounded")
    if case_map["aesthetic_endorsement_present_without_functional_evidence"]["functional_result"] != "NOT_ADMITTED":
        errors.append("aesthetic endorsement cannot substitute for functional evidence")
    if case_map["future_publication_or_branded_use"]["aesthetic_result"] != "SEPARATE_GATE_REQUIRED":
        errors.append("future public or branded use needs a separate aesthetic gate")

    scope = document["scope_boundaries"]
    if scope["architecture_delta"] != "EXPERIMENTAL_EXTENSION_DEFERRED" or scope["delta_viewport_gate"] != "FAIL_DEFERRED":
        errors.append("Delta blocker was changed by the aesthetic boundary record")
    if scope["current_registry_operation_count"] != 19 or scope["registry_write"]:
        errors.append("Step20 must not write or change the Current Registry")
    if scope["default_renderer"] != "NOT_SELECTED" or scope["archify_architecture_authority"]:
        errors.append("renderer or provider authority boundary widened")
    if scope["agent_reach"] != "NO_CHANGE" or scope["authenticated_channel_admission"] != "NO_CHANGE":
        errors.append("Agent Reach or authentication boundary changed")
    if scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN" or scope["task151"] != "FORBIDDEN":
        errors.append("live invocation or successor-task boundary changed")

    contract = document["validation_contract"]
    if not all(contract.values()):
        errors.append("all functional/aesthetic independence assertions must remain true")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP20_FUNCTIONAL_AESTHETIC_BOUNDARY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP20_FUNCTIONAL_AESTHETIC_BOUNDARY_OK "
        "functional=ALLOWED_TO_PROCEED current=NOT_ADMITTED_PENDING_STEP21 "
        "aesthetic=NOT_GRANTED separate_gate=true registry=19"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
