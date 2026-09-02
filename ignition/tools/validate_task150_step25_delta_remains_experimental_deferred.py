#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step25's independent Delta deferral."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step25-delta-remains-experimental-deferred.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step25-delta-remains-experimental-deferred-r1.schema.json"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"
STEP04_PATH = ROOT / "data/operations/iterations/150/step04-viewport-residual-repair.json"
STEP07_PATH = ROOT / "data/operations/iterations/150/step07-architecture-delta-smoke.json"
STEP22_PATH = ROOT / "data/operations/iterations/150/step22-immutable-compatibility-envelope.json"

EXPECTED_PREVIOUS_COMMIT = "958292bf4fb438ef4458e0403774466bde5ccaf7"
EXPECTED_STEP04_SHA = "9c80133dd55d0d771ea3538e5a8495b863b78c6d0a7abc2c9b8207c263ecb2ce"
EXPECTED_STEP07_SHA = "9d4e553b577374aeaa1f3c295ad5d0c936b17519241cad5a905ba79bf28d4a58"
EXPECTED_STEP22_SHA = "db7d5aa2efd64572e80c12b578b7b392a0307263f3a848039902f848f37d2bdd"
EXPECTED_DELTA_ARTIFACTS = {
    "ignition/data/operations/iterations/150/delta-evidence/task150-delta-receipt.json": "a41f4486eb88454da4dd37adb6d85593a07146a39179c5760a9b6f4b5007f7b1",
    "ignition/data/operations/iterations/150/delta-evidence/task150-delta.html": "0c03203600ea496e2d7b015c181b673f9e9e489b6c4141878c56551d3999390a",
    "ignition/data/operations/iterations/150/delta-evidence/task150-delta-visual-check.json": "f5d96d9bd6f19c06f517804783cefdaddddaae55fa8d3316c5159ef586ba0d50",
}


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
        errors.append("Step25 must start from the pushed Step24 formal head")

    evidence = document["evidence"]
    step04 = evidence["step04_blocker_receipt"]
    step07 = evidence["step07_delta_smoke_receipt"]
    step22 = evidence["step22_compatibility_receipt"]
    for path, expected in ((STEP04_PATH, EXPECTED_STEP04_SHA), (STEP07_PATH, EXPECTED_STEP07_SHA), (STEP22_PATH, EXPECTED_STEP22_SHA)):
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"historical receipt hash drifted: {path.relative_to(REPO_ROOT)}")

    actual_step04 = load_json(STEP04_PATH)
    if actual_step04["status"] != "UPSTREAM_BLOCKER_RECORDED":
        errors.append("Step04 historical blocker was relabelled")
    if actual_step04["repair_validation"]["delta_visual_check"]["status"] != "FAIL_UPSTREAM_WRAPPER":
        errors.append("Step04 Delta visual blocker was relabelled")
    if actual_step04["repair_validation"]["delta_visual_check"]["diagnostics"] != 3:
        errors.append("Step04 Delta diagnostic count drifted")
    if not actual_step04["upstream_blocker"]["confirmed"]:
        errors.append("Step04 upstream blocker was not retained")
    if step04["sha256"] != EXPECTED_STEP04_SHA:
        errors.append("Step04 receipt digest in Step25 drifted")

    from tools.validate_task150_step07_architecture_delta_smoke import validate as validate_step07  # noqa: E402

    step07_errors = validate_step07()
    if step07_errors:
        errors.append("retained Step07 validator failed: " + "; ".join(step07_errors))
    actual_step07 = load_json(STEP07_PATH)
    semantic = actual_step07["comparison"]["semantic_classification"]
    delta_visual = actual_step07["comparison"]["delta_visual"]
    if semantic["checks_passed"] != 28 or semantic["check_count"] != 28 or not semantic["provenance_changed"] or semantic["presentation_changed"]:
        errors.append("Step07 semantic provenance-only result drifted")
    if delta_visual["status"] != "FAIL_UPSTREAM_WRAPPER" or delta_visual["diagnostics"] != 3:
        errors.append("Step07 Delta visual blocker or diagnostic count drifted")
    if step07["semantic_checks_passed"] != 28 or step07["semantic_checks_total"] != 28 or step07["historical_validator"] != "PASS":
        errors.append("Step25 Step07 summary is not the retained 28/28 pass")

    actual_step22 = load_json(STEP22_PATH)
    if actual_step22["provider"]["tested_immutable_ref"] != "06dd052602dd9a369e4d034e24faef0917b5a60c":
        errors.append("Step22 immutable provider compatibility ref drifted")
    if actual_step22["admission_boundary"]["delta_extension"] != "EXPERIMENTAL_EXTENSION_DEFERRED" or actual_step22["admission_boundary"]["delta_gate"] != "FAIL_DEFERRED":
        errors.append("Step22 historical Delta gate was relabelled")
    if actual_step22["admission_boundary"]["registry_operation_count"] != 19:
        errors.append("Step22 historical Registry boundary was rewritten")
    if step22["sha256"] != EXPECTED_STEP22_SHA:
        errors.append("Step22 receipt digest in Step25 drifted")

    for item in evidence["immutable_delta_artifacts"]:
        expected = EXPECTED_DELTA_ARTIFACTS.get(item["path"])
        path = REPO_ROOT / item["path"]
        if expected is None:
            errors.append(f"unexpected Delta artifact in Step25: {item['path']}")
        elif not path.is_file() or sha256(path) != expected or item["sha256"] != expected:
            errors.append(f"immutable Delta artifact hash drifted: {item['path']}")

    registry = load_json(REGISTRY_PATH)
    operation_ids = [row["operation_id"] for row in registry.get("operations", [])]
    if any("delta" in operation_id.lower() for operation_id in operation_ids):
        errors.append("Architecture Delta operation was registered")
    if any("archify" in operation_id.lower() for operation_id in operation_ids):
        errors.append("provider-specific Archify operation was registered")
    if document["delta_gate"]["extension"] != "EXPERIMENTAL_EXTENSION_DEFERRED" or document["delta_gate"]["delta_operation_registered"]:
        errors.append("Step25 promoted or registered the Delta extension")
    if not document["delta_gate"]["base_gate_is_independent"] or not document["delta_gate"]["delta_does_not_block_base"]:
        errors.append("Step25 accidentally coupled the Delta gate to the base gate")
    if document["delta_gate"]["visual_result"] != "FAIL_UPSTREAM_WRAPPER" or document["delta_gate"]["diagnostics"] != 3:
        errors.append("Step25 Delta blocker census drifted")

    preserved = document["preserved_boundaries"]
    if not preserved["step14_defer_preserved"] or not preserved["step15_draft_stop_preserved"] or not preserved["no_historical_evidence_rewritten"]:
        errors.append("historical Step14/15 or evidence immutability boundary changed")
    if preserved["default_renderer"] != "NOT_SELECTED" or preserved["architecture_authority"] or preserved["provider_authority"]:
        errors.append("renderer or authority boundary widened")
    if preserved["agent_reach"] != "NO_CHANGE" or preserved["authenticated_channel_admission"] != "NO_CHANGE":
        errors.append("Agent Reach or authentication boundary changed")
    if preserved["live_external_invocation"] != "OPEN_OWNER_DEFERRED_NOT_RUN" or preserved["task151"] != "FORBIDDEN":
        errors.append("live invocation or Task151 boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP25_DELTA_REMAINS_EXPERIMENTAL_DEFERRED_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP25_DELTA_REMAINS_EXPERIMENTAL_DEFERRED_OK semantic=28/28 visual=FAIL_UPSTREAM_WRAPPER diagnostics=3 delta=EXPERIMENTAL_EXTENSION_DEFERRED base_independent=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
