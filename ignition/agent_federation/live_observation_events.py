"""Append-only typed observation outcome events bound to live attempts."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json
from agent_runtime.control import FileLock

from .live_observation_plane import validate_observation_outcome


OBSERVATION_EVENT_SCHEMA = "live-observation-event-r1"
OBSERVATION_EVENT_TYPE = "OBSERVATION_OUTCOME_RECORDED"
ZERO_HASH = "0" * 64
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
TASK_RE = re.compile(r"^IGNITION-[0-9]{8}-[0-9]+$")


class LiveObservationEventError(RuntimeError):
    """Base error for invalid typed observation events."""


class LiveObservationEventCorruption(LiveObservationEventError):
    """Raised when the observation event chain is not intact."""


class LiveObservationEventDuplicateError(LiveObservationEventError):
    """Raised when an attempt receives a second typed observation event."""


def _unsigned(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: document[key] for key in sorted(document) if key != "event_hash"}


def validate_event(document: Mapping[str, Any], *, check_hash: bool = True) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise LiveObservationEventError("observation event must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    required = {
        "schema_version", "sequence", "event_type", "task_id", "dispatch_id", "attempt_id",
        "prior_record_hash", "observation_outcome", "previous_event_hash", "event_hash", "claim_ceiling",
    }
    if set(value) != required:
        raise LiveObservationEventError("observation event fields are not canonical")
    if value["schema_version"] != OBSERVATION_EVENT_SCHEMA or value["event_type"] != OBSERVATION_EVENT_TYPE:
        raise LiveObservationEventError("observation event type or schema version is invalid")
    if not isinstance(value["sequence"], int) or isinstance(value["sequence"], bool) or value["sequence"] < 0:
        raise LiveObservationEventError("observation event sequence is invalid")
    if not isinstance(value["task_id"], str) or not TASK_RE.fullmatch(value["task_id"]):
        raise LiveObservationEventError("observation event task binding is invalid")
    for field in ("dispatch_id", "attempt_id"):
        if not isinstance(value[field], str) or not ID_RE.fullmatch(value[field]):
            raise LiveObservationEventError(f"observation event {field} is invalid")
    for field in ("prior_record_hash", "previous_event_hash"):
        if not isinstance(value[field], str) or not SHA256_RE.fullmatch(value[field]):
            raise LiveObservationEventError(f"observation event {field} must be a SHA-256 digest")
    if not isinstance(value["claim_ceiling"], str) or not value["claim_ceiling"].strip():
        raise LiveObservationEventError("observation event claim ceiling is missing")
    try:
        outcome = validate_observation_outcome(value["observation_outcome"])
    except ValueError as exc:
        raise LiveObservationEventError(f"observation outcome is invalid: {exc}") from exc
    if not isinstance(outcome, dict):
        raise LiveObservationEventError("observation outcome did not normalize to an object")
    if check_hash:
        if not isinstance(value["event_hash"], str) or not SHA256_RE.fullmatch(value["event_hash"]):
            raise LiveObservationEventError("observation event hash is invalid")
        if value["event_hash"] != sha256_json(_unsigned(value)):
            raise LiveObservationEventCorruption("observation event hash does not match immutable content")
    return value


class LiveObservationEventLedger:
    """Locked JSONL chain with at most one typed observation event per attempt."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        attempts: set[str] = set()
        previous = ZERO_HASH
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                raise LiveObservationEventCorruption(f"blank observation event line at {line_number}")
            try:
                event = validate_event(json.loads(line))
            except (json.JSONDecodeError, TypeError, LiveObservationEventError) as exc:
                raise LiveObservationEventCorruption(f"invalid observation event at line {line_number}") from exc
            if event["sequence"] != len(events) or event["previous_event_hash"] != previous:
                raise LiveObservationEventCorruption(f"observation event chain break at line {line_number}")
            if event["attempt_id"] in attempts:
                raise LiveObservationEventCorruption(f"duplicate observation event attempt at line {line_number}")
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
            "schema_version": OBSERVATION_EVENT_SCHEMA,
            "status": "PASS",
            "record_count": len(events),
            "attempt_count": len({event["attempt_id"] for event in events}),
            "head_hash": events[-1]["event_hash"] if events else ZERO_HASH,
            "claim_ceiling": "Append-only typed observation identity and field integrity only; no external effect or completion is inferred.",
        }

    def append(self, event: Mapping[str, Any], *, expected_task_id: str | None = None, expected_attempt_id: str | None = None) -> dict[str, Any]:
        candidate = json.loads(json.dumps(event, ensure_ascii=False))
        if not isinstance(candidate, dict):
            raise LiveObservationEventError("observation event must be an object")
        if any(field in candidate for field in ("sequence", "previous_event_hash", "event_hash")):
            raise LiveObservationEventError("append caller cannot provide immutable observation event fields")
        with FileLock(self.lock_path):
            existing = self._read_unlocked()
            if any(row["attempt_id"] == candidate.get("attempt_id") for row in existing):
                raise LiveObservationEventDuplicateError("attempt already has a typed observation event")
            if expected_task_id is not None and candidate.get("task_id") != expected_task_id:
                raise LiveObservationEventError("observation event task binding does not match expected task")
            if expected_attempt_id is not None and candidate.get("attempt_id") != expected_attempt_id:
                raise LiveObservationEventError("observation event attempt binding does not match expected attempt")
            candidate["schema_version"] = OBSERVATION_EVENT_SCHEMA
            candidate["event_type"] = OBSERVATION_EVENT_TYPE
            candidate["sequence"] = len(existing)
            candidate["previous_event_hash"] = existing[-1]["event_hash"] if existing else ZERO_HASH
            candidate["event_hash"] = sha256_json(_unsigned(candidate))
            normalized = validate_event(candidate)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
                import os
                os.fsync(handle.fileno())
            return normalized


def observation_overlay(path: str | Path) -> dict[str, dict[str, Any]]:
    return {event["attempt_id"]: event["observation_outcome"] for event in LiveObservationEventLedger(path).records()}


__all__ = [
    "OBSERVATION_EVENT_SCHEMA", "OBSERVATION_EVENT_TYPE", "LiveObservationEventError",
    "LiveObservationEventCorruption", "LiveObservationEventDuplicateError", "LiveObservationEventLedger",
    "observation_overlay", "validate_event",
]
