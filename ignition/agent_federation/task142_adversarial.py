"""Offline adversarial guards for Task142 lifecycle and executor admission.

The matrix in this module mutates in-memory copies of canonical records only.
It never probes or invokes an executor.  Each negative case is deliberately
bound to one invariant so a green matrix means rejection was observed, not
that an unsafe candidate was accepted.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .executor_admission_contract import AGENTIC_FAMILY, classify_family
from .live_state_dimensions import derive_live_state_dimensions
from .structured_result_contract import validate_synthetic_result
from .task142_first_completion_validator import (
    FirstCompletionValidationError,
    VALIDATOR_VERSION,
    expected_result_digest,
    validate_exact_completion,
)


ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = ROOT / "data/architecture/current-system-identity.json"
LAYOUT_PATH = ROOT / "data/architecture/interactive-system-map-layout.json"


class Task142AdversarialError(ValueError):
    """Raised when an unsafe mutation is not rejected by a Task142 guard."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _require(value: Any, field: str) -> Any:
    if value is None:
        raise Task142AdversarialError("MISSING_ADMISSION_FIELD", f"{field} is required")
    return value


def validate_terminality_independence(task: Mapping[str, Any], obligation: Mapping[str, Any]) -> None:
    """Reject a completed formal scope that was made live by an open obligation."""

    scope_complete = task.get("scope_complete") is True
    terminal = task.get("terminal") is True
    status = task.get("execution_status")
    obligation_open = obligation.get("current_status") == "OPEN"
    if scope_complete and status == "IN_PROGRESS":
        raise Task142AdversarialError(
            "FORMAL_TASK_REVERTED_BY_OPEN_OBLIGATION",
            "a completed formal scope cannot remain IN_PROGRESS because an obligation is open",
        )
    if scope_complete and not terminal:
        raise Task142AdversarialError(
            "COMPLETED_SCOPE_NOT_TERMINAL",
            "a completed formal scope must be terminal independently of obligation status",
        )
    if status in {"COMPLETED_WITH_CLASSIFIED_RESIDUALS", "COMPLETED_WITH_OPEN_OBLIGATIONS"} and not terminal:
        raise Task142AdversarialError("COMPLETED_STATUS_NOT_TERMINAL", "completed status cannot be non-terminal")
    if terminal and obligation_open and status == "IN_PROGRESS":
        raise Task142AdversarialError("OPEN_OBLIGATION_LIVENESS_COUPLING", "open obligation must not determine task liveness")


def validate_obligation_close_gate(obligation: Mapping[str, Any], validated_completion_count: int) -> None:
    """Reject an obligation terminal state without the exact completion it names."""

    current_status = obligation.get("current_status")
    if current_status == "CLOSED" and validated_completion_count < 1:
        raise Task142AdversarialError(
            "OBLIGATION_CLOSED_WITHOUT_VALIDATED_COMPLETION",
            "the first-validated-completion obligation cannot close at count zero",
        )
    if current_status == "OPEN" and validated_completion_count > 0:
        raise Task142AdversarialError(
            "OBLIGATION_ADJUDICATION_STALE",
            "an open obligation must be adjudicated after a validated completion",
        )


_PROVIDER_NEUTRAL_FAMILY = {
    "AGENTIC_EXECUTOR": "agentic-executor",
    "REASONER_RUNTIME": "reasoner-runtime",
    "TOOL": "tool",
    "UI_SURFACE": "ui-surface",
}


