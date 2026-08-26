"""Offline conformance harness for the provider-neutral executor boundary."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from .structured_result_contract import StructuredResultContractError, extract_synthetic_result


EXPECTED_RESULT = {
    "nonce": "0123456789abcdef01234567",
    "line_count": 3,
    "field_value": "task142-fixture",
    "checksum_prefix": "abcdef01",
}
EXPECTED_CASES = (
    "exact_valid",
    "malformed_json",
    "extra_field",
    "wrong_result",
    "nonzero_exit",
    "timeout",
    "child_cleanup_failure",
    "workspace_mutation",
    "runtime_scratch_leak",
    "capture_incomplete",
    "redaction_failure",
)


def _event(result: Any = EXPECTED_RESULT) -> list[dict[str, Any]]:
    if isinstance(result, str):
        text = result
    else:
        text = json.dumps(result, sort_keys=True)
    return [{"type": "fixture.completed", "item": {"type": "agent_message", "text": text}}]


def _base_case(case_id: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "process_exit_code": 0,
        "timed_out": False,
        "events": _event(),
        "child_cleanup": True,
        "workspace_unchanged": True,
        "runtime_scratch_clean": True,
        "capture_complete": True,
        "redaction_pass": True,
    }


def fixture_cases() -> list[dict[str, Any]]:
    cases = {case_id: _base_case(case_id) for case_id in EXPECTED_CASES}
    cases["malformed_json"]["events"] = _event('{"nonce":')
    cases["extra_field"]["events"] = _event({**EXPECTED_RESULT, "unexpected": "rejected"})
    cases["wrong_result"]["events"] = _event({**EXPECTED_RESULT, "line_count": 4})
    cases["nonzero_exit"]["process_exit_code"] = 1
    cases["timeout"]["timed_out"] = True
    cases["child_cleanup_failure"]["child_cleanup"] = False
    cases["workspace_mutation"]["workspace_unchanged"] = False
    cases["runtime_scratch_leak"]["runtime_scratch_clean"] = False
    cases["capture_incomplete"]["capture_complete"] = False
    cases["redaction_failure"]["redaction_pass"] = False
    return [cases[case_id] for case_id in EXPECTED_CASES]


def evaluate_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate one offline case in the same order as a live completion gate."""

    case_id = str(case.get("case_id", "UNKNOWN"))
    reasons: list[str] = []
    parsed: Mapping[str, Any] | None = None
    if case.get("timed_out"):
        reasons.append("TIMEOUT_EFFECT_UNKNOWN")
    if case.get("process_exit_code") != 0:
        reasons.append("PROCESS_EXIT_NONZERO")
    if not case.get("capture_complete"):
        reasons.append("CAPTURE_INCOMPLETE")
    if not case.get("redaction_pass"):
        reasons.append("REDACTION_GATE_FAILED")
    if not case.get("child_cleanup"):
        reasons.append("CHILD_CLEANUP_FAILED")
    if not case.get("workspace_unchanged"):
        reasons.append("WORKSPACE_MUTATED")
    if not case.get("runtime_scratch_clean"):
        reasons.append("RUNTIME_SCRATCH_LEAK")
    if not reasons:
        try:
            evidence = extract_synthetic_result(case.get("events", []))
            parsed = dict(evidence.value)
            if parsed != EXPECTED_RESULT:
                reasons.append("STRUCTURED_RESULT_SEMANTIC_MISMATCH")
        except StructuredResultContractError as exc:
            reasons.append(exc.code)
    accepted = not reasons
    return {
        "case_id": case_id,
        "decision": "CONFORMANCE_PASS" if accepted else "REJECTED",
        "validated_completion": accepted,
        "reasons": sorted(set(reasons)),
        "structured_result_digest": hashlib.sha256(json.dumps(parsed or {}, sort_keys=True).encode("utf-8")).hexdigest(),
        "claim_ceiling": "Offline synthetic conformance behavior only; no external process, executor capability or live completion is claimed.",
    }


def run_matrix() -> dict[str, Any]:
    rows = [evaluate_case(case) for case in fixture_cases()]
    expected_rejections = {row["case_id"] for row in rows if not row["validated_completion"]}
    return {
        "schema_version": "executor-conformance-matrix-r1",
        "contract_id": "OFFLINE_EXECUTOR_CONFORMANCE_MATRIX",
        "case_order": list(EXPECTED_CASES),
        "cases": rows,
        "summary": {
            "case_count": len(rows),
            "accepted_count": sum(row["validated_completion"] for row in rows),
            "rejected_count": len(expected_rejections),
            "expected_rejection_count": len(EXPECTED_CASES) - 1,
            "live_process_started": False,
            "child_processes_left": 0,
            "formal_workspace_mutated": False,
            "runtime_scratch_leaked": False,
        },
        "claim_ceiling": "Offline synthetic conformance behavior only; all rejected cases remain rejected and no result is promoted to live completion.",
    }


def validate_matrix(matrix: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if tuple(matrix.get("case_order", ())) != EXPECTED_CASES:
        errors.append("case order is incomplete or reordered")
    rows = {row.get("case_id"): row for row in matrix.get("cases", [])}
    if set(rows) != set(EXPECTED_CASES):
        errors.append("conformance case set is incomplete")
    for case_id, row in rows.items():
        if case_id == "exact_valid":
            if row.get("decision") != "CONFORMANCE_PASS" or row.get("validated_completion") is not True:
                errors.append("exact valid case was not accepted")
        elif row.get("validated_completion") is not False or row.get("decision") != "REJECTED":
            errors.append(f"negative case was accepted: {case_id}")
        if not row.get("reasons") and case_id != "exact_valid":
            errors.append(f"negative case has no rejection reason: {case_id}")
    summary = matrix.get("summary", {})
    if summary.get("accepted_count") != 1 or summary.get("rejected_count") != len(EXPECTED_CASES) - 1:
        errors.append("conformance summary counts are incorrect")
    for key in ("live_process_started", "formal_workspace_mutated", "runtime_scratch_leaked"):
        if summary.get(key) is not False:
            errors.append(f"offline matrix safety flag is not false: {key}")
    return errors


__all__ = ["EXPECTED_CASES", "EXPECTED_RESULT", "evaluate_case", "fixture_cases", "run_matrix", "validate_matrix"]
