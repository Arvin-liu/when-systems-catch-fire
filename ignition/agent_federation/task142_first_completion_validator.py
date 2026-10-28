"""Independent exact-binding validator for the first Task142 completion.

The validator consumes a public, already-captured candidate record. It never
trusts an executor's PASS as completion and never invokes a provider.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any


VALIDATOR_VERSION = "task142-exact-validator-r1"
PASS = "LIVE_READONLY_VALIDATED_COMPLETION"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_BINDINGS = (
    "task_id", "dispatch_id", "attempt_id", "executor_id", "family", "executor_version",
    "capability_lease_id", "fixture_nonce", "workspace_digest_before", "workspace_digest_after",
    "capture_ref", "structured_result_ref", "validator_ref",
)


class FirstCompletionValidationError(ValueError):
    """Raised when a candidate cannot be promoted to validated completion."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _digest(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise FirstCompletionValidationError("DIGEST_NOT_EXACT", f"{field} must be a lowercase SHA-256 digest")


def _nonblank(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FirstCompletionValidationError("MISSING_BINDING", f"{field} must be non-empty")


def expected_result_digest(result: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(dict(result), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_exact_completion(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a validator-owned decision; raise on the first unsafe mismatch."""

    if not isinstance(record, Mapping):
        raise FirstCompletionValidationError("RECORD_NOT_OBJECT", "completion candidate must be an object")
    for field in REQUIRED_BINDINGS:
        _nonblank(record.get(field), field)
    if record["family"] != "AGENTIC_EXECUTOR":
        raise FirstCompletionValidationError("WRONG_EXECUTOR_CLASS", "validated completion must come from AGENTIC_EXECUTOR")
    if record["capability_lease_status"] != "ACTIVE":
        raise FirstCompletionValidationError("LEASE_NOT_ACTIVE", "capability lease is not active")
    if record["executor_state"] != "RETURNED_UNVALIDATED":
        raise FirstCompletionValidationError("EXECUTOR_SELF_PASS_NOT_AUTHORITY", "executor state must remain RETURNED_UNVALIDATED until this validator passes")
    _digest(record["workspace_digest_before"], "workspace_digest_before")
    _digest(record["workspace_digest_after"], "workspace_digest_after")
    if record["workspace_digest_before"] != record["workspace_digest_after"]:
        raise FirstCompletionValidationError("WORKSPACE_MUTATED", "read-only workspace digest changed")
    expected = record.get("expected_result")
    returned = record.get("returned_structured_result")
    if not isinstance(expected, Mapping) or not isinstance(returned, Mapping):
        raise FirstCompletionValidationError("STRUCTURED_RESULT_MISSING", "expected and returned structured results are required")
    if expected != returned:
        raise FirstCompletionValidationError("STRUCTURED_RESULT_SEMANTIC_MISMATCH", "returned structured result differs from independently computed expected result")
    if record.get("fixture_nonce") != expected.get("nonce") or returned.get("nonce") != record.get("fixture_nonce"):
        raise FirstCompletionValidationError("FIXTURE_NONCE_MISMATCH", "fixture nonce is not bound through expected and returned result")
    if record.get("returned_result_digest") != expected_result_digest(returned):
        raise FirstCompletionValidationError("RESULT_DIGEST_MISMATCH", "returned result digest is not exact")
    if record["validator_version"] != VALIDATOR_VERSION or record["validator_result"] != "PASS":
        raise FirstCompletionValidationError("VALIDATOR_NOT_EXACT", "validator version/result are not the independent exact validator")
    if record["capture_completeness"] != "COMPLETE":
        raise FirstCompletionValidationError("CAPTURE_INCOMPLETE", "durable capture is incomplete")
    if record["process_return_code"] != 0:
        raise FirstCompletionValidationError("PROCESS_EXIT_NONZERO", "process did not return zero")
    if record["cleanup_status"] != "CONFIRMED_GONE":
        raise FirstCompletionValidationError("CHILD_CLEANUP_NOT_CONFIRMED", "process cleanup is not confirmed")
    if record["workspace_mode"] != "DISPOSABLE_READ_ONLY_FIXTURE" or record["side_effect_observation"] != "READ_ONLY_UNCHANGED":
        raise FirstCompletionValidationError("SIDE_EFFECT_SCOPE_NOT_PROVEN", "workspace/effect boundary is not exact")
    return {
        "status": PASS,
        "validated_completion": True,
        "validator_version": VALIDATOR_VERSION,
        "checks": {field: True for field in ("identity_binding", "lease_binding", "fixture_nonce", "workspace_unchanged", "structured_result_exact", "capture_complete", "process_zero", "cleanup_confirmed", "read_only_effect")},
        "failure_codes": [],
        "claim_ceiling": "One exact validator decision over a supplied synthetic read-only candidate record only; no production readiness, external truth, exactly-once behavior or general executor interchangeability is inferred.",
    }


__all__ = ["FirstCompletionValidationError", "PASS", "REQUIRED_BINDINGS", "VALIDATOR_VERSION", "expected_result_digest", "validate_exact_completion"]
