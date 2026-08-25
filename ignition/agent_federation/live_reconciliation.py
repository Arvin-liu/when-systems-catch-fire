"""Typed reconciliation states for bounded live-attempt evidence.

Reconciliation closes an observation obligation without upgrading an unknown
effect into success, failure, or no-effect.  It is an append-only overlay
contract; historical attempt records remain immutable.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json


RECONCILIATION_SCHEMA = "live-reconciliation-state-r1"
RECONCILIATION_STATUSES = frozenset({
    "OPEN_REQUIRES_EVIDENCE",
    "TERMINAL_UNRECOVERABLE_EFFECT_UNKNOWN",
    "TERMINAL_UNRECOVERABLE_OBSERVATION_INCOMPLETE",
    "CLOSED_NO_LIVE_DISPATCH",
    "CLOSED_RECONCILED",
})
RECOVERY_STATUSES = frozenset({"RECOVERABLE", "EXHAUSTED", "CONCLUSIVE"})
PROCESS_OBSERVATIONS = frozenset({
    "UNKNOWN",
    "NO_LIVE_PROCESS_OBSERVED",
    "LIVE_PROCESS_OBSERVED_OUTCOME_UNKNOWN",
    "LIVE_PROCESS_OUTCOME_KNOWN",
})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TASK_RE = re.compile(r"^IGNITION-[0-9]{8}-[0-9]+$")


class LiveReconciliationError(ValueError):
    """Raised when a reconciliation state contradicts its evidence boundary."""


def _schema_validate(document: Mapping[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover - clean bootstrap fallback
        return
    schema_path = Path(__file__).resolve().parents[1] / "schemas/operations/live-reconciliation-state-r1.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - packaging failure
        raise LiveReconciliationError("reconciliation state schema is unavailable") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.path) or "$"
        raise LiveReconciliationError(f"reconciliation schema violation at {path}: {error.message}")


def _unsigned(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: document[key] for key in sorted(document) if key != "state_digest"}


def _check_sha(value: Any, field: str) -> None:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise LiveReconciliationError(f"{field} must be a lowercase SHA-256 digest")


def validate_reconciliation_state(document: Mapping[str, Any], *, check_digest: bool = True) -> dict[str, Any]:
    """Validate a reconciliation state and preserve explicit unknown effect."""

    if not isinstance(document, Mapping):
        raise LiveReconciliationError("reconciliation state must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    _schema_validate(value)
    required = {
        "schema_version", "task_id", "attempt_id", "prior_record_hash", "prior_process_state",
        "reconciliation_status", "evidence_recovery_status", "evidence_exhausted", "process_observation",
        "external_effect_knowledge", "validated_completion_eligible", "terminal_reason", "evidence_refs",
        "claim_ceiling", "state_digest",
    }
    if set(value) != required:
        raise LiveReconciliationError("reconciliation state fields are not canonical")
    if value["schema_version"] != RECONCILIATION_SCHEMA:
        raise LiveReconciliationError("reconciliation state schema version mismatch")
    if not isinstance(value["task_id"], str) or not TASK_RE.fullmatch(value["task_id"]):
        raise LiveReconciliationError("reconciliation task binding is invalid")
    for field in ("attempt_id", "prior_process_state", "terminal_reason", "claim_ceiling"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise LiveReconciliationError(f"{field} must be a non-empty public string")
    _check_sha(value["prior_record_hash"], "prior_record_hash")
    if value["reconciliation_status"] not in RECONCILIATION_STATUSES:
        raise LiveReconciliationError("unknown reconciliation status")
    if value["evidence_recovery_status"] not in RECOVERY_STATUSES:
        raise LiveReconciliationError("unknown evidence recovery status")
    if not isinstance(value["evidence_exhausted"], bool):
        raise LiveReconciliationError("evidence_exhausted must be boolean")
    if value["evidence_exhausted"] != (value["evidence_recovery_status"] == "EXHAUSTED"):
        raise LiveReconciliationError("evidence exhaustion flag disagrees with recovery status")
    if value["process_observation"] not in PROCESS_OBSERVATIONS:
        raise LiveReconciliationError("unknown process observation")
    if value["external_effect_knowledge"] != "UNKNOWN":
        raise LiveReconciliationError("this reconciliation contract cannot upgrade external effect knowledge")
    if not isinstance(value["validated_completion_eligible"], bool):
        raise LiveReconciliationError("validated_completion_eligible must be boolean")
    if not isinstance(value["evidence_refs"], list) or not value["evidence_refs"] or any(not isinstance(ref, str) or not ref.strip() for ref in value["evidence_refs"]):
        raise LiveReconciliationError("evidence_refs must be a non-empty public reference list")
    status = value["reconciliation_status"]
    if status == "OPEN_REQUIRES_EVIDENCE":
        if value["evidence_recovery_status"] != "RECOVERABLE" or value["evidence_exhausted"]:
            raise LiveReconciliationError("open reconciliation requires recoverable evidence")
    elif status == "CLOSED_NO_LIVE_DISPATCH":
        if value["process_observation"] != "NO_LIVE_PROCESS_OBSERVED" or value["validated_completion_eligible"]:
            raise LiveReconciliationError("no-live-dispatch closure requires an explicit absent process and no completion eligibility")
    elif status == "TERMINAL_UNRECOVERABLE_EFFECT_UNKNOWN":
        if not value["evidence_exhausted"] or value["process_observation"] == "LIVE_PROCESS_OUTCOME_KNOWN" or value["validated_completion_eligible"]:
            raise LiveReconciliationError("unrecoverable effect-unknown state has an unsafe upgrade")
    elif status == "TERMINAL_UNRECOVERABLE_OBSERVATION_INCOMPLETE":
        if not value["evidence_exhausted"] or value["process_observation"] == "LIVE_PROCESS_OUTCOME_KNOWN" or value["validated_completion_eligible"]:
            raise LiveReconciliationError("unrecoverable observation-incomplete state has an unsafe upgrade")
    elif status == "CLOSED_RECONCILED" and value["validated_completion_eligible"]:
        raise LiveReconciliationError("reconciliation state cannot independently authorize a validated completion")
    if value["state_digest"] != sha256_json(_unsigned(value)) if check_digest else False:
        raise LiveReconciliationError("reconciliation state digest does not match content")
    if check_digest:
        _check_sha(value["state_digest"], "state_digest")
    return value


def derive_reconciliation_state(audit: Mapping[str, Any]) -> dict[str, Any]:
    """Derive a conservative terminal/open state from an explicit audit."""

    required = {
        "task_id", "attempt_id", "prior_record_hash", "prior_process_state", "process_observation",
        "evidence_recovery_status", "evidence_refs", "terminal_reason",
    }
    if set(audit) != required:
        raise LiveReconciliationError("reconciliation audit fields are not canonical")
    recovery = audit["evidence_recovery_status"]
    observation = audit["process_observation"]
    prior_state = audit["prior_process_state"]
    if recovery not in RECOVERY_STATUSES:
        raise LiveReconciliationError("unknown evidence recovery status")
    if observation not in PROCESS_OBSERVATIONS:
        raise LiveReconciliationError("unknown process observation")
    if recovery == "RECOVERABLE":
        status = "OPEN_REQUIRES_EVIDENCE"
    elif observation == "NO_LIVE_PROCESS_OBSERVED":
        status = "CLOSED_NO_LIVE_DISPATCH"
    elif prior_state == "TIMED_OUT_EFFECT_UNKNOWN":
        status = "TERMINAL_UNRECOVERABLE_EFFECT_UNKNOWN"
    elif prior_state == "OBSERVATION_INCOMPLETE":
        status = "TERMINAL_UNRECOVERABLE_OBSERVATION_INCOMPLETE"
    else:
        status = "CLOSED_RECONCILED"
    value = {
        "schema_version": RECONCILIATION_SCHEMA,
        "task_id": audit["task_id"],
        "attempt_id": audit["attempt_id"],
        "prior_record_hash": audit["prior_record_hash"],
        "prior_process_state": prior_state,
        "reconciliation_status": status,
        "evidence_recovery_status": recovery,
        "evidence_exhausted": recovery == "EXHAUSTED",
        "process_observation": observation,
        "external_effect_knowledge": "UNKNOWN",
        "validated_completion_eligible": False,
        "terminal_reason": audit["terminal_reason"],
        "evidence_refs": list(audit["evidence_refs"]),
        "claim_ceiling": "Reconciliation closes only the repository evidence obligation; external effect remains UNKNOWN and no success, failure, no-effect, production readiness, Owner acceptance or epistemic upgrade is inferred.",
    }
    value["state_digest"] = sha256_json(_unsigned(value))
    return validate_reconciliation_state(value)


__all__ = [
    "RECONCILIATION_SCHEMA",
    "RECONCILIATION_STATUSES",
    "RECOVERY_STATUSES",
    "PROCESS_OBSERVATIONS",
    "LiveReconciliationError",
    "derive_reconciliation_state",
    "validate_reconciliation_state",
]
