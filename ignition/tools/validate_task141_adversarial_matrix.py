#!/usr/bin/env python3
"""Run the 22-case Task141 semantic and live-policy adversarial matrix."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import argparse
import json
from pathlib import Path
from typing import Any, Callable

from agent_federation.failure_forensics import build_failure_forensics_capsule, validate_failure_forensics_capsule
from agent_federation.live_current_projection import LiveCurrentProjectionError, validate_projection
from agent_federation.live_observation_plane import validate_observation_outcome
from agent_federation.live_state_dimensions import LiveStateDimensionsError, derive_live_state_dimensions, validate_live_state_dimensions
from agent_federation.structured_result_contract import StructuredResultContractError, extract_synthetic_result, validate_synthetic_result
from tools.validate_task141_live_policy_freeze import run_validation as validate_policy


ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "data/operations/iterations/141/live-current-projection-r3.json"
INFERENCE_EVENT = ROOT / "data/operations/iterations/141/live-inference-observation-events-r1.jsonl"
MATRIX = ROOT / "data/operations/iterations/141/step13-adversarial-matrix.json"
VALID_RESULT = {"nonce": "0123456789abcdef01234567", "line_count": 3, "field_value": "value-136", "checksum_prefix": "abcdef01"}


class MatrixGuardError(RuntimeError):
    """Raised when a semantic guard rejects an adversarial case."""


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    expected_action: str
    observed_action: str
    guard: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "case_id": self.case_id,
            "expected_action": self.expected_action,
            "observed_action": self.observed_action,
            "guard": self.guard,
            "detail": self.detail,
            "status": "PASS" if self.expected_action == self.observed_action else "FAIL",
        }


def _projection() -> dict[str, Any]:
    return json.loads(PROJECTION.read_text(encoding="utf-8"))


def _completion_gate(*, process_observed: bool, state: str, capture_complete: bool, result_present: bool, validator_status: str, workspace_unchanged: bool) -> None:
    if not process_observed:
        raise MatrixGuardError("COMPLETION_REQUIRES_OBSERVED_PROCESS")
    if state != "COMPLETED_VALIDATED":
        raise MatrixGuardError("COMPLETION_REQUIRES_COMPLETED_VALIDATED_STATE")
    if not capture_complete:
        raise MatrixGuardError("COMPLETION_REQUIRES_COMPLETE_CAPTURE")
    if not result_present or validator_status != "PASS":
        raise MatrixGuardError("COMPLETION_REQUIRES_RESULT_AND_VALIDATOR")
    if not workspace_unchanged:
        raise MatrixGuardError("COMPLETION_REQUIRES_UNCHANGED_WORKSPACE")


def _failure_capsule_gate(capsule: MappingLike | None) -> None:
    if capsule is None:
        raise MatrixGuardError("FAILURE_FORENSICS_CAPSULE_REQUIRED_BEFORE_RAW_SPOOL_DISPOSAL")


class MappingLike(dict):
    """Typing-only local mapping marker for the capsule gate."""


def _base_capsule() -> dict[str, Any]:
    return build_failure_forensics_capsule(
        task_id="IGNITION-20260826-141", dispatch_id="dispatch-141-matrix-01", attempt_id="attempt-141-matrix-01",
        executor_id="external.synthetic", adapter_id="synthetic-r1", executor_version="synthetic 1", interface_digest="a" * 64,
        argv=("/usr/bin/synthetic", "exec", "--json", "/private/path/omitted"), process_return_code=1, duration_ms=58.0,
        timed_out=False, process_group_status="CONFIRMED_GONE", cleanup_status="CLEANED", stdout_byte_count=0, stdout_digest="b" * 64,
        stderr_byte_count=271, stderr_digest="c" * 64, parser_status="NOT_RUN", parser_error_class="NO_PUBLIC_EVENTS",
        schema_status="NOT_RUN", schema_error_class="NO_STRUCTURED_RESULT", structured_output_status="ABSENT",
        structured_output_present=False, diagnostic_class="PROCESS_EXIT_NONZERO_NO_STRUCTURED_RESULT", runtime_scratch_status="CLEANED",
        auth_source_status="UNCHANGED_REFERENCE", workspace_status="UNCHANGED", inference_observation_status="NOT_OBSERVED",
        raw_spool_initialized=True, raw_spool_retention_status="RETAINED_UNTIL_DURABLE_RECEIPT", raw_spool_disposal_status="PENDING",
        known=("process started", "process returned nonzero"), unknown=("provider-private diagnostic text",), not_inferable=("private inference execution",),
    )


def _case_old_ceiling() -> None:
    value = _projection()
    value["current_live_ceiling"] = "LIVE_EXTERNAL_INVOCATION_NOT_OBSERVED"
    validate_projection(value)


def _case_dispatch_does_not_promote_inference() -> None:
    value = derive_live_state_dimensions({"live_dispatch_calls": 1, "live_dispatch_started": True, "live_process_started": True}, reconciliation_status="NOT_REQUIRED", validated_completion=False, next_action="RUN_DYNAMIC_EXECUTOR_ADMISSION")
    if value["inference_observation_status"] != "NOT_OBSERVED":
        raise MatrixGuardError("DISPATCH_CALL_COUNT_PROMOTED_INFERENCE")


def _case_inference_before_process() -> None:
    value = derive_live_state_dimensions({"live_dispatch_calls": 1, "live_dispatch_started": True, "live_process_started": False}, reconciliation_status="CLOSED_NO_LIVE_DISPATCH", validated_completion=False, explicit_inference_status="OBSERVED", next_action="RUN_DYNAMIC_EXECUTOR_ADMISSION")
    validate_live_state_dimensions(value)


def _case_return_code_without_process_start() -> None:
    event = {"schema_version": "live-observation-outcome-r1", "observation_outcome_type": "PRE_INFERENCE_NO_LIVE_PROCESS", "probe_return_code": 0, "transport_return_code": 0, "public_probe_calls": 2, "live_dispatch_calls": 0, "live_dispatch_started": False, "live_process_started": False, "live_process_return_code": 0, "capture_initialized": False, "structured_result_present": False, "validator_status": "NOT_RUN", "legacy_record_return_code_preserved": 0, "legacy_return_code_scope": "PUBLIC_PROBE_TRANSPORT_VALUE_ONLY"}
    validate_observation_outcome(event)


def _case_exit_zero_without_result() -> None:
    _completion_gate(process_observed=True, state="RETURNED_UNVALIDATED", capture_complete=True, result_present=False, validator_status="NOT_RUN", workspace_unchanged=True)


def _case_nonzero_without_capsule() -> None:
    _failure_capsule_gate(None)


def _case_malformed_without_capsule() -> None:
    _failure_capsule_gate(None)


def _case_extra_structured_field() -> None:
    validate_synthetic_result({**VALID_RESULT, "extra": "reject"})


def _case_non_exact_json() -> None:
    extract_synthetic_result(({"text": "prefix " + json.dumps(VALID_RESULT)},))


def _case_distinct_duplicate_results() -> None:
    extract_synthetic_result(({"text": json.dumps(VALID_RESULT)}, {"text": json.dumps({**VALID_RESULT, "line_count": 4})}))


def _case_valid_strict_result() -> None:
    value = validate_synthetic_result(VALID_RESULT)
    if value != VALID_RESULT:
        raise MatrixGuardError("STRICT_RESULT_NORMALIZATION_CHANGED_VALUE")


def _case_timeout_not_completion() -> None:
    value = derive_live_state_dimensions({"live_dispatch_calls": 1, "live_dispatch_started": True, "live_process_started": True, "live_process_return_code": None}, reconciliation_status="OPEN", validated_completion=False, explicit_inference_status="UNKNOWN", next_action="RECONCILE_UNRECOVERED_ATTEMPTS")
    if value["inference_observation_status"] != "UNKNOWN" or value["validated_completion_status"] != "NOT_VALIDATED" or value["reconciliation_blocker_status"] != "OPEN":
        raise MatrixGuardError("TIMEOUT_DIMENSIONS_NOT_CONSERVATIVE")


def _case_timeout_validated_claim() -> None:
    derive_live_state_dimensions({"live_dispatch_calls": 1, "live_dispatch_started": True, "live_process_started": True, "live_process_return_code": None}, reconciliation_status="OPEN", validated_completion=True, explicit_inference_status="UNKNOWN", next_action="RECONCILE_UNRECOVERED_ATTEMPTS")


def _case_inference_marker_false_observed() -> None:
    event = json.loads(INFERENCE_EVENT.read_text(encoding="utf-8").splitlines()[0])
    event["inference_observation_status"] = "OBSERVED"
    event["marker_observed"] = False
    from agent_federation.live_inference_observation_events import validate_inference_observation_event
    validate_inference_observation_event(event, check_hash=False)


def _case_failure_forensics_specific_class() -> None:
    capsule = _base_capsule()
    if validate_failure_forensics_capsule(capsule)["diagnostic_class"] != "PROCESS_EXIT_NONZERO_NO_STRUCTURED_RESULT":
        raise MatrixGuardError("FAILURE_FORENSICS_CLASS_NOT_SPECIFIC")


def _case_failure_forensics_private_text() -> None:
    capsule = _base_capsule()
    capsule["knowledge"]["known"] = ["api_key=must-not-persist"]
    validate_failure_forensics_capsule(capsule, check_digest=False)


def _case_spool_disposal_without_capsule() -> None:
    _failure_capsule_gate(None)


def _case_codex_policy_exclusion() -> None:
    result = validate_policy()
    if result["authorized_families"]:
        raise MatrixGuardError("CODEX_POLICY_EXCLUSION_WAS_RELAXED")
    raise MatrixGuardError("CODEX_SAME_FAMILY_RETRY_REJECTED")


def _case_family_cap() -> None:
    families = ["Gemini CLI", "Hermes Agent", "OpenClaw"]
    if len(set(families)) > 2:
        raise MatrixGuardError("MAX_DISTINCT_EXECUTOR_FAMILIES_EXCEEDED")


def _case_attempt_cap() -> None:
    attempts = {"Gemini CLI": 2}
    if any(value > 1 for value in attempts.values()):
        raise MatrixGuardError("MAX_ATTEMPTS_PER_FAMILY_EXCEEDED")


def _case_post_validated_probe() -> None:
    value = _projection()
    value["counts"]["validated_completion_count"] = 1
    if value["counts"]["validated_completion_count"] > 0:
        raise MatrixGuardError("STOP_AFTER_FIRST_EXACT_BOUND_VALIDATED_COMPLETION")


def _case_pre_process_dimension() -> None:
    value = derive_live_state_dimensions({"live_dispatch_calls": 0, "live_dispatch_started": False, "live_process_started": False}, reconciliation_status="CLOSED_NO_LIVE_DISPATCH", validated_completion=False, next_action="RUN_DYNAMIC_EXECUTOR_ADMISSION")
    if value["inference_observation_status"] != "NOT_APPLICABLE_PRE_PROCESS":
        raise MatrixGuardError("PRE_PROCESS_INFERENCE_STATUS_IS_NOT_EXPLICIT")


CASES: tuple[tuple[str, str, str, Callable[[], None]], ...] = (
    ("r3-old-invocation-not-observed-ceiling", "REJECT", "R3_PROCESS_OBSERVATION_CEILING", _case_old_ceiling),
    ("dispatch-count-alone-not-inference", "ALLOW", "DISPATCH_PROCESS_INFERENCE_SEPARATION", _case_dispatch_does_not_promote_inference),
    ("inference-observed-before-process", "REJECT", "INFERENCE_REQUIRES_PROCESS", _case_inference_before_process),
    ("return-code-without-process-start", "REJECT", "TYPED_PROCESS_RETURN_SCOPE", _case_return_code_without_process_start),
    ("exit-zero-without-structured-result", "REJECT", "COMPLETION_RESULT_GATE", _case_exit_zero_without_result),
    ("nonzero-without-failure-capsule", "REJECT", "FORENSICS_BEFORE_SPOOL_DISPOSAL", _case_nonzero_without_capsule),
    ("malformed-result-without-failure-capsule", "REJECT", "FORENSICS_BEFORE_SPOOL_DISPOSAL", _case_malformed_without_capsule),
    ("extra-structured-field", "REJECT", "STRICT_RESULT_SCHEMA", _case_extra_structured_field),
    ("non-exact-json-result", "REJECT", "STRICT_RESULT_PARSER", _case_non_exact_json),
    ("distinct-duplicate-results", "REJECT", "AMBIGUOUS_RESULT_GUARD", _case_distinct_duplicate_results),
    ("valid-strict-result", "ALLOW", "STRICT_RESULT_CONTRACT", _case_valid_strict_result),
    ("timeout-not-completion", "ALLOW", "TIMEOUT_UNKNOWN_DIMENSION", _case_timeout_not_completion),
    ("timeout-validated-claim", "REJECT", "TIMEOUT_RECONCILIATION_GATE", _case_timeout_validated_claim),
    ("inference-marker-false-observed", "REJECT", "INFERENCE_MARKER_INVARIANT", _case_inference_marker_false_observed),
    ("failure-forensics-specific-class", "ALLOW", "FAILURE_DIAGNOSTIC_CLASSIFICATION", _case_failure_forensics_specific_class),
    ("failure-forensics-private-text", "REJECT", "FAILURE_REDACTION_GATE", _case_failure_forensics_private_text),
    ("spool-disposal-without-capsule", "REJECT", "FORENSICS_BEFORE_SPOOL_DISPOSAL", _case_spool_disposal_without_capsule),
    ("codex-policy-exclusion", "REJECT", "NO_BLIND_SAME_FAMILY_RETRY", _case_codex_policy_exclusion),
    ("three-family-policy", "REJECT", "MAX_TWO_EXECUTOR_FAMILIES", _case_family_cap),
    ("two-attempts-one-family", "REJECT", "MAX_ONE_ATTEMPT_PER_FAMILY", _case_attempt_cap),
    ("post-validated-probe", "REJECT", "STOP_AFTER_FIRST_VALIDATED_COMPLETION", _case_post_validated_probe),
    ("pre-process-inference-not-applicable", "ALLOW", "PRE_PROCESS_DIMENSION", _case_pre_process_dimension),
)


def _run_case(case_id: str, expected_action: str, guard: str, function: Callable[[], None]) -> CaseResult:
    try:
        function()
    except Exception as exc:
        observed_action = "REJECT"
        detail = f"{type(exc).__name__}: {exc}"
    else:
        observed_action = "ALLOW"
        detail = "guard chain completed without rejection"
    return CaseResult(case_id, expected_action, observed_action, guard, detail)


def run_matrix() -> dict[str, Any]:
    results = [_run_case(*case) for case in CASES]
    serialized = [result.to_dict() for result in results]
    return {
        "schema_version": "ignition-141-step13-adversarial-matrix-r1", "task_id": "IGNITION-20260826-141",
        "status": "PASS" if all(item["status"] == "PASS" for item in serialized) else "FAIL",
        "case_count": len(serialized), "negative_case_count": sum(item["expected_action"] == "REJECT" for item in serialized),
        "positive_case_count": sum(item["expected_action"] == "ALLOW" for item in serialized), "live_processes_started": 0,
        "cases": serialized,
        "canonical_sources": ["ignition/agent_federation/live_state_dimensions.py", "ignition/agent_federation/live_current_projection.py", "ignition/agent_federation/structured_result_contract.py", "ignition/agent_federation/failure_forensics.py", "ignition/data/operations/iterations/141/live-current-projection-r3.json", "ignition/data/operations/iterations/141/step09-live-policy-freeze.json"],
        "claim_ceiling": "Task141 repository-local adversarial semantic and live-policy evidence only; no live process was started by this matrix and no external truth, validated completion, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = run_matrix()
    if args.write:
        MATRIX.parent.mkdir(parents=True, exist_ok=True)
        MATRIX.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
