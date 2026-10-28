"""Append-only canonical reconciliation events for historical live attempts."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json
from agent_runtime.control import FileLock
from agent_federation.live_reconciliation import validate_reconciliation_state


RECONCILIATION_EVENT_SCHEMA = "live-reconciliation-event-r1"
ZERO_HASH = "0" * 64
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
TASK_RE = re.compile(r"^IGNITION-[0-9]{8}-[0-9]+$")


class LiveReconciliationEventError(RuntimeError):
    """Base error for invalid or unsafe reconciliation events."""


class LiveReconciliationEventCorruption(LiveReconciliationEventError):
    """Raised when the append-only event chain is not intact."""


class LiveReconciliationEventDuplicateError(LiveReconciliationEventError):
    """Raised when an attempt receives a second canonical event."""


def _unsigned(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: document[key] for key in sorted(document) if key != "event_hash"}


def _schema_validate(document: Mapping[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover - clean bootstrap fallback
        return
    schema_path = Path(__file__).resolve().parents[1] / "schemas/operations/live-reconciliation-event-r1.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - packaging failure
        raise LiveReconciliationEventError("reconciliation event schema is unavailable") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.path) or "$"
        raise LiveReconciliationEventError(f"reconciliation event schema violation at {path}: {error.message}")


def validate_event(document: Mapping[str, Any], *, check_hash: bool = True) -> dict[str, Any]:
    """Validate one immutable reconciliation event."""

    if not isinstance(document, Mapping):
        raise LiveReconciliationEventError("reconciliation event must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    _schema_validate(value)
    required = {
        "schema_version", "sequence", "event_type", "task_id", "dispatch_id", "attempt_id", "executor_id",
        "prior_record_hash", "reconciliation_state", "previous_event_hash", "event_hash", "claim_ceiling",
    }
    if set(value) != required:
        raise LiveReconciliationEventError("reconciliation event fields are not canonical")
    if value["schema_version"] != RECONCILIATION_EVENT_SCHEMA:
        raise LiveReconciliationEventError("reconciliation event schema version mismatch")
    if not isinstance(value["sequence"], int) or isinstance(value["sequence"], bool) or value["sequence"] < 0:
        raise LiveReconciliationEventError("event sequence must be a non-negative integer")
    if value["event_type"] != "RECONCILIATION_STATE_RECORDED":
        raise LiveReconciliationEventError("unknown reconciliation event type")
    if not isinstance(value["task_id"], str) or not TASK_RE.fullmatch(value["task_id"]):
        raise LiveReconciliationEventError("event task binding is invalid")
    for field in ("dispatch_id", "attempt_id", "executor_id"):
        if not isinstance(value[field], str) or not ID_RE.fullmatch(value[field]):
            raise LiveReconciliationEventError(f"event {field} is invalid")
    for field in ("prior_record_hash", "previous_event_hash"):
        if not isinstance(value[field], str) or not SHA256_RE.fullmatch(value[field]):
            raise LiveReconciliationEventError(f"event {field} must be a lowercase SHA-256 digest")
    if not isinstance(value["claim_ceiling"], str) or not value["claim_ceiling"].strip():
        raise LiveReconciliationEventError("event claim ceiling is missing")
    state = validate_reconciliation_state(value["reconciliation_state"])
    if state["task_id"] != value["task_id"] or state["attempt_id"] != value["attempt_id"] or state["prior_record_hash"] != value["prior_record_hash"]:
        raise LiveReconciliationEventError("event and reconciliation state bindings disagree")
    if check_hash:
        event_hash = value["event_hash"]
        if not isinstance(event_hash, str) or not SHA256_RE.fullmatch(event_hash):
            raise LiveReconciliationEventError("event_hash must be a lowercase SHA-256 digest")
        if event_hash != sha256_json(_unsigned(value)):
            raise LiveReconciliationEventCorruption("event hash does not match immutable event content")
    return value


class LiveReconciliationEventLedger:
    """Locked JSONL chain with at most one reconciliation event per attempt."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise LiveReconciliationEventError("reconciliation event ledger cannot be read") from exc
        events: list[dict[str, Any]] = []
        attempts: set[str] = set()
        previous = ZERO_HASH
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                raise LiveReconciliationEventCorruption(f"blank event line at {line_number}")
            try:
                event = validate_event(json.loads(line))
            except (json.JSONDecodeError, TypeError, LiveReconciliationEventError) as exc:
                raise LiveReconciliationEventCorruption(f"invalid reconciliation event at line {line_number}") from exc
            if event["sequence"] != len(events):
                raise LiveReconciliationEventCorruption(f"event sequence gap at line {line_number}")
            if event["previous_event_hash"] != previous:
                raise LiveReconciliationEventCorruption(f"event hash-chain break at line {line_number}")
            if event["attempt_id"] in attempts:
                raise LiveReconciliationEventCorruption(f"duplicate attempt event at line {line_number}")
            attempts.add(event["attempt_id"])
            previous = event["event_hash"]
            events.append(event)
        return events

    def records(self) -> list[dict[str, Any]]:
        with FileLock(self.lock_path):
            return self._read_unlocked()

    def audit(self) -> dict[str, Any]:
        events = self.records()
        return {
            "schema_version": RECONCILIATION_EVENT_SCHEMA,
            "status": "PASS",
            "record_count": len(events),
            "attempt_count": len({event["attempt_id"] for event in events}),
            "head_hash": events[-1]["event_hash"] if events else ZERO_HASH,
            "claim_ceiling": "Append-only reconciliation event identity and state integrity only; external effect remains UNKNOWN unless a separate validator proves otherwise.",
        }

    def append(
        self,
        event: Mapping[str, Any],
        *,
        expected_task_id: str | None = None,
        expected_attempt_id: str | None = None,
    ) -> dict[str, Any]:
        candidate = json.loads(json.dumps(event, ensure_ascii=False))
        if not isinstance(candidate, dict):
            raise LiveReconciliationEventError("reconciliation event must be an object")
        for field in ("sequence", "previous_event_hash", "event_hash"):
            if field in candidate:
                raise LiveReconciliationEventError(f"append caller cannot provide immutable {field}")
        with FileLock(self.lock_path):
            existing = self._read_unlocked()
            if any(row["attempt_id"] == candidate.get("attempt_id") for row in existing):
                raise LiveReconciliationEventDuplicateError("attempt already has a reconciliation event")
            if expected_task_id is not None and candidate.get("task_id") != expected_task_id:
                raise LiveReconciliationEventError("event task binding does not match expected task")
            if expected_attempt_id is not None and candidate.get("attempt_id") != expected_attempt_id:
                raise LiveReconciliationEventError("event attempt binding does not match expected attempt")
            candidate["schema_version"] = RECONCILIATION_EVENT_SCHEMA
            candidate["sequence"] = len(existing)
            candidate["previous_event_hash"] = existing[-1]["event_hash"] if existing else ZERO_HASH
            candidate["event_hash"] = sha256_json(_unsigned(candidate))
            validated = validate_event(candidate)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            return validated


def reconciliation_overlay(path: str | Path) -> dict[str, dict[str, Any]]:
    """Return attempt-id to validated state overlay for projection builders."""

    return {event["attempt_id"]: event["reconciliation_state"] for event in LiveReconciliationEventLedger(path).records()}


__all__ = [
    "RECONCILIATION_EVENT_SCHEMA",
    "ZERO_HASH",
    "LiveReconciliationEventError",
    "LiveReconciliationEventCorruption",
    "LiveReconciliationEventDuplicateError",
    "LiveReconciliationEventLedger",
    "reconciliation_overlay",
    "validate_event",
]
