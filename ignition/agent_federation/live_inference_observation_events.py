"""Append-only public inference-marker observations.

This ledger is a correction/provenance overlay.  It never rewrites the older
R1 process-observation ledger and never claims what an executor inferred
privately.  ``OBSERVED`` requires an explicit public machine-verifiable marker;
``NOT_OBSERVED`` means that no such marker was present in the bounded public
capture, not that private inference did not happen.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping

from agent_kernel.contracts import sha256_json
from agent_runtime.control import FileLock


INFERENCE_OBSERVATION_EVENT_SCHEMA = "live-inference-observation-event-r1"
INFERENCE_OBSERVATION_EVENT_TYPE = "INFERENCE_OBSERVATION_CORRECTION_RECORDED"
INFERENCE_OBSERVATION_STATUSES = frozenset({
    "OBSERVED", "NOT_OBSERVED", "UNKNOWN", "NOT_APPLICABLE_PRE_PROCESS",
})
ZERO_HASH = "0" * 64
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
TASK_RE = re.compile(r"^IGNITION-[0-9]{8}-[0-9]+$")


class InferenceObservationEventError(RuntimeError):
    """Raised for an invalid public inference observation event."""


class InferenceObservationEventCorruption(InferenceObservationEventError):
    """Raised when the append-only inference event chain is not intact."""


class InferenceObservationEventDuplicateError(InferenceObservationEventError):
    """Raised when an attempt receives a second inference observation event."""


def _unsigned(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: document[key] for key in sorted(document) if key != "event_hash"}


def validate_inference_observation_event(document: Mapping[str, Any], *, check_hash: bool = True) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise InferenceObservationEventError("inference observation event must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    required = {
        "schema_version", "sequence", "event_type", "task_id", "dispatch_id", "attempt_id",
        "prior_record_hash", "inference_observation_status", "marker_observed", "marker_source",
        "evidence_scope", "previous_event_hash", "event_hash", "claim_ceiling",
    }
    if set(value) != required:
        raise InferenceObservationEventError("inference observation event fields are not canonical")
    if value["schema_version"] != INFERENCE_OBSERVATION_EVENT_SCHEMA or value["event_type"] != INFERENCE_OBSERVATION_EVENT_TYPE:
        raise InferenceObservationEventError("inference observation event type or schema is invalid")
    if not isinstance(value["sequence"], int) or isinstance(value["sequence"], bool) or value["sequence"] < 0:
        raise InferenceObservationEventError("inference observation sequence is invalid")
    if not isinstance(value["task_id"], str) or not TASK_RE.fullmatch(value["task_id"]):
        raise InferenceObservationEventError("inference observation task binding is invalid")
    for field in ("dispatch_id", "attempt_id"):
        if not isinstance(value[field], str) or not ID_RE.fullmatch(value[field]):
            raise InferenceObservationEventError(f"inference observation {field} is invalid")
    for field in ("prior_record_hash", "previous_event_hash"):
        if not isinstance(value[field], str) or not SHA256_RE.fullmatch(value[field]):
            raise InferenceObservationEventError(f"inference observation {field} must be a SHA-256 digest")
    if value["inference_observation_status"] not in INFERENCE_OBSERVATION_STATUSES:
        raise InferenceObservationEventError("inference observation status is invalid")
    if not isinstance(value["marker_observed"], bool):
        raise InferenceObservationEventError("marker_observed must be boolean")
    if value["inference_observation_status"] == "OBSERVED" and not value["marker_observed"]:
        raise InferenceObservationEventError("OBSERVED inference status requires marker_observed=true")
    if value["inference_observation_status"] != "OBSERVED" and value["marker_observed"]:
        raise InferenceObservationEventError("non-observed inference status cannot carry marker_observed=true")
    for field in ("marker_source", "evidence_scope", "claim_ceiling"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise InferenceObservationEventError(f"{field} is missing")
    if check_hash:
        if not isinstance(value["event_hash"], str) or not SHA256_RE.fullmatch(value["event_hash"]):
            raise InferenceObservationEventError("inference observation event hash is invalid")
        if value["event_hash"] != sha256_json(_unsigned(value)):
            raise InferenceObservationEventCorruption("inference observation event hash does not match content")
    return value


class LiveInferenceObservationEventLedger:
    """Locked JSONL chain with at most one inference event per attempt."""

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
                raise InferenceObservationEventCorruption(f"blank inference observation line at {line_number}")
            try:
                event = validate_inference_observation_event(json.loads(line))
            except (json.JSONDecodeError, TypeError, InferenceObservationEventError) as exc:
                raise InferenceObservationEventCorruption(f"invalid inference observation event at line {line_number}") from exc
            if event["sequence"] != len(events) or event["previous_event_hash"] != previous:
                raise InferenceObservationEventCorruption(f"inference observation chain break at line {line_number}")
            if event["attempt_id"] in attempts:
                raise InferenceObservationEventCorruption(f"duplicate inference observation attempt at line {line_number}")
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
            "schema_version": INFERENCE_OBSERVATION_EVENT_SCHEMA,
            "status": "PASS",
            "record_count": len(events),
            "attempt_count": len({event["attempt_id"] for event in events}),
            "head_hash": events[-1]["event_hash"] if events else ZERO_HASH,
            "claim_ceiling": "Append-only public inference-marker observation integrity only; no private inference or validated completion is inferred.",
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
            raise InferenceObservationEventError("inference observation event must be an object")
        if any(field in candidate for field in ("sequence", "previous_event_hash", "event_hash")):
            raise InferenceObservationEventError("append caller cannot provide immutable inference event fields")
        with FileLock(self.lock_path):
            existing = self._read_unlocked()
            if any(row["attempt_id"] == candidate.get("attempt_id") for row in existing):
                raise InferenceObservationEventDuplicateError("attempt already has an inference observation event")
            if expected_task_id is not None and candidate.get("task_id") != expected_task_id:
                raise InferenceObservationEventError("inference event task binding does not match expected task")
            if expected_attempt_id is not None and candidate.get("attempt_id") != expected_attempt_id:
                raise InferenceObservationEventError("inference event attempt binding does not match expected attempt")
            candidate["schema_version"] = INFERENCE_OBSERVATION_EVENT_SCHEMA
            candidate["event_type"] = INFERENCE_OBSERVATION_EVENT_TYPE
            candidate["sequence"] = len(existing)
            candidate["previous_event_hash"] = existing[-1]["event_hash"] if existing else ZERO_HASH
            candidate["event_hash"] = sha256_json(_unsigned(candidate))
            normalized = validate_inference_observation_event(candidate)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
                import os
                os.fsync(handle.fileno())
            return normalized


def inference_observation_overlay(path: str | Path) -> dict[str, str]:
    return {
        event["attempt_id"]: event["inference_observation_status"]
        for event in LiveInferenceObservationEventLedger(path).records()
    }


__all__ = [
    "INFERENCE_OBSERVATION_EVENT_SCHEMA", "INFERENCE_OBSERVATION_EVENT_TYPE",
    "INFERENCE_OBSERVATION_STATUSES", "InferenceObservationEventCorruption",
    "InferenceObservationEventDuplicateError", "InferenceObservationEventError",
    "LiveInferenceObservationEventLedger", "inference_observation_overlay",
    "validate_inference_observation_event",
]
