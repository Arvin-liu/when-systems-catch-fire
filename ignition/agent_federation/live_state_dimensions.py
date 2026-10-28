"""Machine-readable dimensions for live state without semantic compression.

The dimensions are intentionally observational.  In particular, an inference
status describes whether a public machine-verifiable inference marker was
observed; it does not claim what an executor privately did.
"""

from __future__ import annotations

import json
from typing import Any, Mapping


LIVE_STATE_DIMENSIONS_SCHEMA = "live-state-dimensions-r1"

DISPATCH_OBSERVATION_STATUSES = frozenset({"OBSERVED", "NOT_OBSERVED", "UNKNOWN"})
PROCESS_OBSERVATION_STATUSES = frozenset({"OBSERVED", "NOT_OBSERVED", "UNKNOWN"})
INFERENCE_OBSERVATION_STATUSES = frozenset({
    "OBSERVED", "NOT_OBSERVED", "UNKNOWN", "NOT_APPLICABLE_PRE_PROCESS",
})
VALIDATED_COMPLETION_STATUSES = frozenset({"VALIDATED", "NOT_VALIDATED", "UNKNOWN"})
RECONCILIATION_BLOCKER_STATUSES = frozenset({"NONE", "OPEN", "UNKNOWN"})
NEXT_ELIGIBLE_ACTIONS = frozenset({
    "RECONCILE_UNRECOVERED_ATTEMPTS",
    "RUN_DYNAMIC_EXECUTOR_ADMISSION",
    "REPAIR_EXECUTOR_CONTRACT",
    "STOP_LIVE_INVOCATION",
    "NO_ACTION",
    "UNKNOWN",
})

_RECONCILIATION_OPEN = frozenset({"OPEN", "REQUIRES_RECONCILIATION", "OPEN_REQUIRES_EVIDENCE"})
_RECONCILIATION_CLOSED = frozenset({
    "NOT_REQUIRED", "CLOSED", "CLOSED_NO_LIVE_DISPATCH", "CLOSED_RECONCILED",
    "TERMINAL_UNRECOVERABLE_EFFECT_UNKNOWN", "TERMINAL_UNRECOVERABLE_OBSERVATION_INCOMPLETE",
})


class LiveStateDimensionsError(ValueError):
    """Raised when independent live-state dimensions contradict one another."""


DIMENSION_CONTRACT: dict[str, dict[str, Any]] = {
    "live_dispatch_observation_status": {
        "source_authority": "typed observation outcome live_dispatch_calls and live_dispatch_started",
        "derivation": "OBSERVED only when a positive live dispatch count and explicit dispatch-start marker agree; zero plus explicit false is NOT_OBSERVED",
        "allowed_values": sorted(DISPATCH_OBSERVATION_STATUSES),
        "unknown_semantics": "UNKNOWN means the public record does not establish whether the live dispatch boundary was crossed",
        "historical_compatibility": "legacy return_code fields never establish this dimension",
    },
    "live_process_observation_status": {
        "source_authority": "typed observation outcome live_process_started and live_process_return_code",
        "derivation": "OBSERVED from explicit process start; NOT_OBSERVED from explicit false; a return code without start is invalid",
        "allowed_values": sorted(PROCESS_OBSERVATION_STATUSES),
        "unknown_semantics": "UNKNOWN means process lifecycle evidence was not recoverably captured",
        "historical_compatibility": "historical raw process fields remain provenance until a typed overlay binds their scope",
    },
    "inference_observation_status": {
        "source_authority": "independent public machine-verifiable inference marker, never transport call count",
        "derivation": "OBSERVED only from an explicit accepted inference marker; absent marker is NOT_OBSERVED after process observation and NOT_APPLICABLE_PRE_PROCESS before process start",
        "allowed_values": sorted(INFERENCE_OBSERVATION_STATUSES),
        "unknown_semantics": "UNKNOWN means the evidence cannot distinguish marker absence from lost observation; no private inference claim is made",
        "historical_compatibility": "live_inference_started booleans from Task140 remain historical provenance and are not canonical inference evidence",
    },
    "validated_completion_status": {
        "source_authority": "Pointfire independent validator exact-binding result",
        "derivation": "VALIDATED only after exact task/dispatch/attempt/executor/adapter/version/lease/workspace/capture/result/validator binding passes",
        "allowed_values": sorted(VALIDATED_COMPLETION_STATUSES),
        "unknown_semantics": "UNKNOWN means validation was not run or its binding cannot be established",
        "historical_compatibility": "exit code, structured result presence, or executor self-report alone never yields VALIDATED",
    },
    "reconciliation_blocker_status": {
        "source_authority": "canonical reconciliation event ledger and typed attempt reconciliation status",
        "derivation": "OPEN for unreconciled states; NONE for known terminal/non-required states; UNKNOWN for an unrecognized or missing reconciliation status",
        "allowed_values": sorted(RECONCILIATION_BLOCKER_STATUSES),
        "unknown_semantics": "UNKNOWN forbids a new live attempt until the reconciliation source is repaired or explicitly closed",
        "historical_compatibility": "terminal UNKNOWN effects remain UNKNOWN even when the repository evidence obligation is closed",
    },
    "next_eligible_action": {
        "source_authority": "Pointfire policy projection over the other dimensions",
        "derivation": "A policy action is selected only after reconciliation, completion and admission gates are evaluated independently",
        "allowed_values": sorted(NEXT_ELIGIBLE_ACTIONS),
        "unknown_semantics": "UNKNOWN means the policy cannot safely authorize a next action from current evidence",
        "historical_compatibility": "legacy current_live_ceiling strings are compatibility projections, not the source of action authority",
    },
}


