#!/usr/bin/env python3
"""Validate the provider-neutral Task149 Contract R0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/provider-adapter-contract-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/provider-adapter-contract-r0.schema.json"

EXPECTED_BASELINE = "2e563b904cdf1ad57949f649a93cfec0926094ca"
EXPECTED_FREEZE_SHA = "956fb9d77667cec8c346b19264fb7b76cd1ddaa911a661efc311c02fd8ff2ecf"
EXPECTED_CLASSES = {"DERIVED_VISUALIZATION_PROVIDER", "READ_ONLY_SOURCE_ACQUISITION_PROVIDER"}
EXPECTED_RESEARCH_SCOPE = "EXPERIMENTAL_PROVIDER_ADMISSION_RESEARCH_ONLY"
EXPECTED_RUNTIME_INTERFACE_STATUS = "NOT_A_CURRENT_RUNTIME_PROVIDER_INTERFACE"
EXPECTED_INVARIANTS = [
    "EXTERNAL_PROVIDER ≠ IGNITION_AUTHORITY",
    "PROVIDER_CAPABILITY ≠ PERMISSION",
    "PROVIDER_OUTPUT ≠ EXTERNAL_TRUTH",
    "PROVIDER_LOCAL_POLICY ≠ IGNITION_GLOBAL_POLICY",
    "ADAPTER_SPIKE_PASS ≠ CURRENT_CAPABILITY",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    schema = load_json(SCHEMA_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(schema).iter_errors(document)]
    if document.get("formal_baseline_sha") != EXPECTED_BASELINE:
        errors.append("contract must be based on the published Step02 formal commit")
    freeze = document.get("upstream_freeze", {})
    if freeze.get("artifact_sha256") != EXPECTED_FREEZE_SHA:
        errors.append("contract must bind the exact Step02 freeze artifact")
    if document.get("provider_neutral") is not True:
        errors.append("provider-neutral marker must remain true")
    if document.get("research_scope") != EXPECTED_RESEARCH_SCOPE:
        errors.append("contract must remain explicitly experimental provider-admission research only")
    if document.get("runtime_interface_status") != EXPECTED_RUNTIME_INTERFACE_STATUS:
        errors.append("contract must not be treated as a Current runtime provider interface")
    classes = {entry.get("provider_class") for entry in document.get("provider_classes", [])}
    if classes != EXPECTED_CLASSES:
        errors.append("both required provider classes must remain present")
    if document.get("authority_invariants") != EXPECTED_INVARIANTS:
        errors.append("authority invariants must remain exact and ordered")
    if document.get("selection_authority", {}).get("owner") != "IGNITION":
        errors.append("Ignition must own provider selection")
    records = {entry.get("provider_id"): entry for entry in document.get("provider_records", [])}
    for provider_id in ("archify", "agent-reach"):
        if provider_id not in records:
            errors.append(f"required candidate record missing: {provider_id}")
    for provider_id, record in records.items():
        if record.get("current_integration", {}).get("status") != "NOT_CURRENT_INTEGRATION":
            errors.append(f"{provider_id} must not be a Current integration")
        if record.get("current_integration", {}).get("pack_permission_change") is not False:
            errors.append(f"{provider_id} must not expand Pack permissions")
        if record.get("authentication_requirement", {}).get("authenticated_channel_admission") != "NOT_GRANTED":
            errors.append(f"{provider_id} must not admit authenticated channels")
        if record.get("provider_local_policy_not_inherited", {}).get("inherited") is not False:
            errors.append(f"{provider_id} provider-local policy must not be inherited")
        if record.get("discovery_method", {}).get("source_copied_into_ignition") is not False:
            errors.append(f"{provider_id} source must not be copied into Ignition")
        if record.get("install_requirement", {}).get("task_local_install_performed") is not False:
            errors.append(f"{provider_id} must not report an install performed in Step03")
    if document.get("global_admission_summary", {}).get("status") != "PROVIDER_ADMISSION_CANDIDATE":
        errors.append("global status must remain PROVIDER_ADMISSION_CANDIDATE")
    if document.get("global_admission_summary", {}).get("live_external_invocation") != "LIVE_EXTERNAL_INVOCATION_UNCHANGED":
        errors.append("live external invocation must remain unchanged")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_PROVIDER_CONTRACT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    records = load_json(ARTIFACT_PATH)["provider_records"]
    print(f"TASK149_PROVIDER_CONTRACT_OK records={len(records)} classes={len(EXPECTED_CLASSES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
