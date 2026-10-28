"""Typed observation outcomes for the bounded Live Observation Plane.

This module deliberately does not run a process or infer an outcome from a
provider return value.  It only gives every host observation an explicit
scope, preserving ``None`` when a lifecycle fact was not observed.
"""

from __future__ import annotations

import json
from typing import Any, Mapping


OBSERVATION_OUTCOME_SCHEMA = "live-observation-outcome-r1"
OBSERVATION_OUTCOME_TYPES = frozenset({
    "PRE_INFERENCE_NO_LIVE_PROCESS",
    "LIVE_PROCESS_OBSERVED",
    "LIVE_PROCESS_UNOBSERVED",
    "LEGACY_SCOPE_UNRECOVERED",
})


class LiveObservationOutcomeError(ValueError):
    """Raised when typed process-observation fields contradict one another."""


def _int_or_none(value: Any, field: str) -> int | None:
    if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
        raise LiveObservationOutcomeError(f"{field} must be an integer or null")
    return value


def _base_unknown(record: Mapping[str, Any]) -> dict[str, Any]:
    process = record["process"]
    events = record["public_events"]
    structured = record["structured_result"]
    validator = record["validator"]
    capture_initialized = events["capture_completeness"] != "NOT_OBSERVED"
    return {
        "schema_version": OBSERVATION_OUTCOME_SCHEMA,
        "observation_outcome_type": "LEGACY_SCOPE_UNRECOVERED",
        "probe_return_code": None,
        "transport_return_code": None,
        "public_probe_calls": None,
        "live_dispatch_calls": None,
        "live_dispatch_started": None,
        "live_process_started": None,
        "live_process_return_code": None,
        "capture_initialized": capture_initialized,
        "structured_result_present": bool(structured["present"]),
        "validator_status": validator["status"],
        "legacy_record_return_code_preserved": process["return_code"],
        "legacy_return_code_scope": "UNSCOPED_HISTORICAL_PROCESS_FIELD",
    }


def derive_observation_outcome(record: Mapping[str, Any]) -> dict[str, Any]:
    """Derive a typed public outcome without upgrading unknown evidence.

    Task139 sequence 4 has a correction record in the task source: its zero
    was the last public-probe/transport value and no live dispatch occurred.
    Other historical R1 records retain their old process field as preserved
    provenance but do not receive a newly invented live-process meaning.
    New adapters may provide an explicit ``observation_typing`` object.
    """

    explicit = record.get("observation_typing")
    if explicit is not None:
        candidate = json.loads(json.dumps(explicit, ensure_ascii=False))
        candidate.setdefault("schema_version", OBSERVATION_OUTCOME_SCHEMA)
        candidate.setdefault("structured_result_present", bool(record["structured_result"]["present"]))
        candidate.setdefault("validator_status", record["validator"]["status"])
        candidate.setdefault("capture_initialized", record["public_events"]["capture_completeness"] != "NOT_OBSERVED")
        return validate_observation_outcome(candidate)

    if record.get("task_id") == "IGNITION-20260825-139" and record.get("attempt_id") == "attempt-139-live-02":
        typed = {
            "schema_version": OBSERVATION_OUTCOME_SCHEMA,
            "observation_outcome_type": "PRE_INFERENCE_NO_LIVE_PROCESS",
            "probe_return_code": 0,
            "transport_return_code": 0,
            "public_probe_calls": 2,
            "live_dispatch_calls": 0,
            "live_dispatch_started": False,
            "live_process_started": False,
            "live_process_return_code": None,
            "capture_initialized": False,
            "structured_result_present": False,
            "validator_status": "UNKNOWN",
            "legacy_record_return_code_preserved": record["process"]["return_code"],
            "legacy_return_code_scope": "PUBLIC_PROBE_TRANSPORT_VALUE_ONLY",
        }
        return validate_observation_outcome(typed)
    return validate_observation_outcome(_base_unknown(record))


def validate_observation_outcome(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate typed probe/transport/process/capture/result fields."""

    if not isinstance(document, Mapping):
        raise LiveObservationOutcomeError("observation outcome must be an object")
    value = json.loads(json.dumps(document, ensure_ascii=False))
    required = {
        "schema_version", "observation_outcome_type", "probe_return_code", "transport_return_code",
        "public_probe_calls", "live_dispatch_calls", "live_dispatch_started", "live_process_started",
        "live_process_return_code", "capture_initialized", "structured_result_present", "validator_status",
        "legacy_record_return_code_preserved", "legacy_return_code_scope",
    }
    if set(value) != required:
        raise LiveObservationOutcomeError("typed observation outcome fields are not canonical")
    if value["schema_version"] != OBSERVATION_OUTCOME_SCHEMA:
        raise LiveObservationOutcomeError("typed observation outcome schema version mismatch")
    if value["observation_outcome_type"] not in OBSERVATION_OUTCOME_TYPES:
        raise LiveObservationOutcomeError("unknown typed observation outcome type")
    for field in ("probe_return_code", "transport_return_code", "live_process_return_code", "legacy_record_return_code_preserved"):
        _int_or_none(value[field], field)
    for field in ("public_probe_calls", "live_dispatch_calls"):
        _int_or_none(value[field], field)
        if value[field] is not None and value[field] < 0:
            raise LiveObservationOutcomeError(f"{field} must be non-negative")
    for field in ("live_dispatch_started", "live_process_started", "capture_initialized", "structured_result_present"):
        if not isinstance(value[field], (bool, type(None))):
            raise LiveObservationOutcomeError(f"{field} must be boolean or null")
    if not isinstance(value["validator_status"], str) or not value["validator_status"]:
        raise LiveObservationOutcomeError("validator_status must be a non-empty string")
    if not isinstance(value["legacy_return_code_scope"], str) or not value["legacy_return_code_scope"]:
        raise LiveObservationOutcomeError("legacy_return_code_scope must be explicit")
    if value["live_process_started"] is False:
        if value["live_process_return_code"] is not None:
            raise LiveObservationOutcomeError("live_process_return_code must be null when live_process_started is false")
        if value["live_dispatch_started"] is True:
            raise LiveObservationOutcomeError("live dispatch cannot be started when live process is explicitly not started")
    if value["live_dispatch_calls"] == 0:
        if value["live_dispatch_started"] is not False or value["live_process_started"] is not False:
            raise LiveObservationOutcomeError("zero live dispatch calls require explicit false dispatch and process starts")
    if value["observation_outcome_type"] == "PRE_INFERENCE_NO_LIVE_PROCESS":
        if value["live_process_started"] is not False or value["live_process_return_code"] is not None:
            raise LiveObservationOutcomeError("pre-inference outcome has an observed live-process contradiction")
    if value["capture_initialized"] is False:
        if value["structured_result_present"] or value["validator_status"] == "PASS":
            raise LiveObservationOutcomeError("absent capture cannot carry structured result or validator PASS")
    return value


__all__ = [
    "OBSERVATION_OUTCOME_SCHEMA",
    "OBSERVATION_OUTCOME_TYPES",
    "LiveObservationOutcomeError",
    "derive_observation_outcome",
    "validate_observation_outcome",
]
