#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step03 renderer/provider independence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step03-renderer-independence.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step03-renderer-independence-r1.schema.json"
CANONICAL_PATH = ROOT / "data/architecture/overall-architecture.json"
EXPECTED_PREVIOUS_COMMIT = "037eaad775909cb85928ecff457e421aa1f8d041"
EXPECTED_SOURCE_PATH = "ignition/data/architecture/overall-architecture.json"
EXPECTED_SOURCE_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_SOURCE_REVISION = "d7372c27abe456b5b8c058675630d8038f91b448"
EXPECTED_OPERATION = "visualization.render_derived_system_view"
EXPECTED_INVARIANTS = [
    "EXTERNAL_PROVIDER ≠ IGNITION_AUTHORITY",
    "PROVIDER_CAPABILITY ≠ PERMISSION",
    "PROVIDER_OUTPUT ≠ EXTERNAL_TRUTH",
    "PROVIDER_LOCAL_POLICY ≠ IGNITION_GLOBAL_POLICY",
    "ADAPTER_SPIKE_PASS ≠ CURRENT_CAPABILITY",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_record(kind: str, identifier: str) -> dict[str, str]:
    payload = f"{EXPECTED_SOURCE_PATH}|{kind}|{identifier}|{EXPECTED_SOURCE_REVISION}|{EXPECTED_SOURCE_SHA}"
    return {
        "source_path": EXPECTED_SOURCE_PATH,
        "canonical_or_source_id": identifier,
        "source_revision": EXPECTED_SOURCE_REVISION,
        "provenance_digest": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step03 must bind the published Step02 formal commit")
    source = document["canonical_source"]
    if source["sha256"] != EXPECTED_SOURCE_SHA or sha256(CANONICAL_PATH) != EXPECTED_SOURCE_SHA:
        errors.append("canonical architecture source hash drifted")
    if source["path"] != EXPECTED_SOURCE_PATH or source["source_revision"] != EXPECTED_SOURCE_REVISION:
        errors.append("canonical source path or revision drifted")

    contract = document["adapter_contract"]
    if contract["operation_id"] != EXPECTED_OPERATION:
        errors.append("adapter operation ID drifted")
    if contract["allowed_flow"] != "CANONICAL_SOURCE -> PROVIDER_ADAPTER -> DERIVED_ARTIFACT":
        errors.append("adapter flow is not the one-way canonical-to-derived flow")
    if contract["reverse_flow_forbidden"] is not True or contract["repository_scan"] is not False or contract["canonical_write"] is not False:
        errors.append("reverse flow, repository scanning or canonical writes were not closed")
    if contract["provider_allowed_fields"] != ["geometry", "route", "theme", "layout"]:
        errors.append("provider allowed field set drifted")
    if "architecture_truth" not in contract["provider_forbidden_authorities"]:
        errors.append("architecture truth is not a provider-forbidden authority")
    if contract["topology_reconciliation"] != "EXACT_NODE_ID_SET_AND_EDGE_ENDPOINT_RELATION_MATCH_REQUIRED":
        errors.append("topology reconciliation is not exact and fail-closed")

    architecture = load_json(CANONICAL_PATH)
    node_ids = [node["id"] for node in architecture["nodes"]]
    edge_ids = [f"canonical-edge-{index:02d}" for index, _ in enumerate(architecture["edges"], start=1)]
    manifest = document["provenance_manifest"]
    if manifest["node_records"] != [expected_record("node", identifier) for identifier in node_ids]:
        errors.append("node provenance manifest does not exactly follow canonical source order")
    if manifest["edge_records"] != [expected_record("edge", identifier) for identifier in edge_ids]:
        errors.append("edge provenance manifest does not exactly follow canonical source order")
    if manifest["missing_field_action"] != "REJECT_AS_UNVALIDATED":
        errors.append("missing provenance field must reject the derived artifact")

    if document["authority_invariants"] != EXPECTED_INVARIANTS:
        errors.append("authority invariants are missing, reordered or weakened")
    boundary = document["boundary"]
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
        if boundary[key] is not False:
            errors.append(f"authority boundary widened: {key}")
    if boundary["provider_can_decide_geometry_route_theme_layout"] is not True:
        errors.append("provider geometry/layout choice was not retained as the only allowed choice")
    if boundary["current_integration"] != "NOT_CURRENT_INTEGRATION":
        errors.append("Step03 cannot claim Current integration")
    if boundary["authenticated_channel_admission"] != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("authenticated channel admission changed")
    if boundary["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live external invocation changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP03_RENDERER_INDEPENDENCE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    document = load_json(ARTIFACT_PATH)
    manifest = document["provenance_manifest"]
    print(
        "TASK150_STEP03_RENDERER_INDEPENDENCE_OK "
        f"operation={document['adapter_contract']['operation_id']} "
        f"nodes={len(manifest['node_records'])} edges={len(manifest['edge_records'])} "
        "flow=ONE_WAY provenance=COMPLETE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