def validate_provider_neutral_candidate(candidate: Mapping[str, Any]) -> None:
    """Apply admission boundary checks without granting a provider brand authority."""

    family = classify_family(_require(candidate.get("family"), "family"))
    if candidate.get("class_separation") != family:
        raise Task142AdversarialError("CLASS_SEPARATION_BYPASS", "candidate class and declared family differ")
    if candidate.get("provider_neutral_family") != _PROVIDER_NEUTRAL_FAMILY[family]:
        raise Task142AdversarialError(
            "PROVIDER_BRAND_BYPASS",
            "a provider brand or arbitrary family label cannot replace the canonical family taxonomy",
        )
    if family != AGENTIC_FAMILY:
        raise Task142AdversarialError("NON_AGENT_CLASS_NOT_LIVE_ELIGIBLE", "only AGENTIC_EXECUTOR may enter live admission")
    if candidate.get("installed") is not True:
        raise Task142AdversarialError("EXECUTOR_NOT_INSTALLED", "live admission requires an observed installed executable")
    if candidate.get("public_auth") != "PASS" or candidate.get("auth_attestation") != "PUBLIC_STATUS_PASS":
        raise Task142AdversarialError("PUBLIC_AUTH_NOT_ATTESTED", "presence-only or fake auth success is not public status proof")
    if candidate.get("auth_content_read") is not False:
        raise Task142AdversarialError("AUTH_CONTENT_READ", "auth content must remain unread")
    if candidate.get("billing_change_required") is not False or candidate.get("no_new_billing") is not True:
        raise Task142AdversarialError("NEW_BILLING_REQUIRED", "admission cannot ignore a billing or API authorization change")
    if candidate.get("workspace_mode") != "DISPOSABLE_READ_ONLY_FIXTURE" or candidate.get("workspace_read_only") is not True:
        raise Task142AdversarialError("WORKSPACE_NOT_READ_ONLY", "the task workspace must be a disposable read-only fixture")
    if candidate.get("runtime_scratch_mode") != "ATTEMPT_EPHEMERAL_WRITABLE" or candidate.get("runtime_scratch_separate") is not True:
        raise Task142AdversarialError("RUNTIME_SCRATCH_BOUNDARY_INVALID", "runtime scratch must be separate from the task workspace")
    if candidate.get("structured_result") != "STRICT":
        raise Task142AdversarialError("STRUCTURED_RESULT_NOT_STRICT", "admission requires a strict structured result contract")
    if candidate.get("capture") != "PROVEN" or candidate.get("cleanup") != "PROVEN":
        raise Task142AdversarialError("OBSERVATION_BOUNDARY_NOT_PROVEN", "durable capture and cleanup must be proven before admission")
    if candidate.get("no_effect_scope") != "PROVEN":
        raise Task142AdversarialError("SIDE_EFFECT_SCOPE_NOT_PROVEN", "channel/browser/remote-write effects must be denied and observed")


def validate_attempt_policy(
    attempts: Sequence[Mapping[str, Any]],
    *,
    validated_completion_count: int = 0,
    proposing_new_attempt: bool = False,
) -> None:
    """Enforce total/family caps, no blind retry, and success-stop."""

    if len(attempts) > 2:
        raise Task142AdversarialError("MAX_TOTAL_ATTEMPTS_EXCEEDED", "Task142 permits at most two attempts")
    families: dict[str, list[Mapping[str, Any]]] = {}
    for attempt in attempts:
        family = str(_require(attempt.get("family"), "attempt.family"))
        families.setdefault(family, []).append(attempt)
    for family, rows in families.items():
        if len(rows) <= 1:
            continue
        if not all(row.get("root_cause_confirmed") is True and bool(row.get("root_cause_fix_ref")) for row in rows[1:]):
            raise Task142AdversarialError("SAME_FAMILY_BLIND_RETRY", f"family {family} has no confirmed root-cause repair")
    if validated_completion_count > 0 and proposing_new_attempt:
        raise Task142AdversarialError("SUCCESS_STOP_VIOLATION", "no attempt may start after the first validated completion")


def validate_inference_observation_boundary(observation: Mapping[str, Any]) -> None:
    """Reject legacy inference promotion when no independent marker exists."""

    dimensions = derive_live_state_dimensions(
        observation,
        reconciliation_status="NOT_REQUIRED",
        validated_completion=False,
        next_action="NO_ACTION",
    )
    if observation.get("live_inference_started") is True and observation.get("inference_marker_observed") is not True:
        raise Task142AdversarialError(
            "PROCESS_DOES_NOT_PROVE_INFERENCE",
            "process observation must not promote inference without an independent accepted marker",
        )
    if dimensions["inference_observation_status"] == "OBSERVED" and observation.get("inference_marker_observed") is not True:
        raise Task142AdversarialError("INFERENCE_MARKER_MISSING", "OBSERVED inference requires its explicit marker")


