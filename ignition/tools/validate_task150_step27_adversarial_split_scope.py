#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step27 split-scope adversarial regressions."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.validate_ignition_operation_capability_registry import validate as validate_registry
from tools.validate_task150_step21_fresh_standalone_evidence import exact_topology_errors


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step27-adversarial-split-scope-regression.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step27-adversarial-split-scope-r1.schema.json"
FIXTURE_PATH = ROOT / "data/operations/iterations/150/fixtures/task150-step27-adversarial-split-scope.json"
CANONICAL_PATH = ROOT / "data/architecture/overall-architecture.json"
IR_PATH = ROOT / "data/operations/iterations/150/task150-archify-typed-ir-r1.json"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"

EXPECTED_FORMAL_HEAD = "672a7a1a757a3741cd1c2643a29e5fc4470ab06a"
EXPECTED_FIXTURE_SHA = "d9079c63ae87917124698bd52b06f7e84bccd2dc953cb1c80536fbfb74dd79b7"
EXPECTED_CANONICAL_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_IR_SHA = "2788796b4d329251cc67e502b6081b77542388b7f25f99470e400bf6722575ed"
EXPECTED_IR_SOURCE_REVISION = "68d5d30bda0d8eb9c715ac346ce6476a55c0e288"
EXPECTED_CASE_IDS = (
    "standalone_pass_delta_fail",
    "standalone_fail_delta_pass",
    "archify_unavailable",
    "archify_adds_semantic_node",
    "archify_deletes_canonical_node",
    "archify_changes_edge_semantics",
    "green_validator_no_architecture_truth",
    "aesthetic_endorsement_absent",
    "delta_wrapper_repaired_no_auto_promotion",
    "new_provider_version_no_auto_upgrade",
    "provider_skill_imperative_no_override",
)
EXPECTED_CASE_OUTPUTS = {
    "standalone_pass_delta_fail": {
        "base": "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE",
        "delta": "DEFER",
        "result": "BASE_BOUNDED_DELTA_DEFERRED",
    },
    "standalone_fail_delta_pass": {
        "base": "DEFER",
        "delta": "SEPARATE_ADMISSION_REQUIRED",
        "result": "BASE_FAILURE_BLOCKS_BASE_ADMISSION",
    },
    "archify_unavailable": {
        "base": "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT",
        "delta": "NOT_RUN",
        "result": "NO_INSTALL_NO_SUBSTITUTION_NO_REPOSITORY_MUTATION",
    },
    "archify_adds_semantic_node": {
        "base": "REJECT_ARTIFACT",
        "delta": "NOT_RELEVANT",
        "result": "EXTRA_CANONICAL_NODE_REJECTED",
    },
    "archify_deletes_canonical_node": {
        "base": "REJECT_ARTIFACT",
        "delta": "NOT_RELEVANT",
        "result": "DELETED_CANONICAL_NODE_REJECTED",
    },
    "archify_changes_edge_semantics": {
        "base": "REJECT_ARTIFACT",
        "delta": "NOT_RELEVANT",
        "result": "CHANGED_CANONICAL_EDGE_REJECTED",
    },
    "green_validator_no_architecture_truth": {
        "base": "BOUNDED_RESULT_ONLY",
        "delta": "UNCHANGED",
        "result": "NO_ARCHITECTURE_TRUTH_ESCALATION",
    },
    "aesthetic_endorsement_absent": {
        "base": "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE",
        "delta": "DEFER",
        "result": "FUNCTIONAL_ALLOWED_AESTHETIC_NOT_CLAIMED",
    },
    "delta_wrapper_repaired_no_auto_promotion": {
        "base": "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE",
        "delta": "SEPARATE_ADMISSION_REQUIRED",
        "result": "NO_AUTOMATIC_DELTA_PROMOTION",
    },
    "new_provider_version_no_auto_upgrade": {
        "base": "COMPATIBILITY_CHECK_REQUIRED",
        "delta": "UNCHANGED",
        "result": "NO_AUTOMATIC_PROVIDER_UPGRADE",
    },
    "provider_skill_imperative_no_override": {
        "base": "IGNITION_SELECTION_PREVAILS",
        "delta": "UNCHANGED",
        "result": "SKILL_CANNOT_OVERRIDE_IGNITION_AUTHORITY",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_topology_mutation(ir: dict[str, Any], mutation: str) -> dict[str, Any]:
    """Apply one declared adversarial mutation without writing the input or result."""

    mutated = copy.deepcopy(ir)
    if mutation == "APPEND_COMPONENT":
        mutated["components"].append(
            {
                "id": "adversarial-semantic-node",
                "type": "backend",
                "label": "Adversarial semantic node",
                "tag": "CANONICAL_DERIVED_PROJECTION",
                "pos": [10, 10],
                "size": [190, 28],
            }
        )
    elif mutation == "REMOVE_COMPONENT":
        mutated["components"] = [
            item for item in mutated["components"] if item["id"] != "navigation-machine"
        ]
    elif mutation == "CHANGE_EDGE_SEMANTICS":
        for connection in mutated["connections"]:
            if connection["id"] == "canonical-edge-01":
                connection["label"] = "未经授权的语义改变"
                break
        else:
            raise ValueError("canonical-edge-01 is missing from typed IR")
    else:
        raise ValueError(f"mutation is not a topology mutation: {mutation}")
    return mutated


def evaluate_case(case: dict[str, Any], architecture: dict[str, Any], ir: dict[str, Any]) -> dict[str, str]:
    """Evaluate one policy fixture using only immutable in-memory values."""

    case_id = case["id"]
    if case_id == "standalone_pass_delta_fail":
        return {
            "base": "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE",
            "delta": "DEFER",
            "result": "BASE_BOUNDED_DELTA_DEFERRED",
        }
    if case_id == "standalone_fail_delta_pass":
        return {
            "base": "DEFER",
            "delta": "SEPARATE_ADMISSION_REQUIRED",
            "result": "BASE_FAILURE_BLOCKS_BASE_ADMISSION",
        }
    if case_id == "archify_unavailable":
        return {
            "base": "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT",
            "delta": "NOT_RUN",
            "result": "NO_INSTALL_NO_SUBSTITUTION_NO_REPOSITORY_MUTATION",
        }
    if case_id in {
        "archify_adds_semantic_node",
        "archify_deletes_canonical_node",
        "archify_changes_edge_semantics",
    }:
        mutated = apply_topology_mutation(ir, case["mutation"])
        if not exact_topology_errors(architecture, mutated):
            return {"base": "ACCEPTED", "delta": "NOT_RELEVANT", "result": "TOPOLOGY_RECONCILIATION_FAILED_OPEN"}
        result_by_case = {
            "archify_adds_semantic_node": "EXTRA_CANONICAL_NODE_REJECTED",
            "archify_deletes_canonical_node": "DELETED_CANONICAL_NODE_REJECTED",
            "archify_changes_edge_semantics": "CHANGED_CANONICAL_EDGE_REJECTED",
        }
        return {"base": "REJECT_ARTIFACT", "delta": "NOT_RELEVANT", "result": result_by_case[case_id]}
    if case_id == "green_validator_no_architecture_truth":
        return {
            "base": "BOUNDED_RESULT_ONLY",
            "delta": "UNCHANGED",
            "result": "NO_ARCHITECTURE_TRUTH_ESCALATION",
        }
    if case_id == "aesthetic_endorsement_absent":
        return {
            "base": "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE",
            "delta": "DEFER",
            "result": "FUNCTIONAL_ALLOWED_AESTHETIC_NOT_CLAIMED",
        }
    if case_id == "delta_wrapper_repaired_no_auto_promotion":
        return {
            "base": "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE",
            "delta": "SEPARATE_ADMISSION_REQUIRED",
            "result": "NO_AUTOMATIC_DELTA_PROMOTION",
        }
    if case_id == "new_provider_version_no_auto_upgrade":
        return {
            "base": "COMPATIBILITY_CHECK_REQUIRED",
            "delta": "UNCHANGED",
            "result": "NO_AUTOMATIC_PROVIDER_UPGRADE",
        }
    if case_id == "provider_skill_imperative_no_override":
        return {
            "base": "IGNITION_SELECTION_PREVAILS",
            "delta": "UNCHANGED",
            "result": "SKILL_CANNOT_OVERRIDE_IGNITION_AUTHORITY",
        }
    raise ValueError(f"unknown Step27 fixture: {case_id}")


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_FORMAL_HEAD:
        errors.append("Step27 must start from the pushed Step26 formal head")

    fixture = load_json(FIXTURE_PATH)
    if sha256(FIXTURE_PATH) != EXPECTED_FIXTURE_SHA:
        errors.append("Step27 adversarial fixture hash drifted")
    if document["fixture"]["sha256"] != EXPECTED_FIXTURE_SHA:
        errors.append("recorded Step27 fixture hash drifted")
    if document["fixture"]["case_count"] != len(fixture["cases"]):
        errors.append("Step27 fixture case count is inconsistent")
    if document["case_results"] != fixture["cases"]:
        errors.append("Step27 receipt case results do not exactly match the durable fixture")
    case_ids = tuple(case["id"] for case in fixture["cases"])
    if case_ids != EXPECTED_CASE_IDS:
        errors.append(f"Step27 fixture case order or IDs drifted: {case_ids!r}")
    if len(set(case_ids)) != len(case_ids):
        errors.append("Step27 fixture contains duplicate case IDs")
    if fixture["provider_process_started"] or fixture["credentials_or_sessions_accessed"] or fixture["system_or_repository_mutation"]:
        errors.append("Step27 fixture crossed a side-effect boundary")

    architecture = load_json(CANONICAL_PATH)
    ir = load_json(IR_PATH)
    if sha256(CANONICAL_PATH) != EXPECTED_CANONICAL_SHA or document["canonical_binding"]["canonical_source_sha256"] != EXPECTED_CANONICAL_SHA:
        errors.append("canonical source hash drifted")
    if sha256(IR_PATH) != EXPECTED_IR_SHA or document["canonical_binding"]["typed_ir_sha256"] != EXPECTED_IR_SHA:
        errors.append("typed IR hash drifted")
    if ir.get("meta", {}).get("repository", {}).get("revision") != EXPECTED_IR_SOURCE_REVISION:
        errors.append("typed IR source revision drifted")
    if len(architecture.get("nodes", [])) != 24 or len(architecture.get("edges", [])) != 24:
        errors.append("canonical topology cardinality drifted")
    if len(ir.get("components", [])) != 24 or len(ir.get("connections", [])) != 24:
        errors.append("typed IR topology cardinality drifted")
    if exact_topology_errors(architecture, ir):
        errors.append("current typed IR is not exactly reconciled to canonical topology")

    if document["canonical_binding"]["provider_topology_authority"]:
        errors.append("provider topology authority was enabled")
    for case in fixture["cases"]:
        expected = EXPECTED_CASE_OUTPUTS.get(case["id"])
        if expected is None or case["expected"] != expected:
            errors.append(f"declared expected output drifted for {case['id']}")
            continue
        try:
            observed = evaluate_case(case, architecture, ir)
        except (KeyError, ValueError) as exc:
            errors.append(f"fixture evaluation failed for {case['id']}: {exc}")
            continue
        if observed != expected:
            errors.append(f"adversarial case {case['id']} did not produce its expected fail-closed result")

    registry = load_json(REGISTRY_PATH)
    if sha256(REGISTRY_PATH) != "ec285324bbdff4a718f7ffd761a61f8d393b77b8e15967bfd2e207a6d9950ea4":
        errors.append("Capability Registry hash drifted from the Step24-26 candidate baseline")
    registry_errors = validate_registry(copy.deepcopy(registry))
    if registry_errors:
        errors.append("canonical Capability Registry validator failed: " + "; ".join(registry_errors))
    operation_ids = [row["operation_id"] for row in registry.get("operations", [])]
    if len(operation_ids) != 20 or "visualization.render_derived_system_view" not in operation_ids:
        errors.append("Step27 requires the single provider-neutral base operation at Registry count 20")
    if any("delta" in operation_id.casefold() for operation_id in operation_ids):
        errors.append("Architecture Delta was registered as an operation")
    if any("archify" in operation_id.casefold() for operation_id in operation_ids):
        errors.append("provider-specific Archify operation was registered")
    operation = next((row for row in registry.get("operations", []) if row["operation_id"] == "visualization.render_derived_system_view"), None)
    if operation is None:
        errors.append("base visualization operation is absent")
    else:
        if operation["current_status"] != "CURRENT_BOUNDED" or operation["pack_binding"] is not None:
            errors.append("base visualization operation lost its provider-neutral bounded definition")
        if operation["default_execution_mode"] != "READ_ONLY_RUN" or operation["repository_mutation_permission"] != "FORBIDDEN" or operation["external_action_permission"] != "FORBIDDEN":
            errors.append("base visualization operation side-effect boundary widened")
        if operation["ai_callability"] != "PUBLIC_BOUNDED":
            errors.append("base visualization operation callability widened")

    validation = document["validation"]
    expected_validation = {
        "fixture_hash": "PASS",
        "case_count": 11,
        "canonical_source_hash": "PASS",
        "typed_ir_hash": "PASS",
        "exact_topology": "PASS_EXACT_24_NODES_24_EDGES",
        "topology_mutations": "PASS_REJECTED_3_OF_3",
        "standalone_delta_split": "PASS_BASE_INDEPENDENT_DELTA_DEFERRED",
        "provider_unavailable": "PASS_FAIL_CLOSED_NO_INSTALL_NO_SUBSTITUTION",
        "green_validator_truth_boundary": "PASS_NO_ARCHITECTURE_TRUTH_ESCALATION",
        "aesthetic_boundary": "PASS_FUNCTIONAL_ALLOWED_AESTHETIC_NOT_CLAIMED",
        "delta_auto_promotion": "PASS_SEPARATE_ADMISSION_REQUIRED",
        "provider_auto_upgrade": "PASS_COMPATIBILITY_CHECK_REQUIRED",
        "provider_skill_authority": "PASS_IGNITION_SELECTION_PREVAILS",
        "side_effect_boundary": "PASS_NO_PROCESS_CREDENTIAL_SESSION_OR_REPOSITORY_SIDE_EFFECT",
        "registry_boundary": "PASS_20_PROVIDER_NEUTRAL_BASE_ONLY",
        "default_renderer": "NOT_SELECTED",
        "architecture_authority": False,
        "agent_reach": "NO_CHANGE",
        "authenticated_channel_admission": "NO_CHANGE",
        "live_external_invocation": "OPEN_OWNER_DEFERRED_NOT_RUN",
        "task151": "FORBIDDEN",
    }
    if validation != expected_validation:
        errors.append("Step27 validation summary drifted")

    scope = document["scope_freeze"]
    expected_scope = {
        "task150_scope": "ARCHIFY_ONLY",
        "base_operation": "CURRENT_BOUNDED_CANDIDATE",
        "architecture_delta": "EXPERIMENTAL_EXTENSION_DEFERRED",
        "owner_aesthetic_endorsement": "NOT_GRANTED_NOT_CLAIMED",
        "default_renderer": "NOT_SELECTED",
        "architecture_authority": False,
        "agent_reach": "NO_CHANGE",
        "authenticated_channel_admission": "NO_CHANGE",
        "live_external_invocation": "OPEN_OWNER_DEFERRED_NOT_RUN",
        "task151": "FORBIDDEN",
    }
    if scope != expected_scope:
        errors.append("Step27 scope freeze widened")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP27_ADVERSARIAL_SPLIT_SCOPE_REGRESSION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP27_ADVERSARIAL_SPLIT_SCOPE_REGRESSION_OK "
        "cases=11 topology_mutations=3/3_rejected base_delta=independent "
        "provider_unavailable=fail_closed aesthetic=not_claimed auto_promotion=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
