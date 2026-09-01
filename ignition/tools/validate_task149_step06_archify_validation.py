#!/usr/bin/env python3
"""Validate the Task149 Step06 Archify provider-bound receipt."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step06-archify-validation-receipt.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step06-archify-validation-r0.schema.json"
ARCHITECTURE_PATH = ROOT / "data/architecture/overall-architecture.json"
SYSTEM_MAP_PATH = ROOT / "data/architecture/interactive-system-map.json"
IR_PATH = ROOT / "data/operations/iterations/149/archify-typed-ir-r0.json"

EXPECTED_FORMAL_COMMIT = "c27bca66e154a68f6fa0d819edcdd02ee2414c6d"
EXPECTED_ARTIFACT_SHA256 = "978008823b3941622a8ba21e751913f37d8c87310e28b46c5bca6f17db913017"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_commit") != EXPECTED_FORMAL_COMMIT:
        errors.append("Step06 must bind the published Step05 formal commit")

    source_paths = {
        "ignition/data/architecture/overall-architecture.json": ARCHITECTURE_PATH,
        "ignition/data/architecture/interactive-system-map.json": SYSTEM_MAP_PATH,
    }
    observed_sources = {item.get("path"): item for item in document.get("source_inputs", [])}
    for relative, path in source_paths.items():
        if observed_sources.get(relative, {}).get("sha256") != digest(path):
            errors.append(f"source hash mismatch: {relative}")

    typed = document.get("typed_ir", {})
    if typed.get("sha256") != digest(IR_PATH):
        errors.append("typed IR hash does not match the formal IR")
    if typed.get("bytes") != IR_PATH.stat().st_size:
        errors.append("typed IR byte count does not match the formal IR")

    commands = document.get("commands", {})
    validate_command = commands.get("validate", {})
    deliver_command = commands.get("deliver", {})
    visual_command = commands.get("visual_check", {})
    if validate_command.get("status") != "PASS" or validate_command.get("errors") != 0 or validate_command.get("warnings") != 0:
        errors.append("Archify validate receipt must be a warning-free PASS")
    if deliver_command.get("status") != "PASS" or deliver_command.get("artifact_sha256") != EXPECTED_ARTIFACT_SHA256:
        errors.append("Archify deliver receipt must bind the expected artifact PASS")
    if visual_command.get("status") != "PASS" or visual_command.get("diagnostics_count") != 0:
        errors.append("Archify visual-check receipt must be a diagnostic-free PASS")
    if len(visual_command.get("light_containment_viewports", [])) != 4:
        errors.append("visual-check must retain all four light containment viewports")
    if len(visual_command.get("dark_capture_viewports", [])) != 2:
        errors.append("visual-check must retain both captured dark viewports")
    if len(visual_command.get("screenshots", [])) != 4:
        errors.append("visual-check must retain four screenshot hashes")

    artifact = document.get("artifact", {})
    if artifact.get("status") != "NOT_COMMITTED" or artifact.get("sha256") != deliver_command.get("artifact_sha256"):
        errors.append("the uncommitted artifact status/hash must remain bound to deliver")
    boundaries = document.get("boundaries", {})
    if boundaries.get("current_integration") != "NOT_CURRENT_INTEGRATION":
        errors.append("Step06 must not claim Current integration")
    if boundaries.get("provider_output_can_update_canonical_truth") is not False:
        errors.append("provider output must remain unable to update canonical truth")
    if boundaries.get("provider_permission_granted") is not False:
        errors.append("Step06 must not grant provider permission")
    if boundaries.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("authenticated-channel admission must remain closed")
    if boundaries.get("live_external_invocation") != "UNCHANGED_OPEN_OWNER_DEFERRED":
        errors.append("live external invocation must remain unchanged and deferred")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP06_ARCHIFY_VALIDATION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    commands = load_json(ARTIFACT_PATH)["commands"]
    artifact = commands["deliver"]["artifact_sha256"]
    print(f"TASK149_STEP06_ARCHIFY_VALIDATION_OK validate=PASS deliver=PASS visual_check=PASS artifact={artifact[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
