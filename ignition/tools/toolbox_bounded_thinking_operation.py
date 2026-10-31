#!/usr/bin/env python3
"""Select one bounded next thinking operation from caller-declared run state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
MAX_STDIN_BYTES = 262144
INPUT_SCHEMA_PATH = ROOT / "ignition/schemas/operations/toolbox-bounded-thinking-operation-input-r0.schema.json"
OUTPUT_SCHEMA_PATH = ROOT / "ignition/schemas/operations/toolbox-bounded-thinking-operation-output-r0.schema.json"

class DecisionError(ValueError):
    """Raised when caller-declared state is inconsistent or invalid."""


def _load_schema(path: Path) -> dict[str, Any]:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DecisionError(f"cannot load schema: {path.name}") from exc
    Draft202012Validator.check_schema(schema)
    return schema


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DecisionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _validate_input(data: Any) -> dict[str, Any]:
    schema = _load_schema(INPUT_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "input"
        raise DecisionError(f"{location}: {error.message}")
    state = data["state"]
    failures = state["failure_refs"]
    first_failure = state["first_failure_ref"]
    if failures and first_failure != failures[0]:
        raise DecisionError("first_failure_ref must preserve the earliest failure_refs entry")
    if not failures and first_failure is not None:
        raise DecisionError("first_failure_ref must be null when failure_refs is empty")
    assessment_operations = [item["operation"] for item in data["candidate_assessments"]]
    if len(assessment_operations) != len(set(assessment_operations)):
        raise DecisionError("candidate_assessments must contain at most one entry per operation")
    if not set(assessment_operations) <= set(data["available_operations"]):
        raise DecisionError("candidate assessments must be a subset of available_operations")
    return data


def _output(
    data: dict[str, Any],
    *,
    operation: str,
    terminal: str | None,
    reasons: list[str],
    refs: list[str],
    assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = data["state"]
    result = {
        "schema_version": "toolbox-bounded-thinking-operation-output-r0",
        "episode_id": data["task"]["episode_id"],
        "state_ref": state["state_ref"],
        "selected_operation": operation,
        "terminal_disposition": terminal,
        "reason_codes": list(dict.fromkeys([
            *reasons,
            *(["FIRST_FAILURE_PRESERVED"] if state["first_failure_ref"] is not None else []),
        ])),
        "reason_refs": list(dict.fromkeys([*refs, *state["failure_refs"]])),
        "expected_state_delta": assessment["expected_state_delta"] if assessment else None,
        "expected_value_status": assessment["expected_value_status"] if assessment else "NOT_APPLICABLE",
        "expected_value_band": assessment["expected_value_band"] if assessment else None,
        "expected_cost_band": assessment["expected_cost_band"] if assessment else None,
        "estimated_cost_units": assessment["estimated_cost_units"] if assessment else None,
        "cost_basis": "CALLER_DECLARED_ABSTRACT_UNITS_NOT_MEASURED",
        "return_condition": (
            assessment["return_condition"]
            if assessment
            else "Return this terminal disposition to the caller; do not continue or execute another operation automatically."
        ),
        "first_failure_ref": state["first_failure_ref"],
        "authority_effect": "NONE",
        "execution_authorized": False,
        "permission_expanded": False,
        "source_evidence_mutated": False,
        "frame_changed": False,
        "claim_ceiling": "CALLER_STATE_BASED_OPERATION_RECOMMENDATION_ONLY",
    }
    schema = _load_schema(OUTPUT_SCHEMA_PATH)
    errors = list(Draft202012Validator(schema).iter_errors(result))
    if errors:
        raise DecisionError(f"internal output schema violation: {errors[0].message}")
    return result


def _stop(
    data: dict[str, Any],
    terminal: str,
    reason: str,
    refs: list[str] | None = None,
    extra_reasons: list[str] | None = None,
) -> dict[str, Any]:
    reasons = [reason, *(extra_reasons or [])]
    if data["state"]["first_failure_ref"] is not None:
        reasons.append("FIRST_FAILURE_PRESERVED")
    return _output(data, operation="STOP", terminal=terminal, reasons=reasons, refs=refs or [])


def select_bounded_thinking_operation(raw_data: Any) -> dict[str, Any]:
    """Return one rule-based operation suggestion or a bounded terminal stop."""
    data = _validate_input(raw_data)
    state = data["state"]
    obligations = state["required_obligations"]
    open_required = [item for item in obligations if item["required"] and item["status"] != "RESOLVED"]
    open_any = [item for item in obligations if item["status"] != "RESOLVED"]
    verification_open = [item for item in open_required if item["verification_required"]]
    obligation_refs = [item["obligation_ref"] for item in open_any]

    target: str | None = None
    reason: str | None = None
    terminal_if_unavailable = "EXPLICIT_GAP"
    if state["authority_missing"]:
        target, reason = "REQUEST_OWNER_DECISION", "AUTHORITY_DEFICIT"
        terminal_if_unavailable = "OWNER_DECISION_REQUIRED"
    elif state["frame_unresolved"]:
        target, reason = "REFRAME_OR_CLARIFY", "FRAME_UNRESOLVED"
        terminal_if_unavailable = "FRAME_UNRESOLVED"
    elif state["capability_missing"]:
        target, reason = "CAPACITY_OR_EXECUTOR_ESCALATE", "CAPABILITY_DEFICIT"
        terminal_if_unavailable = "CAPABILITY_BLOCKED"
    elif verification_open:
        target, reason = "VERIFY", "REQUIRED_VERIFICATION_OPEN"
        terminal_if_unavailable = "VERIFICATION_CEILING"
    elif state["decomposition_needed"]:
        target, reason = "DECOMPOSE", "DECOMPOSITION_NEEDED"
    elif state["freshness_gap"]:
        target, reason = "READ_MORE", "FRESHNESS_GAP"
    elif open_required:
        target, reason = "READ_MORE", "REQUIRED_OBLIGATION_OPEN"
    elif open_any:
        return _stop(data, "EXPLICIT_GAP", "OPTIONAL_GAP_REMAINS", refs=obligation_refs)

    if target is None:
        return _stop(
            data,
            "SUFFICIENT",
            "DECLARED_REQUIREMENTS_MET",
            refs=[*obligation_refs, *state["uncertainty_refs"]],
        )

    if target not in data["available_operations"]:
        return _stop(
            data,
            terminal_if_unavailable,
            "REQUIRED_OPERATION_UNAVAILABLE",
            refs=[*obligation_refs, *state["uncertainty_refs"]],
            extra_reasons=[reason],
        )
    assessment = next(
        (item for item in data["candidate_assessments"] if item["operation"] == target),
        None,
    )
    if assessment is None:
        return _stop(
            data,
            terminal_if_unavailable,
            "REQUIRED_OPERATION_UNAVAILABLE",
            refs=[*obligation_refs, *state["uncertainty_refs"]],
            extra_reasons=[reason],
        )
    missing_capabilities = set(assessment["required_capabilities"]) - set(data["available_capabilities"])
    if missing_capabilities:
        return _stop(
            data,
            "CAPABILITY_BLOCKED",
            "REQUIRED_CAPABILITY_UNAVAILABLE",
            refs=[*obligation_refs, *state["uncertainty_refs"]],
            extra_reasons=[reason],
        )
    if assessment["estimated_cost_units"] > state["remaining_budget_units"]:
        return _stop(
            data,
            "BUDGET_EXHAUSTED",
            "BUDGET_EXHAUSTED",
            refs=[*obligation_refs, *state["uncertainty_refs"]],
            extra_reasons=[reason],
        )
    if assessment["expected_value_status"] != "POSITIVE":
        return _stop(
            data,
            terminal_if_unavailable,
            "EXPECTED_VALUE_NOT_POSITIVE",
            refs=[*obligation_refs, *state["uncertainty_refs"]],
            extra_reasons=[reason],
        )
    repeated_without_change = any(
        history["operation"] == target
        and history["state_ref"] == state["state_ref"]
        and history["outcome"] in {"NO_STATE_CHANGE", "FAILED"}
        for history in state["operation_history"]
    )
    if repeated_without_change:
        return _stop(
            data,
            terminal_if_unavailable,
            "REPEATED_OPERATION_WITHOUT_STATE_CHANGE",
            refs=[*obligation_refs, *state["uncertainty_refs"]],
            extra_reasons=[reason],
        )
    return _output(
        data,
        operation=target,
        terminal=None,
        reasons=[reason],
        refs=[*assessment["reason_refs"], *obligation_refs, *state["uncertainty_refs"]],
        assessment=assessment,
    )


def _read_stdin() -> Any:
    raw = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    if len(raw) > MAX_STDIN_BYTES:
        raise DecisionError(f"stdin exceeds {MAX_STDIN_BYTES} bytes")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DecisionError("stdin must contain one UTF-8 JSON value") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded JSON request from stdin")
    parser.parse_args(argv)
    try:
        result = select_bounded_thinking_operation(_read_stdin())
    except DecisionError as exc:
        print(json.dumps({"status": "INVALID_INPUT", "message": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
