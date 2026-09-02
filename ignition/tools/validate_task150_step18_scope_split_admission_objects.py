#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step18's split admission objects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step18-scope-split-admission-objects.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step18-scope-split-admission-objects-r1.schema.json"

EXPECTED_BASE_GATE_IDS = [
    "canonical_source_provenance_complete",
    "node_edge_semantic_fidelity",
    "provider_topology_unchanged",
    "standalone_viewport_containment_zero_failure",
    "provider_failure_fail_closed",
    "canonical_source_unaffected",
    "environment_admission_no_auto_install",
    "immutable_tested_compatibility_envelope",
    "artifact_digest_and_provenance_receipt",
    "provider_local_policy_isolation",
    "no_default_renderer",
    "no_architecture_truth_escalation",
]


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

    if document["formal_previous_commit"] != "c28314f9ede8e10690f937b00b9bb10e6bc226be":
        errors.append("Step18 must start from the pushed Step17 formal head")

    base = document["base_operation"]
    if base["operation_id"] != "visualization.render_derived_system_view":
        errors.append("base operation must remain provider-neutral")
    if base["status"] != "CURRENT_BOUNDED_CANDIDATE":
        errors.append("base operation must be a candidate until later lifecycle gates")
    if base["provider_binding"]["operation_definition_is_provider_neutral"] is not True:
        errors.append("provider binding cannot redefine the operation")
    if base["execution_boundary"]["mode"] != "READ_ONLY_RUN" or base["execution_boundary"]["repository_mutation"] != "FORBIDDEN":
        errors.append("base operation execution boundary widened")
    if base["execution_boundary"]["default_renderer"] != "NOT_SELECTED":
        errors.append("base object selected a default renderer")
    observed_base_ids = [gate["id"] for gate in base["gates"]]
    if observed_base_ids != EXPECTED_BASE_GATE_IDS:
        errors.append(f"base gate family drifted: expected={EXPECTED_BASE_GATE_IDS!r} observed={observed_base_ids!r}")
    if any(gate["result"] not in {"PENDING_STEP21_REVALIDATION", "PENDING_STEP22_REVALIDATION", "PASS_SCOPE_LOCKED"} for gate in base["gates"]):
        errors.append("Step18 cannot invent a fresh base gate result")

    delta = document["delta_extension"]
    if delta["status"] != "EXPERIMENTAL_EXTENSION_DEFERRED":
        errors.append("Delta must remain an experimental deferred extension")
    if delta["gate"]["result"] != "FAIL_DEFERRED" or delta["gate"]["diagnostics"] != 3:
        errors.append("Delta blocker was deleted or relabelled")
    if delta["promotion_guard"]["delta_failure_can_pollute_base"] is not False:
        errors.append("Delta failure cannot contaminate the base operation")
    if delta["promotion_guard"]["base_pass_promotes_delta"] is not False:
        errors.append("base pass cannot promote Delta")

    aesthetic = document["aesthetic_boundary"]
    if aesthetic["owner_aesthetic_endorsement"] != "NOT_GRANTED":
        errors.append("Owner aesthetic endorsement must remain ungranted")
    if aesthetic["owner_aesthetic_endorsement_required_for_base"] is not False:
        errors.append("aesthetic endorsement must not block this functional scope")
    if aesthetic["owner_rejected_visual"] or aesthetic["owner_visual_accepted"]:
        errors.append("aesthetic boundary was relabelled as rejection or acceptance")

    registry = document["registry_boundary"]
    if registry["operation_count_before"] != 19 or registry["operation_count_after"] != 19:
        errors.append("Step18 must not change the 19-operation registry")
    if registry["registry_write_in_step18"] or registry["operation_present"] or registry["delta_registered"]:
        errors.append("Step18 performed or claimed a registry admission")

    scope = document["scope_freeze"]
    if scope["task150_scope"] != "ARCHIFY_ONLY" or scope["agent_reach"] != "NO_CHANGE":
        errors.append("Task150 or Agent Reach scope changed")
    if scope["authenticated_channel_admission"] != "NO_CHANGE" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("authentication or live invocation boundary changed")
    if scope["default_renderer"] != "NOT_SELECTED" or scope["task151"] != "FORBIDDEN":
        errors.append("default renderer or successor-task boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP18_SCOPE_SPLIT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP18_SCOPE_SPLIT_OK "
        "base=visualization.render_derived_system_view "
        "base_status=CURRENT_BOUNDED_CANDIDATE "
        "delta=EXPERIMENTAL_EXTENSION_DEFERRED "
        "delta_viewport=FAIL_DEFERRED registry=19"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
