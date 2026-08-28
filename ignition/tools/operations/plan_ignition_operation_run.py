#!/usr/bin/env python3
"""Plan an Ignition operation run through the canonical lifecycle gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from classify_ignition_run_mode import ModeRoutingError, classify_mode  # noqa: E402


REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"
FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/lifecycle-planning-r1.json"
CORE_CURRENT_READS = (
    "ignition/OPERATING-METHOD.md",
    "ignition/AI-START-HERE.md",
    "ignition/data/architecture/current-facts.json",
    "ignition/data/operations/current-snapshot-r1.json",
    "ignition/data/operations/ignition-operation-capability-registry-r1.json",
)
LIFECYCLE_STAGES = (
    "ACCEPT_REQUEST",
    "FREEZE_CURRENT",
    "CLASSIFY_MODE",
    "CLASSIFY_INPUT_OBJECT",
    "RESOLVE_OPERATION",
    "CHECK_CAPABILITY_STATUS",
    "BUILD_MINIMAL_READ_PLAN",
    "NORMALIZE_INPUT_AND_PROVENANCE",
    "EXECUTE_OPERATION",
    "CANONICAL_COLLISION / EVIDENCE CHECK",
    "ADVERSARIAL_REVIEW",
    "APPLY_CLAIM_CEILING",
    "RENDER_RESULT",
    "STOP / HANDOFF",
)
STATUS_DECISIONS = {
    "CURRENT": ("PROCEED", None),
    "CURRENT_BOUNDED": ("PROCEED_BOUNDED", None),
    "OWNER_DEFERRED": ("STOP", "CAPABILITY_OWNER_DEFERRED"),
    "REFERENCE_ONLY": ("STOP", "CAPABILITY_REFERENCE_ONLY"),
    "HISTORICAL": ("STOP", "CAPABILITY_NOT_CURRENT"),
    "UNSUPPORTED": ("STOP", "UNSUPPORTED_OPERATION"),
}


class RunPlanningError(ValueError):
    """Raised when a run plan request is structurally invalid."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def plan_run(request: dict[str, Any], operation_id: str, current_ref: str) -> dict[str, Any]:
    if not isinstance(operation_id, str) or not operation_id:
        raise RunPlanningError("operation_id must be a nonblank string")
    if not isinstance(current_ref, str) or not current_ref:
        raise RunPlanningError("current_ref must be a nonblank string")
    try:
        mode = classify_mode(request)
    except ModeRoutingError as exc:
        raise RunPlanningError(str(exc)) from exc

    registry = load_json(REGISTRY_PATH)
    operation = next((row for row in registry["operations"] if row["operation_id"] == operation_id), None)
    if operation is None:
        return {
            "lifecycle": list(LIFECYCLE_STAGES),
            "current_ref": current_ref,
            "run_mode": mode["mode"],
            "operation_id": operation_id,
            "operation_status": "UNREGISTERED",
            "decision": "STOP",
            "stop_reason": "UNSUPPORTED_OPERATION",
            "minimal_read_plan": list(CORE_CURRENT_READS),
            "side_effects_authorized_by_plan": False,
        }

    decision, stop_reason = STATUS_DECISIONS[operation["current_status"]]
    expected_mode = operation["default_execution_mode"]
    if expected_mode in {"REPOSITORY_CHANGE_RUN", "EXTERNAL_ACTION_RUN"} and mode["mode"] != expected_mode:
        decision = "STOP"
        stop_reason = "OPERATION_MODE_MISMATCH"
    if mode["reason_code"] == "STOP_SPLIT_OR_CLARIFY":
        decision = "STOP"
        stop_reason = "STOP_SPLIT_OR_CLARIFY"

    reads = _dedupe(
        list(CORE_CURRENT_READS)
        + operation["required_current_reads"]
        + [source["path"] for source in operation["authoritative_sources"]]
        + operation["applicable_governance"]
        + [check["path"] for check in operation["validation_checks"]]
    )
    return {
        "lifecycle": list(LIFECYCLE_STAGES),
        "current_ref": current_ref,
        "run_mode": mode["mode"],
        "mode_reason": mode["reason_code"],
        "operation_id": operation_id,
        "operation_status": operation["current_status"],
        "operation_class": operation["operation_class"],
        "decision": decision,
        "stop_reason": stop_reason,
        "minimal_read_plan": reads,
        "operation_claim_ceiling": operation["claim_ceiling"],
        "known_limits": operation["known_limits"],
        "side_effects_authorized_by_plan": False,
    }


def validate_fixtures(document: dict[str, Any] | None = None) -> list[str]:
    fixtures = document if document is not None else load_json(FIXTURE_PATH)
    errors: list[str] = []
    cases = fixtures.get("cases", []) if isinstance(fixtures, dict) else []
    if not isinstance(cases, list) or not cases:
        return ["lifecycle fixture cases must be a nonempty array"]
    case_ids: list[str] = []
    for case in cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str):
            errors.append("every lifecycle fixture must have a case_id")
            continue
        case_ids.append(case_id)
        try:
            actual = plan_run(case["request"], case["operation_id"], case["current_ref"])
        except (KeyError, RunPlanningError) as exc:
            errors.append(f"{case_id}: planner error: {exc}")
            continue
        for key, expected in case.get("expected", {}).items():
            if actual.get(key) != expected:
                errors.append(f"{case_id}: {key} expected {expected!r}, got {actual.get(key)!r}")
        if actual["minimal_read_plan"][: len(CORE_CURRENT_READS)] != list(CORE_CURRENT_READS):
            errors.append(f"{case_id}: minimum read plan does not start with the canonical core")
        if len(actual["minimal_read_plan"]) != len(set(actual["minimal_read_plan"])):
            errors.append(f"{case_id}: minimum read plan contains duplicates")
        if actual["side_effects_authorized_by_plan"]:
            errors.append(f"{case_id}: planning cannot authorize side effects")
    if len(case_ids) != len(set(case_ids)):
        errors.append("lifecycle fixture case ids must be unique")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-fixtures", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate_fixtures()
    if errors:
        print("IGNITION_OPERATION_LIFECYCLE_FIXTURES_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    cases = load_json(FIXTURE_PATH)["cases"]
    print(f"IGNITION_OPERATION_LIFECYCLE_FIXTURES_OK cases={len(cases)} stages={len(LIFECYCLE_STAGES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
