#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step08 provider fallback evidence."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step08-provider-failure-fallback.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step08-provider-failure-fallback-r1.schema.json"
CANONICAL_PATH = ROOT / "data/architecture/overall-architecture.json"
SYSTEM_MAP_PATH = ROOT / "data/architecture/interactive-system-map.json"

EXPECTED_CASES = {
    "archify-command-unavailable": ("provider_command_discovery", "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT"),
    "node-unavailable": ("runtime_discovery", "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT"),
    "schema-fail": ("provider_schema_validation", "BOUNDED_PROVIDER_FAILURE"),
    "validation-fail": ("derived_ir_validation", "BOUNDED_PROVIDER_FAILURE"),
    "deliver-fail": ("derived_artifact_delivery", "BOUNDED_PROVIDER_FAILURE"),
    "visual-containment-fail": ("visual_containment_validation", "BOUNDED_PROVIDER_FAILURE"),
    "upstream-version-mismatch": ("provider_revision_admission", "BOUNDED_PROVIDER_FAILURE"),
}
EXPECTED_ARCH_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_MAP_SHA = "3824697a9c781c1ea825f7335bc9461e6fb693e70bb65c042309fd16da173313"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simulated_result(case_id: str) -> str:
    if case_id in {"archify-command-unavailable", "node-unavailable"}:
        return "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT"
    return "BOUNDED_PROVIDER_FAILURE"


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if errors:
        return errors
    if document["failure_injection"]["real_provider_process_started"] is not False or document["failure_injection"]["system_mutation"] is not False:
        errors.append("failure matrix must not start a provider or mutate the system")
    if sha256(CANONICAL_PATH) != EXPECTED_ARCH_SHA or sha256(SYSTEM_MAP_PATH) != EXPECTED_MAP_SHA:
        errors.append("canonical or last-known map hash drifted")
    preservation = document["canonical_preservation"]
    if preservation["architecture_before_sha256"] != preservation["architecture_after_sha256"] or preservation["last_known_map_before_sha256"] != preservation["last_known_map_after_sha256"]:
        errors.append("failure handling did not preserve canonical inputs")
    seen = set()
    for case in document["cases"]:
        case_id = case["id"]
        seen.add(case_id)
        expected = EXPECTED_CASES.get(case_id)
        if expected is None:
            errors.append(f"unknown failure case: {case_id}")
            continue
        if (case["failure_stage"], case["expected"]) != expected:
            errors.append(f"failure case expectation drifted: {case_id}")
        if case["observed"] != simulated_result(case_id):
            errors.append(f"failure case result is not the bounded typed result: {case_id}")
        if case["canonical_preserved"] is not True or case["last_known_map_preserved"] is not True:
            errors.append(f"fallback preservation missing: {case_id}")
    if seen != set(EXPECTED_CASES):
        errors.append("failure matrix does not cover exactly the seven required stages")
    scope = document["scope_freeze"]
    if scope["agent_reach"] != "NO_CHANGE" or scope["installation"] != "NO_INSTALL_OR_AUTO_UPGRADE":
        errors.append("Agent Reach or installation scope changed")
    if scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("authentication or live invocation boundary changed")
    if scope["current_admission"] != "NOT_ADMITTED":
        errors.append("failure fallback cannot admit a Current capability")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP08_PROVIDER_FAILURE_FALLBACK_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP08_PROVIDER_FAILURE_FALLBACK_OK cases=7/7 canonical_preserved=true last_known_map_preserved=true provider=REPLACEABLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