def current_projection_expectations() -> dict[str, Any]:
    """Return stable current/architecture identity values used by the stale case."""

    identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    return {
        "current_task_id": identity["current_formal_task_id"],
        "identity_epoch": identity["identity_epoch"],
        "map_version": layout["current_map_version"],
    }


def validate_current_projection_fresh(current: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    """Reject a Current projection that lags its canonical identity or map."""

    for field in ("current_task_id", "identity_epoch", "map_version"):
        if current.get(field) != expected.get(field):
            raise Task142AdversarialError("STALE_CURRENT_ARCHITECTURE_PROJECTION", f"{field} differs from canonical identity")


def _completion_record() -> dict[str, Any]:
    result = {
        "nonce": "0123456789abcdef01234567",
        "line_count": 3,
        "field_value": "task142-fixture",
        "checksum_prefix": "abcdef01",
    }
    digest = "a" * 64
    return {
        "task_id": "IGNITION-20260827-142",
        "dispatch_id": "dispatch-142-adversarial",
        "attempt_id": "attempt-142-adversarial",
        "executor_id": "external.synthetic",
        "family": AGENTIC_FAMILY,
        "executor_version": "fixture-agent-r1",
        "capability_lease_id": "lease-142-adversarial",
        "capability_lease_status": "ACTIVE",
        "fixture_nonce": result["nonce"],
        "workspace_digest_before": digest,
        "workspace_digest_after": digest,
        "capture_ref": "capture://attempt-142-adversarial",
        "structured_result_ref": "capture://attempt-142-adversarial/result",
        "validator_ref": "validator://task142-exact-validator-r1",
        "executor_state": "RETURNED_UNVALIDATED",
        "expected_result": result,
        "returned_structured_result": deepcopy(result),
        "returned_result_digest": expected_result_digest(result),
        "validator_version": VALIDATOR_VERSION,
        "validator_result": "PASS",
        "capture_completeness": "COMPLETE",
        "process_return_code": 0,
        "cleanup_status": "CONFIRMED_GONE",
        "workspace_mode": "DISPOSABLE_READ_ONLY_FIXTURE",
        "side_effect_observation": "READ_ONLY_UNCHANGED",
    }
    return record


def _admission_fixture() -> dict[str, Any]:
    return {
        "executor_id": "external.synthetic",
        "family": AGENTIC_FAMILY,
        "provider_neutral_family": "agentic-executor",
        "class_separation": AGENTIC_FAMILY,
        "installed": True,
        "public_auth": "PASS",
        "auth_attestation": "PUBLIC_STATUS_PASS",
        "auth_content_read": False,
        "billing_change_required": False,
        "no_new_billing": True,
        "workspace_mode": "DISPOSABLE_READ_ONLY_FIXTURE",
        "workspace_read_only": True,
        "runtime_scratch_mode": "ATTEMPT_EPHEMERAL_WRITABLE",
        "runtime_scratch_separate": True,
        "structured_result": "STRICT",
        "capture": "PROVEN",
        "cleanup": "PROVEN",
        "no_effect_scope": "PROVEN",
    }


def _case_completed_scope_reverted() -> None:
    task = {"task_id": "IGNITION-20260826-141", "execution_status": "IN_PROGRESS", "terminal": False, "scope_complete": True}
    obligation = {"obligation_id": "LIVE_EXTERNAL_INVOCATION", "current_status": "OPEN"}
    validate_terminality_independence(task, obligation)


def _case_open_obligation_closed() -> None:
    validate_obligation_close_gate({"obligation_id": "LIVE_EXTERNAL_INVOCATION", "current_status": "CLOSED"}, 0)


def _case_reasoner_masquerades_as_agent() -> None:
    candidate = _admission_fixture()
    candidate.update({"family": "REASONER_RUNTIME", "class_separation": "REASONER_RUNTIME", "provider_neutral_family": "reasoner-runtime"})
    validate_provider_neutral_candidate(candidate)


def _case_provider_brand_bypass() -> None:
    candidate = _admission_fixture()
    candidate["provider_neutral_family"] = "Codex"
    validate_provider_neutral_candidate(candidate)


def _case_fake_auth_success() -> None:
    candidate = _admission_fixture()
    candidate["auth_attestation"] = "PRESENCE_ONLY"
    validate_provider_neutral_candidate(candidate)


def _case_billing_change_ignored() -> None:
    candidate = _admission_fixture()
    candidate["billing_change_required"] = True
    validate_provider_neutral_candidate(candidate)


def _case_writable_workspace() -> None:
    candidate = _admission_fixture()
    candidate["workspace_mode"] = "WORKSPACE_WRITE"
    validate_provider_neutral_candidate(candidate)


def _case_scratch_workspace_mixed() -> None:
    candidate = _admission_fixture()
    candidate["runtime_scratch_separate"] = False
    validate_provider_neutral_candidate(candidate)


def _case_malformed_result_validated() -> None:
    result = _completion_record()["returned_structured_result"]
    result["extra"] = "malformed"
    validate_synthetic_result(result)


def _case_executor_self_pass() -> None:
    record = _completion_record()
    record["executor_state"] = "COMPLETED_VALIDATED"
    validate_exact_completion(record)


def _case_same_family_blind_retry() -> None:
    validate_attempt_policy(
        [
            {"family": "Codex", "root_cause_confirmed": False},
            {"family": "Codex", "root_cause_confirmed": False},
        ]
    )


def _case_second_after_first_success() -> None:
    validate_attempt_policy(
        [{"family": "Gemini"}],
        validated_completion_count=1,
        proposing_new_attempt=True,
    )


def _case_capture_incomplete_validated() -> None:
    record = _completion_record()
    record["capture_completeness"] = "INCOMPLETE"
    validate_exact_completion(record)


def _case_process_promotes_inference() -> None:
    validate_inference_observation_boundary(
        {
            "live_dispatch_calls": 1,
            "live_dispatch_started": True,
            "live_process_started": True,
            "live_inference_started": True,
            "inference_marker_observed": False,
        }
    )


def _case_stale_current_architecture() -> None:
    expected = current_projection_expectations()
    current = dict(expected)
    current["map_version"] = "0.15.0"
    validate_current_projection_fresh(current, expected)


CASES: tuple[tuple[str, str, str, Callable[[], None]], ...] = (
    ("completed-scope-reverted-by-open-obligation", "FORMAL_TASK_TERMINALITY_INDEPENDENT_OF_OPEN_OBLIGATION", "FORMAL_TASK_REVERTED_BY_OPEN_OBLIGATION", _case_completed_scope_reverted),
    ("open-obligation-written-terminal", "OBLIGATION_CARRY_FORWARD_WITHOUT_TASK_LIVENESS", "OBLIGATION_CLOSED_WITHOUT_VALIDATED_COMPLETION", _case_open_obligation_closed),
    ("reasoner-masquerades-as-agent", "TOOL_REASONER_AGENT_CLASS_SEPARATION", "NON_AGENT_CLASS_NOT_LIVE_ELIGIBLE", _case_reasoner_masquerades_as_agent),
    ("provider-brand-bypasses-admission", "EXECUTOR_ADMISSION_PROVIDER_NEUTRAL", "PROVIDER_BRAND_BYPASS", _case_provider_brand_bypass),
    ("fake-auth-success", "PUBLIC_AUTH_STATUS_ATTESTATION", "PUBLIC_AUTH_NOT_ATTESTED", _case_fake_auth_success),
    ("billing-change-requirement-ignored", "NO_NEW_BILLING_AUTHORITY", "NEW_BILLING_REQUIRED", _case_billing_change_ignored),
    ("writable-task-workspace", "DISPOSABLE_READ_ONLY_WORKSPACE", "WORKSPACE_NOT_READ_ONLY", _case_writable_workspace),
    ("runtime-scratch-mixed-with-workspace", "RUNTIME_SCRATCH_SEPARATION", "RUNTIME_SCRATCH_BOUNDARY_INVALID", _case_scratch_workspace_mixed),
    ("malformed-result-promoted-to-validated", "FIRST_VALIDATED_COMPLETION_EXACT_BINDING", "EXTRA_FIELDS", _case_malformed_result_validated),
    ("executor-self-pass-direct-completion", "EXECUTOR_SELF_PASS_NOT_AUTHORITY", "EXECUTOR_SELF_PASS_NOT_AUTHORITY", _case_executor_self_pass),
    ("same-family-blind-retry", "NO_BLIND_SAME_FAMILY_RETRY", "SAME_FAMILY_BLIND_RETRY", _case_same_family_blind_retry),
    ("second-attempt-after-first-success", "STOP_AFTER_FIRST_VALIDATED_COMPLETION", "SUCCESS_STOP_VIOLATION", _case_second_after_first_success),
    ("capture-incomplete-promoted-to-validated", "COMPLETE_DURABLE_CAPTURE_REQUIRED", "CAPTURE_INCOMPLETE", _case_capture_incomplete_validated),
    ("process-observed-promotes-inference", "PROCESS_INFERENCE_SEPARATION", "PROCESS_DOES_NOT_PROVE_INFERENCE", _case_process_promotes_inference),
    ("stale-current-architecture-projection", "CURRENT_STATE_SYNC_AND_SOLE_MAP", "STALE_CURRENT_ARCHITECTURE_PROJECTION", _case_stale_current_architecture),
)


def _run_case(case_id: str, guard: str, expected_code: str, function: Callable[[], None]) -> dict[str, Any]:
    try:
        function()
    except Exception as exc:
        observed_action = "REJECT"
        observed_code = getattr(exc, "code", None)
        if observed_code is None:
            text = str(exc)
            observed_code = text.split(":", 1)[0] if text else type(exc).__name__
        detail = f"{type(exc).__name__}: {exc}"
    else:
        observed_action = "ALLOW"
        observed_code = None
        detail = "unsafe mutation passed the guard chain"
    return {
        "case_id": case_id,
        "expected_action": "REJECT",
        "observed_action": observed_action,
        "expected_code": expected_code,
        "observed_code": observed_code,
        "guard": guard,
        "detail": detail,
        "status": "PASS" if observed_action == "REJECT" and observed_code == expected_code else "FAIL",
    }


def run_matrix() -> dict[str, Any]:
    cases = [_run_case(case_id, guard, expected_code, function) for case_id, guard, expected_code, function in CASES]
    return {
        "schema_version": "task142-adversarial-matrix-r1",
        "task_id": "IGNITION-20260827-142",
        "step": "18",
        "status": "PASS" if all(row["status"] == "PASS" for row in cases) else "FAIL",
        "case_count": len(cases),
        "negative_case_count": len(cases),
        "live_process_started": False,
        "cases": cases,
        "safety": {
            "secret_content_read": False,
            "configuration_changed": False,
            "billing_changed": False,
            "install_or_upgrade_performed": False,
            "live_process_started": False,
            "live_inference_started": False,
            "workspace_modified": False,
        },
        "canonical_sources": [
            "ignition/agent_federation/task142_first_completion_validator.py",
            "ignition/agent_federation/executor_admission_contract.py",
            "ignition/agent_federation/live_state_dimensions.py",
            "ignition/agent_federation/structured_result_contract.py",
            "ignition/data/operations/formal-task-lifecycle-r1.json",
            "ignition/data/operations/open-obligation-registry-r1.json",
            "ignition/data/architecture/current-system-identity.json",
            "ignition/data/architecture/interactive-system-map-layout.json",
        ],
        "claim_ceiling": "Offline repository-local adversarial rejection evidence only; no executor was probed or invoked, no validated completion is claimed, and no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


__all__ = [
    "CASES",
    "Task142AdversarialError",
    "current_projection_expectations",
    "run_matrix",
    "validate_attempt_policy",
    "validate_current_projection_fresh",
    "validate_inference_observation_boundary",
    "validate_obligation_close_gate",
    "validate_provider_neutral_candidate",
    "validate_terminality_independence",
]
