#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step22 immutable compatibility evidence."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step22-immutable-compatibility-envelope.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step22-immutable-compatibility-envelope-r1.schema.json"
CANONICAL_PATH = ROOT / "data/architecture/overall-architecture.json"
IR_PATH = ROOT / "data/operations/iterations/150/task150-archify-typed-ir-r1.json"
DELIVERY_PATH = ROOT / "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.html"

EXPECTED_STEP21_HEAD = "2affa9334f769c2bc65ffa852cb9c56fc25d5409"
EXPECTED_FORMAL_SOURCE_REVISION = "68d5d30bda0d8eb9c715ac346ce6476a55c0e288"
EXPECTED_CANONICAL_SHA = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
EXPECTED_PROVIDER_REVISION = "06dd052602dd9a369e4d034e24faef0917b5a60c"
EXPECTED_PROVIDER_SCHEMA_SHA = "8c96140b6af8d93fb825a3c63e46b74176c9485185c978074ffe89e0f614576c"
EXPECTED_IR_SHA = "2788796b4d329251cc67e502b6081b77542388b7f25f99470e400bf6722575ed"
EXPECTED_ARTIFACT_SHA = "da7947e408af2839e51fddc90871de30f84b1846ae1d14809a076a40d55daf45"


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

    if document["formal_previous_commit"] != EXPECTED_STEP21_HEAD:
        errors.append("Step22 must start from the proven Step21 formal head")

    provider = document["provider"]
    exact_ref_fields = (
        provider["remote_observation_revision"],
        provider["tested_immutable_ref"],
        provider["checkout_revision"],
    )
    if any(value != EXPECTED_PROVIDER_REVISION for value in exact_ref_fields):
        errors.append("provider compatibility is not bound to the same immutable exact commit")
    if provider["schema_sha256"] != EXPECTED_PROVIDER_SCHEMA_SHA:
        errors.append("provider schema digest drifted")
    if provider["checkout_clean"] is not True or provider["checkout_non_shallow"] is not True:
        errors.append("provider checkout cleanliness or shallow boundary drifted")
    if provider["automatic_update"] is not False or provider["architecture_authority"] is not False:
        errors.append("provider update or architecture-authority boundary widened")

    recheck = document["compatibility_recheck"]
    if recheck["formal_source_revision"] != EXPECTED_FORMAL_SOURCE_REVISION:
        errors.append("compatibility recheck source revision drifted")
    if sha256(CANONICAL_PATH) != EXPECTED_CANONICAL_SHA:
        errors.append("canonical source hash drifted")
    if sha256(IR_PATH) != EXPECTED_IR_SHA or recheck["typed_ir_sha256"] != EXPECTED_IR_SHA:
        errors.append("typed IR compatibility digest drifted")
    ir = load_json(IR_PATH)
    if ir.get("meta", {}).get("repository", {}).get("revision") != EXPECTED_FORMAL_SOURCE_REVISION:
        errors.append("typed IR is not bound to the Step21 source revision")
    if recheck["delivery"]["artifact_sha256"] != EXPECTED_ARTIFACT_SHA or sha256(DELIVERY_PATH) != EXPECTED_ARTIFACT_SHA:
        errors.append("delivered artifact compatibility digest drifted")
    delivery = recheck["delivery"]
    if delivery["specification_sha256"] != EXPECTED_IR_SHA or delivery["source_evidence_revision"] != EXPECTED_FORMAL_SOURCE_REVISION:
        errors.append("delivery compatibility binding drifted")
    if delivery["status"] != "PASS" or delivery["checks_passed"] != 9 or delivery["checks_total"] != 9 or not delivery["source_evidence_verified"]:
        errors.append("delivery compatibility result is incomplete")

    visual = recheck["visual_check"]
    if visual["status"] != "PASS" or visual["visual_review"] != "PENDING_PERCEPTUAL_REVIEW":
        errors.append("visual compatibility result or perceptual boundary drifted")
    if visual["diagnostics"] != 0 or visual["required_containment_viewports"] != 4 or visual["required_capture_screenshots"] != 4:
        errors.append("required compatibility visual observations are incomplete")
    if any(visual[key] != 0 for key in ("containment_failures", "readability_failures", "viewer_chrome_failures")):
        errors.append("compatibility visual failure census is non-zero")
    if not recheck["same_output_as_step21"]:
        errors.append("compatibility output differs from the validated Step21 output")

    policy = document["pin_policy"]
    if policy["tested_compatibility_ref"] != EXPECTED_PROVIDER_REVISION:
        errors.append("pin policy does not use the tested immutable provider revision")
    if not policy["tested_ref_is_immutable_exact_commit"] or not policy["moving_main_is_not_compatibility_binding"]:
        errors.append("pin policy permits a moving ref")
    if policy["automatic_update"] or not policy["future_version_requires_compatibility_check"]:
        errors.append("future-version compatibility policy weakened")

    boundary = document["admission_boundary"]
    if boundary["operation_id"] != "visualization.render_derived_system_view" or not boundary["operation_definition_is_provider_neutral"]:
        errors.append("compatibility receipt changed the provider-neutral operation definition")
    if boundary["compatibility_gate"] != "PASS" or boundary["current_capability"] or boundary["registry_write"]:
        errors.append("compatibility receipt crossed the Current or Registry boundary")
    if boundary["registry_operation_count"] != 19:
        errors.append("Step22 registry count must remain 19")
    if boundary["delta_extension"] != "EXPERIMENTAL_EXTENSION_DEFERRED" or boundary["delta_gate"] != "FAIL_DEFERRED":
        errors.append("Delta was promoted or its blocker relabelled")
    if boundary["owner_aesthetic_endorsement"] != "NOT_GRANTED_NOT_CLAIMED" or boundary["default_renderer"] != "NOT_SELECTED":
        errors.append("aesthetic or default-renderer boundary widened")
    if boundary["architecture_authority"] or boundary["agent_reach"] != "NO_CHANGE" or boundary["authenticated_channel_admission"] != "NO_CHANGE":
        errors.append("authority, Agent Reach or authentication boundary changed")
    if boundary["live_external_invocation"] != "OPEN_OWNER_DEFERRED_NOT_RUN" or boundary["task151"] != "FORBIDDEN":
        errors.append("live invocation or successor-task boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP22_IMMUTABLE_COMPATIBILITY_ENVELOPE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TASK150_STEP22_IMMUTABLE_COMPATIBILITY_ENVELOPE_OK "
        "provider=archify ref=06dd0526 validate=9/9 deliver=9/9 "
        "visual=4/4 current=false registry=19 future_check=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
