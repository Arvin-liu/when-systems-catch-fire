#!/usr/bin/env python3
"""Fail-closed validation for the Task149 Step07 Archify Delta receipt."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step07-archify-delta-receipt.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step07-archify-architecture-delta-r0.schema.json"
BEFORE_IR_PATH = ROOT / "data/operations/iterations/149/step07-archify-before-r0.json"
AFTER_IR_PATH = ROOT / "data/operations/iterations/149/step07-archify-after-r0.json"
ARCHITECTURE_PATH = ROOT / "data/architecture/overall-architecture.json"
SYSTEM_MAP_PATH = ROOT / "data/architecture/interactive-system-map.json"

EXPECTED_BEFORE_SHA = "a1a1d102c3cd2fa12fc962b648b0eea62d8097cf"
EXPECTED_AFTER_SHA = "14c2595d796494286caf31378173fd9dd027edcf"
EXPECTED_FORMAL_PREVIOUS_COMMIT = "656e555711ada1dd3754a0b43b8ec73aacda1f9c"
EXPECTED_BEFORE_IR_SHA = "0ee0e9fad3b39c2da95da7e4941bc86f387bf1867bec76c02fa116dfd125e9e1"
EXPECTED_AFTER_IR_SHA = "b3415845a682c9d8162a056da6402622505ce91f2c6658bf3f199fd9e6653049"
EXPECTED_ARCHITECTURE_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_BEFORE_MAP_SHA = "18f0f68f60d606976470368ee82fac2d35e2e96cd3739be9f5f43e8db9075d69"
EXPECTED_AFTER_MAP_SHA = "3824697a9c781c1ea825f7335bc9461e6fb693e70bb65c042309fd16da173313"
FORBIDDEN_FIELD_LIST = ["impact", "risk", "safety", "quality_improvement", "correctness", "merge_readiness"]
FORBIDDEN_KEYS = set(FORBIDDEN_FIELD_LIST)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def all_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        keys.extend(value.keys())
        for child in value.values():
            keys.extend(all_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(all_keys(child))
    return keys


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    schema = load_json(SCHEMA_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(schema).iter_errors(document)]

    if document.get("formal_previous_commit") != EXPECTED_FORMAL_PREVIOUS_COMMIT:
        errors.append("Step07 must bind the published Step06 formal commit")
    lineage = document.get("lineage", {})
    if lineage.get("before", {}).get("sha") != EXPECTED_BEFORE_SHA:
        errors.append("before lineage must remain the accepted pre-Task148 main baseline")
    if lineage.get("after", {}).get("sha") != EXPECTED_AFTER_SHA:
        errors.append("after lineage must remain the post-publication Current main SHA")
    if lineage.get("remote_main", {}).get("observed_sha") != EXPECTED_AFTER_SHA:
        errors.append("remote main observation must remain the post-publication Current main SHA")

    source_inputs = document.get("source_inputs", {})
    delta_input = source_inputs.get("delta_input", {})
    if delta_input.get("before_sha256") != EXPECTED_ARCHITECTURE_SHA or delta_input.get("after_sha256") != EXPECTED_ARCHITECTURE_SHA:
        errors.append("overall architecture source hashes must remain byte-identical")
    context = source_inputs.get("context_only", [{}])[0]
    if context.get("before_sha256") != EXPECTED_BEFORE_MAP_SHA or context.get("after_sha256") != EXPECTED_AFTER_MAP_SHA:
        errors.append("interactive system map context hashes drifted")
    if context.get("not_promoted_to_archify_node_or_edge") is not True:
        errors.append("context-only map changes must not become Archify nodes or edges")

    typed = document.get("typed_snapshots", {})
    if typed.get("before", {}).get("sha256") != digest(BEFORE_IR_PATH) or digest(BEFORE_IR_PATH) != EXPECTED_BEFORE_IR_SHA:
        errors.append("before typed snapshot hash mismatch")
    if typed.get("after", {}).get("sha256") != digest(AFTER_IR_PATH) or digest(AFTER_IR_PATH) != EXPECTED_AFTER_IR_SHA:
        errors.append("after typed snapshot hash mismatch")

    upstream = document.get("upstream", {})
    if upstream.get("revision") != "2bfb47132c057195d8dddb3e25ae966dd7c7a72e":
        errors.append("Archify upstream revision drifted")
    delta = document.get("delta_output", {})
    actual = delta.get("actual_authored_facts", {})
    if actual.get("components") != {"added": 0, "removed": 0, "changed": 0, "moved": 0, "evidence_changed": 0}:
        errors.append("component delta must remain empty")
    if actual.get("connections") != {"added": 0, "removed": 0, "changed": 0, "rerouted": 0}:
        errors.append("connection delta must remain empty")
    if actual.get("boundaries") != {"added": 0, "removed": 0, "changed": 0, "geometry_changed": 0}:
        errors.append("boundary delta must remain empty")
    if actual.get("change_records") != []:
        errors.append("Step07 must not carry unvalidated change records")
    if delta.get("no_inference_fields_emitted") != FORBIDDEN_FIELD_LIST:
        errors.append("delta forbidden inference field list drifted")
    if any(key in FORBIDDEN_KEYS for key in all_keys(document)):
        errors.append("forbidden impact/risk/safety/correctness/merge-readiness key emitted")

    boundaries = document.get("boundaries", {})
    for key in ("external_provider_is_ignition_authority", "provider_capability_is_permission", "provider_output_is_external_truth", "provider_local_policy_is_ignition_global_policy", "adapter_spike_pass_is_current_capability", "provider_permission_granted", "source_copied_or_vendored"):
        if boundaries.get(key) is not False:
            errors.append(f"provider boundary {key} is not fail-closed")
    if boundaries.get("current_integration") != "NOT_CURRENT_INTEGRATION":
        errors.append("Step07 must not claim Current integration")
    if boundaries.get("production_readiness") != "NOT_PRODUCTION_READY":
        errors.append("Step07 must not claim production readiness")
    if boundaries.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("authenticated channel admission must remain closed")
    if boundaries.get("live_external_invocation") != "LIVE_EXTERNAL_INVOCATION_UNCHANGED":
        errors.append("live external invocation must remain unchanged")
    visual_delta = document.get("commands", {}).get("visual_check", {}).get("delta", {})
    if visual_delta.get("status") != "FAIL_VIEWPORT_CONTAINMENT" or visual_delta.get("diagnostic_code") != "viewer/viewport-overflow":
        errors.append("known Delta viewer containment residual must remain explicit")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP07_ARCHIFY_DELTA_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    delta = load_json(ARTIFACT_PATH)["delta_output"]["actual_authored_facts"]
    print(f"TASK149_STEP07_ARCHIFY_DELTA_OK components={delta['components']['changed']} connections={delta['connections']['changed']} provenance_changed={str(delta['provenance_changed']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