def _copy(value: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _status_from_count(calls: Any, started: Any) -> str:
    if calls is None or started is None:
        return "UNKNOWN"
    if not isinstance(calls, int) or isinstance(calls, bool) or calls < 0:
        raise LiveStateDimensionsError("live_dispatch_calls must be a non-negative integer or null")
    if not isinstance(started, bool):
        raise LiveStateDimensionsError("live_dispatch_started must be boolean or null")
    if calls > 0 and started:
        return "OBSERVED"
    if calls == 0 and not started:
        return "NOT_OBSERVED"
    return "UNKNOWN"


def derive_dispatch_observation_status(observation: Mapping[str, Any]) -> str:
    return _status_from_count(observation.get("live_dispatch_calls"), observation.get("live_dispatch_started"))


def derive_process_observation_status(observation: Mapping[str, Any]) -> str:
    started = observation.get("live_process_started")
    return "UNKNOWN" if started is None else "OBSERVED" if started is True else "NOT_OBSERVED" if started is False else _invalid("live_process_started")


def derive_inference_observation_status(
    observation: Mapping[str, Any],
    *,
    explicit_status: str | None = None,
) -> str:
    if explicit_status is not None:
        if explicit_status not in INFERENCE_OBSERVATION_STATUSES:
            raise LiveStateDimensionsError("inference observation status is not allowed")
        return explicit_status
    process = derive_process_observation_status(observation)
    if process == "NOT_OBSERVED":
        return "NOT_APPLICABLE_PRE_PROCESS"
    if process == "OBSERVED":
        return "NOT_OBSERVED"
    return "UNKNOWN"


def derive_reconciliation_blocker_status(reconciliation_status: str | None) -> str:
    if reconciliation_status is None:
        return "UNKNOWN"
    if reconciliation_status in _RECONCILIATION_OPEN:
        return "OPEN"
    if reconciliation_status in _RECONCILIATION_CLOSED:
        return "NONE"
    return "UNKNOWN"


def derive_live_state_dimensions(
    observation: Mapping[str, Any],
    *,
    reconciliation_status: str | None,
    validated_completion: bool | None,
    explicit_inference_status: str | None = None,
    next_action: str = "UNKNOWN",
) -> dict[str, Any]:
    dispatch = derive_dispatch_observation_status(observation)
    process = derive_process_observation_status(observation)
    inference = derive_inference_observation_status(observation, explicit_status=explicit_inference_status)
    if validated_completion is True:
        completion = "VALIDATED"
    elif validated_completion is False:
        completion = "NOT_VALIDATED"
    elif validated_completion is None:
        completion = "UNKNOWN"
    else:
        raise LiveStateDimensionsError("validated_completion must be boolean or null")
    if next_action not in NEXT_ELIGIBLE_ACTIONS:
        raise LiveStateDimensionsError("next eligible action is not allowed")
    return validate_live_state_dimensions({
        "schema_version": LIVE_STATE_DIMENSIONS_SCHEMA,
        "live_dispatch_observation_status": dispatch,
        "live_process_observation_status": process,
        "inference_observation_status": inference,
        "validated_completion_status": completion,
        "reconciliation_blocker_status": derive_reconciliation_blocker_status(reconciliation_status),
        "next_eligible_action": next_action,
    })


def validate_live_state_dimensions(document: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise LiveStateDimensionsError("live state dimensions must be an object")
    value = _copy(document)
    required = {"schema_version", *DIMENSION_CONTRACT}
    if set(value) != required:
        raise LiveStateDimensionsError("live state dimension fields are not canonical")
    if value["schema_version"] != LIVE_STATE_DIMENSIONS_SCHEMA:
        raise LiveStateDimensionsError("live state dimension schema version mismatch")
    for field, contract in DIMENSION_CONTRACT.items():
        if value[field] not in contract["allowed_values"]:
            raise LiveStateDimensionsError(f"{field} contains an unsupported value")
    if value["live_process_observation_status"] == "NOT_OBSERVED" and value["inference_observation_status"] == "OBSERVED":
        raise LiveStateDimensionsError("inference cannot be observed before a live process is observed")
    if value["validated_completion_status"] == "VALIDATED" and value["live_process_observation_status"] != "OBSERVED":
        raise LiveStateDimensionsError("validated completion requires an observed live process")
    if value["validated_completion_status"] == "VALIDATED" and value["reconciliation_blocker_status"] != "NONE":
        raise LiveStateDimensionsError("validated completion requires no reconciliation blocker")
    return value


def _invalid(field: str) -> str:
    raise LiveStateDimensionsError(f"{field} has an invalid type")


__all__ = [
    "DIMENSION_CONTRACT", "DISPATCH_OBSERVATION_STATUSES", "INFERENCE_OBSERVATION_STATUSES",
    "LIVE_STATE_DIMENSIONS_SCHEMA", "LiveStateDimensionsError", "NEXT_ELIGIBLE_ACTIONS",
    "PROCESS_OBSERVATION_STATUSES", "RECONCILIATION_BLOCKER_STATUSES", "VALIDATED_COMPLETION_STATUSES",
    "derive_dispatch_observation_status", "derive_inference_observation_status",
    "derive_live_state_dimensions", "derive_process_observation_status",
    "derive_reconciliation_blocker_status", "validate_live_state_dimensions",
]
