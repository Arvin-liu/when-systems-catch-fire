"""Append-only canonical records for bounded live external attempts.

This ledger is deliberately separate from model/tool output.  A record is
written only after the host has a final observation (possibly explicitly
incomplete), and an attempt identity can never be overwritten or reused.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json
from agent_runtime.control import FileLock


LIVE_ATTEMPT_LEDGER_SCHEMA = "live-attempt-ledger-r1"
ZERO_HASH = "0" * 64
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
TASK_RE = re.compile(r"^IGNITION-[0-9]{8}-[0-9]+$")

ATTEMPT_STATES = frozenset({
    "STARTUP_FAILURE",
    "TIMED_OUT_EFFECT_UNKNOWN",
    "FAILED_VALIDATION",
    "OBSERVATION_INCOMPLETE",
    "COMPLETED_VALIDATED",
    "RETURNED_UNVALIDATED",
    "MALFORMED_RESULT",
    "SKIPPED_UNSAFE_OR_UNAVAILABLE",
    "REQUIRES_RECONCILIATION",
})
COMPLETENESS = frozenset({"COMPLETE", "INCOMPLETE", "NOT_OBSERVED"})
PRIVATE_MARKERS = (
    "access_token", "api_key", "bearer ", "client_secret", "password", "secret",
    "hidden reasoning", "private model reasoning", "chain-of-thought", "chain of thought",
    "full_prompt", "raw_prompt", "prompt_body", "token_telemetry", "session_db",
)


class LiveAttemptLedgerError(RuntimeError):
    """Base error for invalid, unsafe, or conflicting attempt records."""


class LiveAttemptLedgerCorruption(LiveAttemptLedgerError):
    """Raised when an existing JSONL chain is not append-only and intact."""


class LiveAttemptDuplicateError(LiveAttemptLedgerError):
    """Raised when a dispatch or attempt identity is reused."""


class LiveAttemptBindingError(LiveAttemptLedgerError):
    """Raised when a record is bound to the wrong task, executor, or lease."""


def _is_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _ref(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise LiveAttemptLedgerError(f"{field} must be a non-empty public reference")
    if value not in {"UNRECOVERED", "NOT_APPLICABLE"} and not _is_sha(value):
        raise LiveAttemptLedgerError(f"{field} must be a SHA-256 digest or explicit unavailable marker")


def _timestamp_or_marker(value: Any, field: str, *, allow_not_applicable: bool = False) -> None:
    if value in {"UNRECOVERED", "NOT_APPLICABLE"}:
        if value == "NOT_APPLICABLE" and not allow_not_applicable:
            raise LiveAttemptLedgerError(f"{field} cannot be NOT_APPLICABLE")
        return
    if not isinstance(value, str) or not value:
        raise LiveAttemptLedgerError(f"{field} must be an ISO-8601 timestamp or explicit unavailable marker")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LiveAttemptLedgerError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LiveAttemptLedgerError(f"{field} must include a timezone")


def _scan_public(value: Any, field: str = "record") -> None:
    """Reject private output and reasoning material before a record is persisted."""

    if isinstance(value, str):
        lowered = value.casefold()
        if any(marker in lowered for marker in PRIVATE_MARKERS):
            raise LiveAttemptLedgerError(f"{field} contains private or hidden material")
        return
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str) or not key.strip():
                raise LiveAttemptLedgerError(f"{field} contains an invalid key")
            lowered = key.casefold()
            if any(marker in lowered for marker in PRIVATE_MARKERS) or "prompt" in lowered:
                raise LiveAttemptLedgerError(f"{field}.{key} is not a canonical public field")
            _scan_public(child, f"{field}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _scan_public(child, f"{field}[{index}]")
        return
    raise LiveAttemptLedgerError(f"{field} contains a non-JSON value")


def _schema_validate(document: Mapping[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover - clean bootstrap fallback
        return
    schema_path = Path(__file__).resolve().parents[1] / "schemas/operations/live-attempt-ledger-r1.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - packaging failure
        raise LiveAttemptLedgerError("live attempt ledger schema is unavailable") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.path) or "$"
        raise LiveAttemptLedgerError(f"ledger schema violation at {path}: {error.message}")


def validate_record(document: Mapping[str, Any], *, check_hash: bool = True) -> dict[str, Any]:
    """Validate one complete ledger record and return a JSON-safe copy."""

    if not isinstance(document, Mapping):
        raise LiveAttemptLedgerError("attempt record must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    _schema_validate(value)
    _scan_public(value)
    if value["schema_version"] != LIVE_ATTEMPT_LEDGER_SCHEMA:
        raise LiveAttemptLedgerError("attempt record schema version mismatch")
    if not isinstance(value["sequence"], int) or isinstance(value["sequence"], bool) or value["sequence"] < 0:
        raise LiveAttemptLedgerError("sequence must be a non-negative integer")
    for field in ("dispatch_id", "attempt_id"):
        if not isinstance(value[field], str) or not ID_RE.fullmatch(value[field]):
            raise LiveAttemptLedgerError(f"{field} must be a safe stable identity")
    if not isinstance(value["task_id"], str) or not TASK_RE.fullmatch(value["task_id"]):
        raise LiveAttemptLedgerError("task_id must be a canonical IGNITION task id")
    for field in ("capability_lease_digest", "workspace_digest_before", "workspace_digest_after", "runtime_scratch_lifecycle_digest"):
        _ref(value[field], field)
    lease_status = value["lease_binding_status"]
    if lease_status == "BOUND" and not _is_sha(value["capability_lease_digest"]):
        raise LiveAttemptLedgerError("BOUND lease must carry a SHA-256 capability lease digest")
    if lease_status == "UNRECOVERED" and value["capability_lease_digest"] != "UNRECOVERED":
        raise LiveAttemptLedgerError("UNRECOVERED lease binding must carry UNRECOVERED digest")
    _timestamp_or_marker(value["started_at"], "started_at")
    _timestamp_or_marker(value["ended_at"], "ended_at", allow_not_applicable=True)
    process = value["process"]
    if process["state"] not in ATTEMPT_STATES:
        raise LiveAttemptLedgerError("unknown process state")
    if process["return_code"] is not None and (not isinstance(process["return_code"], int) or isinstance(process["return_code"], bool)):
        raise LiveAttemptLedgerError("process return_code must be an integer or null")
    public_events = value["public_events"]
    if public_events["capture_completeness"] not in COMPLETENESS:
        raise LiveAttemptLedgerError("unknown public capture completeness")
    if public_events["capture_completeness"] != value["evidence_completeness"]:
        raise LiveAttemptLedgerError("capture and record evidence completeness disagree")
    for field in ("capture_digest", "stdout_digest", "stderr_digest"):
        _ref(public_events[field], f"public_events.{field}")
    if any(not isinstance(public_events[field], int) or isinstance(public_events[field], bool) or public_events[field] < 0 for field in ("event_count", "stdout_byte_count", "stderr_byte_count")):
        raise LiveAttemptLedgerError("public capture counts must be non-negative integers")
    structured = value["structured_result"]
    if structured["present"]:
        if not isinstance(structured["ref"], str) or not structured["ref"] or not _is_sha(structured["digest"]):
            raise LiveAttemptLedgerError("present structured result requires public ref and SHA-256 digest")
    elif structured["ref"] is not None or structured["digest"] not in {None, "UNRECOVERED", "NOT_APPLICABLE"}:
        raise LiveAttemptLedgerError("absent structured result cannot carry a result reference or digest")
    validator = value["validator"]
    if validator["status"] == "PASS":
        if not isinstance(validator["ref"], str) or not validator["ref"] or not _is_sha(validator["digest"]):
            raise LiveAttemptLedgerError("PASS validator requires public ref and SHA-256 digest")
    elif validator["status"] != "PASS" and validator["digest"] not in {None, "UNRECOVERED", "NOT_APPLICABLE"}:
        raise LiveAttemptLedgerError("non-PASS validator cannot claim a completed digest")
    if "observation_typing" in value:
        from agent_federation.live_observation_plane import validate_observation_outcome

        try:
            validate_observation_outcome(value["observation_typing"])
        except ValueError as exc:
            raise LiveAttemptLedgerError(f"typed observation outcome is invalid: {exc}") from exc
    state = process["state"]
    if value["evidence_completeness"] == "INCOMPLETE":
        if state not in {"OBSERVATION_INCOMPLETE", "REQUIRES_RECONCILIATION", "TIMED_OUT_EFFECT_UNKNOWN"}:
            raise LiveAttemptLedgerError("incomplete evidence has an incompatible process state")
        if validator["status"] == "PASS":
            raise LiveAttemptLedgerError("incomplete evidence cannot have a passing validator")
    if state == "COMPLETED_VALIDATED":
        if value["evidence_completeness"] != "COMPLETE" or not structured["present"] or validator["status"] != "PASS":
            raise LiveAttemptLedgerError("validated completion requires complete capture, result, and validator PASS")
        if value["reconciliation_status"] not in {"NOT_REQUIRED", "CLOSED"}:
            raise LiveAttemptLedgerError("validated completion cannot retain open reconciliation")
        if value["lease_binding_status"] != "BOUND":
            raise LiveAttemptLedgerError("validated completion requires exact lease binding")
    if validator["status"] == "PASS" and state != "COMPLETED_VALIDATED":
        raise LiveAttemptLedgerError("validator PASS can only be projected as completed validated")
    if value["reconciliation_status"] in {"OPEN", "REQUIRES_RECONCILIATION"} and state == "COMPLETED_VALIDATED":
        raise LiveAttemptLedgerError("open reconciliation cannot accompany validated completion")
    if check_hash:
        record_hash = value["record_hash"]
        if not _is_sha(record_hash):
            raise LiveAttemptLedgerError("record_hash must be a lowercase SHA-256 digest")
        if record_hash != sha256_json(_unsigned_record(value)):
            raise LiveAttemptLedgerCorruption("record hash does not match immutable record content")
    return value


def _unsigned_record(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: document[key] for key in sorted(document) if key != "record_hash"}


class LiveAttemptLedger:
    """Locked JSONL ledger whose attempt identities are append-only."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise LiveAttemptLedgerError("live attempt ledger cannot be read") from exc
        records: list[dict[str, Any]] = []
        dispatch_ids: set[str] = set()
        attempt_ids: set[str] = set()
        previous = ZERO_HASH
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                raise LiveAttemptLedgerCorruption(f"blank ledger line at {line_number}")
            try:
                record = validate_record(json.loads(line))
            except (json.JSONDecodeError, TypeError, LiveAttemptLedgerError) as exc:
                raise LiveAttemptLedgerCorruption(f"invalid ledger record at line {line_number}") from exc
            if record["sequence"] != len(records):
                raise LiveAttemptLedgerCorruption(f"sequence gap at line {line_number}")
            if record["previous_record_hash"] != previous:
                raise LiveAttemptLedgerCorruption(f"hash-chain break at line {line_number}")
            if record["dispatch_id"] in dispatch_ids or record["attempt_id"] in attempt_ids:
                raise LiveAttemptLedgerCorruption(f"duplicate dispatch or attempt identity at line {line_number}")
            dispatch_ids.add(record["dispatch_id"])
            attempt_ids.add(record["attempt_id"])
            previous = record["record_hash"]
            records.append(record)
        return records

    def records(self) -> list[dict[str, Any]]:
        with FileLock(self.lock_path):
            return self._read_unlocked()

    def append(
        self,
        record: Mapping[str, Any],
        *,
        expected_task_id: str | None = None,
        expected_executor_id: str | None = None,
        expected_lease_digest: str | None = None,
    ) -> dict[str, Any]:
        candidate = json.loads(json.dumps(record, ensure_ascii=False))
        if not isinstance(candidate, dict):
            raise LiveAttemptLedgerError("attempt record must be an object")
        for field in ("sequence", "previous_record_hash", "record_hash"):
            if field in candidate:
                raise LiveAttemptLedgerError(f"append caller cannot provide immutable {field}")
        candidate["schema_version"] = LIVE_ATTEMPT_LEDGER_SCHEMA
        with FileLock(self.lock_path):
            existing = self._read_unlocked()
            if any(item["dispatch_id"] == candidate.get("dispatch_id") for item in existing):
                raise LiveAttemptDuplicateError("dispatch_id already exists in append-only ledger")
            if any(item["attempt_id"] == candidate.get("attempt_id") for item in existing):
                raise LiveAttemptDuplicateError("attempt_id already exists in append-only ledger")
            if expected_task_id is not None and candidate.get("task_id") != expected_task_id:
                raise LiveAttemptBindingError("attempt record task binding does not match expected task")
            if expected_executor_id is not None and candidate.get("executor_id") != expected_executor_id:
                raise LiveAttemptBindingError("attempt record executor binding does not match expected executor")
            if expected_lease_digest is not None and candidate.get("capability_lease_digest") != expected_lease_digest:
                raise LiveAttemptBindingError("attempt record lease digest does not match expected lease")
            candidate["sequence"] = len(existing)
            candidate["previous_record_hash"] = existing[-1]["record_hash"] if existing else ZERO_HASH
            # The schema requires the immutable hash field even during the
            # pre-hash structural pass.  The placeholder is replaced below
            # before anything is written.
            candidate["record_hash"] = ZERO_HASH
            validate_record(candidate, check_hash=False)
            candidate["record_hash"] = sha256_json(_unsigned_record(candidate))
            normalized = validate_record(candidate)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
                import os
                os.fsync(handle.fileno())
            return normalized

    def audit(self) -> dict[str, Any]:
        records = self.records()
        return {
            "schema_version": LIVE_ATTEMPT_LEDGER_SCHEMA,
            "status": "PASS",
            "record_count": len(records),
            "dispatch_count": len({record["dispatch_id"] for record in records}),
            "attempt_count": len({record["attempt_id"] for record in records}),
            "head_hash": records[-1]["record_hash"] if records else ZERO_HASH,
            "claim_ceiling": "Append-only live-attempt identity and public evidence integrity only; no external success or truth is inferred.",
        }


__all__ = [
    "ATTEMPT_STATES", "COMPLETENESS", "LIVE_ATTEMPT_LEDGER_SCHEMA", "LiveAttemptBindingError",
    "LiveAttemptDuplicateError", "LiveAttemptLedger", "LiveAttemptLedgerCorruption",
    "LiveAttemptLedgerError", "validate_record",
]
