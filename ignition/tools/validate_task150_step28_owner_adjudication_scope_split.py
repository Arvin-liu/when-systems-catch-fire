#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step28's post-review adjudication."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.validate_ignition_operation_capability_registry import validate as validate_registry
from tools.validate_task150_step23_candidate_registry_admission import validate as validate_step23
from tools.validate_task150_step24_playbook_and_minimal_routing_sync import validate as validate_step24
from tools.validate_task150_step25_delta_remains_experimental_deferred import validate as validate_step25
from tools.validate_task150_step26_front_door_and_sync_surface_restraint import validate as validate_step26
from tools.validate_task150_step27_adversarial_split_scope import validate as validate_step27


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step28-owner-adjudication-scope-split.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step28-owner-adjudication-scope-split-r1.schema.json"
STEP14_PATH = ROOT / "data/operations/iterations/150/step14-final-defer-decision.json"
STEP15_PATH = ROOT / "data/operations/iterations/150/step15-draft-closeout.json"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"

EXPECTED_PREVIOUS_COMMIT = "d08ec65c03ea2fdf334e71649ab22dd4aec84f04"
EXPECTED_STEP14_SHA = "ef6465cdc824e9865cf3a2e4b8e366684877a672e0f0e9a5fb791b7cbf8a1482"
EXPECTED_STEP15_SHA = "13894ad61b0b28b0fbcba96d2f562208fd7f2d3f5d83212687dd959c7be4b4c3"
EXPECTED_REGISTRY_SHA = "ec285324bbdff4a718f7ffd761a61f8d393b77b8e15967bfd2e207a6d9950ea4"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step28 must start from the pushed Step27 formal head")

    timeline = document["historical_timeline"]
    if sha256(STEP14_PATH) != EXPECTED_STEP14_SHA or timeline["step14_sha256"] != EXPECTED_STEP14_SHA:
        errors.append("historical Step14 receipt hash drifted")
    if sha256(STEP15_PATH) != EXPECTED_STEP15_SHA or timeline["step15_sha256"] != EXPECTED_STEP15_SHA:
        errors.append("historical Step15 receipt hash drifted")
    step14 = load_json(STEP14_PATH)
    step15 = load_json(STEP15_PATH)
    if step14["status"] != "DEFER" or step14["decision"]["outcome"] != "DEFER":
        errors.append("historical Step14 DEFER was rewritten")
    if step14["decision"]["current_capability"] or step14["decision"]["default_renderer"] or step14["decision"]["registry_write"] or step14["decision"]["ready_or_merge_authorization"]:
        errors.append("historical Step14 authority boundaries widened")
    if step14["gate_summary"]["delta_viewport_containment_zero_failure"] != "FAIL" or step14["gate_summary"]["owner_visual_acceptance"] != "PENDING":
        errors.append("historical Step14 blocker or Owner-pending state was rewritten")
    if step15["status"] != "AWAIT_OWNER_ARCHIFY_BOUNDED_ADMISSION_REVIEW" or not step15["pull_request"]["is_draft"]:
        errors.append("historical Step15 Draft stop was rewritten")
    if step15["closeout"]["decision"] != "DEFER" or step15["closeout"]["registry_write"] or step15["closeout"]["current_capability"] or step15["closeout"]["task151"] != "FORBIDDEN":
        errors.append("historical Step15 closeout boundaries widened")
    if timeline["step14_basis"] != "STEP14_DEFER_WAS_VALID_UNDER_COMBINED_SCOPE" or timeline["owner_scope_split_timing"] != "OWNER_SCOPE_SPLIT_OCCURRED_AFTER_STEP15":
        errors.append("Step28 did not preserve the required historical sequence")
    if not timeline["historical_files_unchanged"] or not timeline["no_evidence_rewritten"]:
        errors.append("Step28 claims or permits historical evidence rewriting")

    step27_errors = validate_step27()
    if step27_errors:
        errors.append("Step27 adversarial regression is not retained: " + "; ".join(step27_errors))

    registry = load_json(REGISTRY_PATH)
    if sha256(REGISTRY_PATH) != EXPECTED_REGISTRY_SHA:
        errors.append("Capability Registry changed during Step28 adjudication")
    registry_errors = validate_registry(copy.deepcopy(registry))
    if registry_errors:
        errors.append("canonical Capability Registry validator failed: " + "; ".join(registry_errors))
    operation_ids = [row["operation_id"] for row in registry.get("operations", [])]
    if len(operation_ids) != 20 or "visualization.render_derived_system_view" not in operation_ids:
        errors.append("Step28 no longer sees the single base operation at Registry count 20")
    if any("delta" in operation_id.casefold() or "archify" in operation_id.casefold() for operation_id in operation_ids):
        errors.append("Step28 allowed a Delta or provider-specific operation ID")
    operation = next((row for row in registry["operations"] if row["operation_id"] == "visualization.render_derived_system_view"), None)
    if operation is None or operation["current_status"] != "CURRENT_BOUNDED" or operation["pack_binding"] is not None:
        errors.append("base Registry entry is not the provider-neutral CURRENT_BOUNDED definition")

    adjudication = document["adjudication"]
    base = adjudication["base_standalone"]
    delta = adjudication["architecture_delta"]
    aesthetic = adjudication["aesthetic_endorsement"]
    if base["decision"] != "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE" or base["delta_is_required"] or base["aesthetic_is_required"]:
        errors.append("base standalone adjudication is not independently bounded")
    if delta["decision"] != "DEFER" or delta["status"] != "EXPERIMENTAL_EXTENSION_DEFERRED" or not delta["independent_admission_required"] or delta["base_pass_promotes_delta"]:
        errors.append("Delta adjudication was promoted or coupled to the base")
    if aesthetic["decision"] != "NOT_CLAIMED" or aesthetic["required_for_functional_admission"] or aesthetic["homepage_or_brand_claim"] != "FORBIDDEN":
        errors.append("aesthetic endorsement was used as a base gate or claimed")
    if adjudication["default_renderer"] != "NOT_SELECTED" or adjudication["archify_architecture_authority"] or adjudication["architecture_authority_source"] != "IGNITION_CANONICAL_SOURCE":
        errors.append("renderer or architecture authority boundary widened")
    if adjudication["agent_reach"] != "NO_CHANGE" or adjudication["authenticated_channel_admission"] != "NO_CHANGE" or adjudication["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("Agent Reach, authentication or live invocation boundary changed")
    if adjudication["base_gate_failure_fallback"] != "OVERALL_DEFER" or adjudication["task151"] != "FORBIDDEN":
        errors.append("base failure fallback or Task151 guard changed")

    lifecycle = document["lifecycle_boundary"]
    if lifecycle["registry_operation_count"] != 20 or lifecycle["registry_entry_status"] != "CURRENT_BOUNDED_CANDIDATE":
        errors.append("Step28 lifecycle boundary is not candidate-only")
    if lifecycle["formal_ready"] or lifecycle["merged_to_main"] or lifecycle["current_on_main"] or lifecycle["ready_transition_authorized_by_step28"]:
        errors.append("Step28 crossed the Ready, merge or Current-on-main boundary")
    if lifecycle["pr_state"] != "OPEN" or not lifecycle["pr_is_draft"]:
        errors.append("Step28 requires the PR to remain OPEN + DRAFT before Step29")
    if lifecycle["default_renderer"] != "NOT_SELECTED" or lifecycle["delta_operation_registered"]:
        errors.append("Step28 renderer or Delta registration boundary changed")

    expected_validation = {
        "historical_step14_hash": "PASS",
        "historical_step15_hash": "PASS",
        "step27_validator": "PASS",
        "registry_validator": "PASS operations=20",
        "base_operation_lookup": "PASS_PROVIDER_NEUTRAL_CURRENT_BOUNDED",
        "delta_not_registered": "PASS",
        "scope_split_decision": "PASS_BASE_ADMIT_CANDIDATE_DELTA_DEFER",
        "aesthetic_boundary": "PASS_NOT_REQUIRED_NOT_CLAIMED",
        "live_and_auth_boundary": "PASS_UNCHANGED",
        "ready_boundary": "PASS_DRAFT_PRE_READY",
        "successor_boundary": "PASS_TASK151_FORBIDDEN",
    }
    if document["validation"] != expected_validation:
        errors.append("Step28 validation summary drifted")

    expected_scope = {
        "task150_scope": "ARCHIFY_ONLY",
        "base_operation": "CURRENT_BOUNDED_CANDIDATE",
        "architecture_delta": "EXPERIMENTAL_EXTENSION_DEFERRED",
        "owner_aesthetic_endorsement": "NOT_GRANTED_NOT_CLAIMED",
        "default_renderer": "NOT_SELECTED",
        "architecture_authority": False,
        "agent_reach": "NO_CHANGE",
        "authenticated_channel_admission": "NO_CHANGE",
        "live_external_invocation": "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN",
        "task151": "FORBIDDEN",
    }
    if document["scope_freeze"] != expected_scope:
        errors.append("Step28 scope freeze widened")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("TASK150_STEP28_OWNER_ADJUDICATION_SCOPE_SPLIT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP28_OWNER_ADJUDICATION_SCOPE_SPLIT_OK "
        "historical_step14=DEFER_preserved historical_step15=draft_stop_preserved "
        "base=ADMIT_AS_CURRENT_BOUNDED_CANDIDATE delta=DEFER aesthetic=NOT_CLAIMED "
        "default_renderer=NOT_SELECTED ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
