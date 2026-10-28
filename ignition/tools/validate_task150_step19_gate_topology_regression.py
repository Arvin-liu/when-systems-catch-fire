#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step19's independent gate topology."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step19-gate-topology-regression.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step19-gate-topology-regression-r1.schema.json"
HISTORICAL_STEP11_PATH = ROOT / "data/operations/iterations/150/step11-capability-registry-candidate-gate.json"

EXPECTED_PREVIOUS_COMMIT = "1ca874d5994372713b0745ae1ccc699da862c9a3"
EXPECTED_HISTORICAL_STEP11_SHA = "fee253fd361c0e312f401762d370cfa333f34ced946aad178aa81888bb9b9866"
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
        errors.append("Step19 must start from the pushed Step18 formal head")
    historical = document["historical_step11"]
    if sha256(HISTORICAL_STEP11_PATH) != EXPECTED_HISTORICAL_STEP11_SHA or historical["artifact_sha256"] != EXPECTED_HISTORICAL_STEP11_SHA:
        errors.append("historical Step11 evidence changed or its fingerprint drifted")
    if historical["retained_as_historical"] is not True or historical["rewritten"] is not False:
        errors.append("historical combined-model evidence was not preserved")

    topology = document["gate_topology"]
    base = topology["base_operation"]
    if base["gate_ids"] != EXPECTED_BASE_GATE_IDS:
        errors.append(f"base gate topology drifted: expected={EXPECTED_BASE_GATE_IDS!r} observed={base['gate_ids']!r}")
    if "delta_viewport_containment_zero_failure" in base["gate_ids"]:
        errors.append("Delta viewport gate leaked back into the base operation")
    if "owner_aesthetic_acceptance" in base["gate_ids"] or "owner_aesthetic_endorsement" in base["gate_ids"]:
        errors.append("Owner aesthetic endorsement leaked into the functional base gate")
    if base["delta_gate_included"] or base["owner_aesthetic_gate_included"]:
        errors.append("base gate family is not independent")
    if base["standalone_viewport_gate_is_independent"] is not True:
        errors.append("standalone viewport gate is not independent")

    delta = topology["delta_extension"]
    if delta["gate_ids"] != ["delta_viewport_containment_zero_failure"]:
        errors.append("Delta gate family changed")
    if delta["current_result"] != "FAIL_DEFERRED" or delta["separate_admission_required"] is not True:
        errors.append("Delta was incorrectly promoted")
    if delta["base_gate_included"] or delta["base_pass_promotes_delta"]:
        errors.append("Delta promotion guard widened")

    cases = {case["id"]: case for case in document["regression_cases"]}
    required_cases = {"standalone_pass_delta_fail", "standalone_fail_delta_pass", "delta_repaired_base_pass", "aesthetic_endorsement_absent"}
    if set(cases) != required_cases:
        errors.append(f"split regression cases drifted: expected={required_cases!r} observed={set(cases)!r}")
    else:
        pass_delta_fail = cases["standalone_pass_delta_fail"]
        if pass_delta_fail["delta_gate_result"] != "FAIL" or pass_delta_fail["expected_base_admission"] != "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE" or pass_delta_fail["expected_delta_admission"] != "DEFER":
            errors.append("standalone PASS + Delta FAIL does not admit only the base candidate")
        fail_delta_pass = cases["standalone_fail_delta_pass"]
        if fail_delta_pass["base_gate_results"]["standalone_viewport_containment_zero_failure"] != "FAIL" or fail_delta_pass["delta_gate_result"] != "PASS" or fail_delta_pass["expected_base_admission"] != "DEFER":
            errors.append("standalone FAIL + Delta PASS did not fail closed for base")
        repaired = cases["delta_repaired_base_pass"]
        if repaired["expected_delta_admission"] != "SEPARATE_ADMISSION_REQUIRED":
            errors.append("repaired Delta auto-promoted")
        aesthetic = cases["aesthetic_endorsement_absent"]
        if aesthetic.get("expected_aesthetic_claim") != "NOT_CLAIMED" or aesthetic["expected_base_admission"] != "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE":
            errors.append("missing aesthetic endorsement incorrectly blocks or accepts an aesthetic claim")
        if any(case["live_evidence"] is not False for case in cases.values()):
            errors.append("synthetic policy fixture was relabelled as live evidence")

    current = document["current_state"]
    if current["registry_operation_count"] != 19 or current["registry_write_in_step19"]:
        errors.append("Step19 changed the Current Registry")
    if current["base_operation_current"] or current["delta_current"]:
        errors.append("Step19 promoted an operation to Current")
    if current["default_renderer"] != "NOT_SELECTED" or current["agent_reach"] != "NO_CHANGE":
        errors.append("default renderer or Agent Reach changed")
    if current["authenticated_channel_admission"] != "NO_CHANGE" or current["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("authentication or live invocation changed")
    if current["task151"] != "FORBIDDEN":
        errors.append("Task151 guard changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP19_GATE_TOPOLOGY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP19_GATE_TOPOLOGY_OK base_independent=true delta=DEFER synthetic_cases=4 registry=19")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
