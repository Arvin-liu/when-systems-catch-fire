"""OS-owned contracts for bounded live external-executor dispatch.

This module is deliberately a contract layer.  It does not contain a model
client, tool loop, gateway, scheduler, or session store.  External session
values are opaque pointers and the only durable result shape is a sanitized
receipt owned by the Ignition OS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contracts import FederationContractError, canonical_digest
from .sdk import map_capabilities


LIVE_DISPATCH_SCHEMA = "live-dispatch-envelope-r1"
LIVE_LEASE_SCHEMA = "live-capability-lease-r1"
LIVE_RECEIPT_SCHEMA = "live-executor-receipt-r1"

LIVE_DISPATCH_STATES = frozenset({
    "CREATED", "ADMITTED", "DISPATCHING", "IN_FLIGHT", "RETURNED_UNVALIDATED",
    "VALIDATING", "COMPLETED_VALIDATED", "REJECTED_POLICY", "REJECTED_CAPABILITY",
    "REJECTED_COST_AUTHORITY", "TIMED_OUT_KNOWN_NO_EFFECT", "TIMED_OUT_EFFECT_UNKNOWN",
    "CANCEL_REQUESTED", "CANCEL_CONFIRMED", "REQUIRES_RECONCILIATION",
    "VALIDATION_FAILED", "MALFORMED_RESULT", "EXECUTOR_UNAVAILABLE",
})
LIVE_TERMINAL_STATES = frozenset({
    "COMPLETED_VALIDATED", "REJECTED_POLICY", "REJECTED_CAPABILITY",
    "REJECTED_COST_AUTHORITY", "TIMED_OUT_KNOWN_NO_EFFECT", "TIMED_OUT_EFFECT_UNKNOWN",
    "CANCEL_CONFIRMED", "REQUIRES_RECONCILIATION", "VALIDATION_FAILED",
    "MALFORMED_RESULT", "EXECUTOR_UNAVAILABLE",
})
LIVE_ELIGIBILITY = frozenset({
    "ELIGIBLE_FOR_LIVE_READONLY",
    "SKIPPED_COST_OR_AUTHORITY_UNCERTAIN",
    "SKIPPED_UNSAFE_WORKSPACE_OR_CHANNEL_BOUNDARY",
    "SKIPPED_NOT_AUTHENTICATED",
    "SKIPPED_INTERFACE_UNSUPPORTED",
    "SKIPPED_EXECUTOR_UNAVAILABLE",
})
LIVE_SIDE_EFFECT_CLASSES = frozenset({"READ_ONLY_SYNTHETIC", "NO_EXTERNAL_SIDE_EFFECT"})
LIVE_NETWORK_CLASSES = frozenset({"DISABLED", "INFERENCE_TRANSPORT_ONLY"})
LIVE_WORKSPACE_MODES = frozenset({"DISPOSABLE_READ_ONLY", "DISPOSABLE_SYNTHETIC_READ_ONLY"})
LIVE_RETRY_POLICIES = frozenset({"NO_BLIND_RETRY", "LINEAGE_ONLY_NO_BLIND_RETRY"})
LIVE_RECONCILIATION_POLICIES = frozenset({"REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT", "REQUIRE_ON_UNKNOWN_EFFECT"})
LIVE_BUDGET_AUTHORITIES = frozenset({"NO_NEW_BILLING_AUTHORITY", "EXISTING_AUTHORITY_NO_CHANGE"})
LIVE_VALIDATION_STATUSES = frozenset({"NOT_RUN", "PASS", "FAIL"})
LIVE_RECONCILIATION_STATUSES = frozenset({"NOT_REQUIRED", "OPEN", "CLOSED"})
LIVE_CANCEL_STATES = frozenset({"NOT_REQUESTED", "NOT_SUPPORTED", "REQUESTED", "CONFIRMED", "UNKNOWN"})
LIVE_SIDE_EFFECT_OBSERVATIONS = frozenset({"NO_EFFECT_OBSERVED", "READ_ONLY_UNCHANGED", "UNKNOWN", "FORBIDDEN_EFFECT_OBSERVED"})
_HIDDEN_MARKERS = frozenset({
    "prompt", "system_prompt", "chain_of_thought", "cot", "thoughts", "reasoning",
    "reasoning_tokens", "token", "api_key", "secret", "cookie", "authorization",
    "password", "provider_telemetry", "session_transcript",
})

LIVE_TRANSITIONS: dict[str, frozenset[str]] = {
    "CREATED": frozenset({"ADMITTED", "REJECTED_POLICY", "REJECTED_CAPABILITY", "REJECTED_COST_AUTHORITY", "EXECUTOR_UNAVAILABLE"}),
    "ADMITTED": frozenset({"DISPATCHING", "REJECTED_POLICY", "REJECTED_CAPABILITY", "REJECTED_COST_AUTHORITY", "CANCEL_REQUESTED", "EXECUTOR_UNAVAILABLE"}),
    "DISPATCHING": frozenset({"IN_FLIGHT", "RETURNED_UNVALIDATED", "TIMED_OUT_KNOWN_NO_EFFECT", "TIMED_OUT_EFFECT_UNKNOWN", "CANCEL_REQUESTED", "MALFORMED_RESULT", "EXECUTOR_UNAVAILABLE"}),
    "IN_FLIGHT": frozenset({"RETURNED_UNVALIDATED", "TIMED_OUT_KNOWN_NO_EFFECT", "TIMED_OUT_EFFECT_UNKNOWN", "CANCEL_REQUESTED", "MALFORMED_RESULT", "EXECUTOR_UNAVAILABLE"}),
    "RETURNED_UNVALIDATED": frozenset({"VALIDATING", "REQUIRES_RECONCILIATION", "MALFORMED_RESULT"}),
    "VALIDATING": frozenset({"COMPLETED_VALIDATED", "VALIDATION_FAILED", "REQUIRES_RECONCILIATION"}),
    "CANCEL_REQUESTED": frozenset({"CANCEL_CONFIRMED", "IN_FLIGHT", "TIMED_OUT_EFFECT_UNKNOWN", "REQUIRES_RECONCILIATION"}),
    "REQUIRES_RECONCILIATION": frozenset({"VALIDATING", "CANCEL_CONFIRMED", "VALIDATION_FAILED"}),
    "COMPLETED_VALIDATED": frozenset(),
    "REJECTED_POLICY": frozenset(),
    "REJECTED_CAPABILITY": frozenset(),
    "REJECTED_COST_AUTHORITY": frozenset(),
    "TIMED_OUT_KNOWN_NO_EFFECT": frozenset(),
    "TIMED_OUT_EFFECT_UNKNOWN": frozenset(),
    "CANCEL_CONFIRMED": frozenset(),
    "VALIDATION_FAILED": frozenset(),
    "MALFORMED_RESULT": frozenset(),
    "EXECUTOR_UNAVAILABLE": frozenset(),
}


def _strict(data: Mapping[str, Any], keys: set[str], name: str) -> None:
    if not isinstance(data, Mapping) or set(data) != keys:
        actual = sorted(data) if isinstance(data, Mapping) else type(data).__name__
        raise FederationContractError(f"{name} keys must be exactly {sorted(keys)}; got {actual}")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FederationContractError(f"{field} must be a non-empty string")
    return value.strip()


def _enum(value: Any, allowed: frozenset[str], field: str) -> str:
    value = _text(value, field)
    if value not in allowed:
        raise FederationContractError(f"{field} is unsupported: {value}")
    return value


def _strings(values: Sequence[str], field: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise FederationContractError(f"{field} must be an array")
    result = tuple(_text(value, f"{field}[]") for value in values)
    if nonempty and not result:
        raise FederationContractError(f"{field} must not be empty")
    if len(result) != len(set(result)):
        raise FederationContractError(f"{field} must not contain duplicates")
    return result


def _digest(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise FederationContractError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _optional_digest(value: Any, field: str) -> str | None:
    return None if value is None else _digest(value, field)


def _public(value: Any, field: str, *, depth: int = 0) -> Any:
    if depth > 6:
        raise FederationContractError(f"{field} is too deeply nested")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            normalized = name.casefold()
            if normalized in _HIDDEN_MARKERS or any(marker in normalized for marker in ("api_key", "secret", "password", "chain_of_thought")):
                raise FederationContractError(f"{field} contains prohibited private field: {name}")
            result[name] = _public(item, f"{field}.{name}", depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        return [_public(item, f"{field}[]", depth=depth + 1) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise FederationContractError(f"{field} contains unsupported value type")


def _capabilities(values: Sequence[str], field: str, *, nonempty: bool = False) -> tuple[str, ...]:
    values = _strings(values, field, nonempty=nonempty)
    try:
        return map_capabilities(values)
    except FederationContractError:
        raise
    except Exception as exc:  # AdapterSDKError is deliberately normalized at this boundary.
        raise FederationContractError(f"{field} contains an unsupported capability") from exc


@dataclass(frozen=True)
class LiveDispatchEnvelope:
    schema_version: str
    task_id: str
    dispatch_id: str
    attempt_id: str
    executor_id: str
    adapter_id: str
    capability_id: str
    capability_lease_ref: str
    workspace_ref: str
    workspace_mode: str
    permission_ceiling: tuple[str, ...]
    side_effect_class: str
    network_class: str
    intent_capsule_ref: str | None
    synthetic_input_ref: str
    synthetic_input_digest: str
    success_criteria: tuple[str, ...]
    output_contract: Mapping[str, Any]
    deadline: str
    timeout_seconds: float
    retry_policy: str
    reconciliation_policy: str
    budget_authority: str
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.schema_version != LIVE_DISPATCH_SCHEMA:
            raise FederationContractError("live dispatch schema version mismatch")
        for field in ("task_id", "dispatch_id", "attempt_id", "executor_id", "adapter_id", "capability_id", "capability_lease_ref", "workspace_ref", "synthetic_input_ref", "deadline"):
            _text(getattr(self, field), f"live_dispatch.{field}")
        object.__setattr__(self, "workspace_mode", _enum(self.workspace_mode, LIVE_WORKSPACE_MODES, "live_dispatch.workspace_mode"))
        object.__setattr__(self, "permission_ceiling", _capabilities(self.permission_ceiling, "live_dispatch.permission_ceiling", nonempty=True))
        object.__setattr__(self, "side_effect_class", _enum(self.side_effect_class, LIVE_SIDE_EFFECT_CLASSES, "live_dispatch.side_effect_class"))
        object.__setattr__(self, "network_class", _enum(self.network_class, LIVE_NETWORK_CLASSES, "live_dispatch.network_class"))
        if set(self.permission_ceiling) - {"repo.read", "structured_progress"}:
            raise FederationContractError("live_dispatch read-only synthetic permission ceiling is wider than repo.read/structured_progress")
        object.__setattr__(self, "synthetic_input_digest", _digest(self.synthetic_input_digest, "live_dispatch.synthetic_input_digest"))
        object.__setattr__(self, "success_criteria", _strings(self.success_criteria, "live_dispatch.success_criteria", nonempty=True))
        if not isinstance(self.output_contract, Mapping):
            raise FederationContractError("live_dispatch.output_contract must be an object")
        output = _public(self.output_contract, "live_dispatch.output_contract")
        if not isinstance(output.get("format"), str) or not output["format"].strip():
            raise FederationContractError("live_dispatch.output_contract.format is required")
        required = output.get("required_fields", ())
        object.__setattr__(self, "output_contract", {**output, "required_fields": list(_strings(required, "live_dispatch.output_contract.required_fields"))})
        if not isinstance(self.timeout_seconds, (int, float)) or isinstance(self.timeout_seconds, bool) or self.timeout_seconds <= 0:
            raise FederationContractError("live_dispatch.timeout_seconds must be positive")
        object.__setattr__(self, "retry_policy", _enum(self.retry_policy, LIVE_RETRY_POLICIES, "live_dispatch.retry_policy"))
        object.__setattr__(self, "reconciliation_policy", _enum(self.reconciliation_policy, LIVE_RECONCILIATION_POLICIES, "live_dispatch.reconciliation_policy"))
        object.__setattr__(self, "budget_authority", _enum(self.budget_authority, LIVE_BUDGET_AUTHORITIES, "live_dispatch.budget_authority"))
        if self.intent_capsule_ref is not None:
            _text(self.intent_capsule_ref, "live_dispatch.intent_capsule_ref")
        object.__setattr__(self, "provenance", _public(self.provenance, "live_dispatch.provenance"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "task_id": self.task_id, "dispatch_id": self.dispatch_id,
            "attempt_id": self.attempt_id, "executor_id": self.executor_id, "adapter_id": self.adapter_id,
            "capability_id": self.capability_id, "capability_lease_ref": self.capability_lease_ref,
            "workspace_ref": self.workspace_ref, "workspace_mode": self.workspace_mode,
            "permission_ceiling": list(self.permission_ceiling), "side_effect_class": self.side_effect_class,
            "network_class": self.network_class, "intent_capsule_ref": self.intent_capsule_ref,
            "synthetic_input_ref": self.synthetic_input_ref, "synthetic_input_digest": self.synthetic_input_digest,
            "success_criteria": list(self.success_criteria), "output_contract": dict(self.output_contract),
            "deadline": self.deadline, "timeout_seconds": self.timeout_seconds, "retry_policy": self.retry_policy,
            "reconciliation_policy": self.reconciliation_policy, "budget_authority": self.budget_authority,
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LiveDispatchEnvelope":
        keys = {"schema_version", "task_id", "dispatch_id", "attempt_id", "executor_id", "adapter_id", "capability_id", "capability_lease_ref", "workspace_ref", "workspace_mode", "permission_ceiling", "side_effect_class", "network_class", "intent_capsule_ref", "synthetic_input_ref", "synthetic_input_digest", "success_criteria", "output_contract", "deadline", "timeout_seconds", "retry_policy", "reconciliation_policy", "budget_authority", "provenance"}
        _strict(data, keys, "LiveDispatchEnvelope")
        values = dict(data)
        values["permission_ceiling"] = tuple(values["permission_ceiling"])
        values["success_criteria"] = tuple(values["success_criteria"])
        return cls(**values)


@dataclass(frozen=True)
class LiveCapabilityLease:
    schema_version: str
    lease_id: str
    executor_id: str
    executor_version: str
    observed_at: str
    expires_at: str
    ttl_seconds: float
    binary_digest: str
    interface_digest: str
    observed_capabilities: tuple[str, ...]
    forbidden_capabilities: tuple[str, ...]
    unknown_capabilities: tuple[str, ...]
    workspace_semantics: str
    approval_sandbox_semantics: str
    structured_output_semantics: str
    timeout_supported: bool
    cancel_supported: bool
    resume_supported: bool
    live_eligibility: str
    eligibility_blockers: tuple[str, ...]
    source: str
    lease_digest: str

    def __post_init__(self) -> None:
        if self.schema_version != LIVE_LEASE_SCHEMA:
            raise FederationContractError("live capability lease schema version mismatch")
        for field in ("lease_id", "executor_id", "executor_version", "observed_at", "expires_at", "workspace_semantics", "approval_sandbox_semantics", "structured_output_semantics", "source"):
            _text(getattr(self, field), f"live_lease.{field}")
        if not isinstance(self.ttl_seconds, (int, float)) or isinstance(self.ttl_seconds, bool) or self.ttl_seconds <= 0:
            raise FederationContractError("live_lease.ttl_seconds must be positive")
        object.__setattr__(self, "binary_digest", _digest(self.binary_digest, "live_lease.binary_digest"))
        object.__setattr__(self, "interface_digest", _digest(self.interface_digest, "live_lease.interface_digest"))
        object.__setattr__(self, "observed_capabilities", _capabilities(self.observed_capabilities, "live_lease.observed_capabilities"))
        object.__setattr__(self, "forbidden_capabilities", _capabilities(self.forbidden_capabilities, "live_lease.forbidden_capabilities"))
        object.__setattr__(self, "unknown_capabilities", _strings(self.unknown_capabilities, "live_lease.unknown_capabilities"))
        for field in ("timeout_supported", "cancel_supported", "resume_supported"):
            if not isinstance(getattr(self, field), bool):
                raise FederationContractError(f"live_lease.{field} must be boolean")
        object.__setattr__(self, "live_eligibility", _enum(self.live_eligibility, LIVE_ELIGIBILITY, "live_lease.live_eligibility"))
        object.__setattr__(self, "eligibility_blockers", _strings(self.eligibility_blockers, "live_lease.eligibility_blockers"))
        expected = canonical_digest(self._unsigned_dict())
        if _digest(self.lease_digest, "live_lease.lease_digest") != expected:
            raise FederationContractError("live_lease.lease_digest does not match its unsigned content")

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "lease_id": self.lease_id, "executor_id": self.executor_id,
            "executor_version": self.executor_version, "observed_at": self.observed_at, "expires_at": self.expires_at,
            "ttl_seconds": self.ttl_seconds, "binary_digest": self.binary_digest, "interface_digest": self.interface_digest,
            "observed_capabilities": list(self.observed_capabilities), "forbidden_capabilities": list(self.forbidden_capabilities),
            "unknown_capabilities": list(self.unknown_capabilities), "workspace_semantics": self.workspace_semantics,
            "approval_sandbox_semantics": self.approval_sandbox_semantics, "structured_output_semantics": self.structured_output_semantics,
            "timeout_supported": self.timeout_supported, "cancel_supported": self.cancel_supported, "resume_supported": self.resume_supported,
            "live_eligibility": self.live_eligibility, "eligibility_blockers": list(self.eligibility_blockers), "source": self.source,
        }

    def to_dict(self) -> dict[str, Any]:
        result = self._unsigned_dict()
        result["lease_digest"] = self.lease_digest
        return result

    @classmethod
    def build(cls, **kwargs: Any) -> "LiveCapabilityLease":
        values = dict(kwargs)
        values.setdefault("schema_version", LIVE_LEASE_SCHEMA)
        unsigned = dict(values)
        unsigned.pop("lease_digest", None)
        values["lease_digest"] = canonical_digest(unsigned)
        return cls(**values)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LiveCapabilityLease":
        keys = {"schema_version", "lease_id", "executor_id", "executor_version", "observed_at", "expires_at", "ttl_seconds", "binary_digest", "interface_digest", "observed_capabilities", "forbidden_capabilities", "unknown_capabilities", "workspace_semantics", "approval_sandbox_semantics", "structured_output_semantics", "timeout_supported", "cancel_supported", "resume_supported", "live_eligibility", "eligibility_blockers", "source", "lease_digest"}
        _strict(data, keys, "LiveCapabilityLease")
        values = dict(data)
        for field in ("observed_capabilities", "forbidden_capabilities", "unknown_capabilities", "eligibility_blockers"):
            values[field] = tuple(values[field])
        return cls(**values)


@dataclass(frozen=True)
class LiveExecutorReceipt:
    schema_version: str
    task_id: str
    dispatch_id: str
    attempt_id: str
    executor_id: str
    adapter_id: str
    state: str
    started_at: str
    ended_at: str
    exit_code: int | None
    timed_out: bool
    cancel_state: str
    event_count: int
    sanitized_event_summary: str
    response_digest: str | None
    structured_result: Mapping[str, Any] | None
    session_pointer: str | None
    side_effect_class: str
    side_effect_observation: str
    workspace_before_digest: str
    workspace_after_digest: str
    os_validation_status: str
    reconciliation_status: str
    claim_ceiling: str
    receipt_digest: str

    def __post_init__(self) -> None:
        if self.schema_version != LIVE_RECEIPT_SCHEMA:
            raise FederationContractError("live executor receipt schema version mismatch")
        for field in ("task_id", "dispatch_id", "attempt_id", "executor_id", "adapter_id", "started_at", "ended_at", "sanitized_event_summary", "claim_ceiling"):
            _text(getattr(self, field), f"live_receipt.{field}")
        object.__setattr__(self, "state", _enum(self.state, LIVE_DISPATCH_STATES, "live_receipt.state"))
        if self.exit_code is not None and (not isinstance(self.exit_code, int) or isinstance(self.exit_code, bool)):
            raise FederationContractError("live_receipt.exit_code must be null or an integer")
        if not isinstance(self.timed_out, bool):
            raise FederationContractError("live_receipt.timed_out must be boolean")
        object.__setattr__(self, "cancel_state", _enum(self.cancel_state, LIVE_CANCEL_STATES, "live_receipt.cancel_state"))
        if not isinstance(self.event_count, int) or isinstance(self.event_count, bool) or self.event_count < 0:
            raise FederationContractError("live_receipt.event_count must be non-negative")
        object.__setattr__(self, "response_digest", _optional_digest(self.response_digest, "live_receipt.response_digest"))
        if self.structured_result is not None:
            object.__setattr__(self, "structured_result", _public(self.structured_result, "live_receipt.structured_result"))
        if self.session_pointer is not None:
            pointer = _text(self.session_pointer, "live_receipt.session_pointer")
            if any(marker in pointer.casefold() for marker in ("prompt", "token", "secret", "reasoning")):
                raise FederationContractError("live_receipt.session_pointer must remain opaque")
            object.__setattr__(self, "session_pointer", pointer)
        object.__setattr__(self, "side_effect_class", _enum(self.side_effect_class, LIVE_SIDE_EFFECT_CLASSES, "live_receipt.side_effect_class"))
        object.__setattr__(self, "side_effect_observation", _enum(self.side_effect_observation, LIVE_SIDE_EFFECT_OBSERVATIONS, "live_receipt.side_effect_observation"))
        object.__setattr__(self, "workspace_before_digest", _digest(self.workspace_before_digest, "live_receipt.workspace_before_digest"))
        object.__setattr__(self, "workspace_after_digest", _digest(self.workspace_after_digest, "live_receipt.workspace_after_digest"))
        object.__setattr__(self, "os_validation_status", _enum(self.os_validation_status, LIVE_VALIDATION_STATUSES, "live_receipt.os_validation_status"))
        object.__setattr__(self, "reconciliation_status", _enum(self.reconciliation_status, LIVE_RECONCILIATION_STATUSES, "live_receipt.reconciliation_status"))
        expected = canonical_digest(self._unsigned_dict())
        if _digest(self.receipt_digest, "live_receipt.receipt_digest") != expected:
            raise FederationContractError("live_receipt.receipt_digest does not match its unsigned content")

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "task_id": self.task_id, "dispatch_id": self.dispatch_id,
            "attempt_id": self.attempt_id, "executor_id": self.executor_id, "adapter_id": self.adapter_id,
            "state": self.state, "started_at": self.started_at, "ended_at": self.ended_at, "exit_code": self.exit_code,
            "timed_out": self.timed_out, "cancel_state": self.cancel_state, "event_count": self.event_count,
            "sanitized_event_summary": self.sanitized_event_summary, "response_digest": self.response_digest,
            "structured_result": self.structured_result, "session_pointer": self.session_pointer,
            "side_effect_class": self.side_effect_class, "side_effect_observation": self.side_effect_observation,
            "workspace_before_digest": self.workspace_before_digest, "workspace_after_digest": self.workspace_after_digest,
            "os_validation_status": self.os_validation_status, "reconciliation_status": self.reconciliation_status,
            "claim_ceiling": self.claim_ceiling,
        }

    def to_dict(self) -> dict[str, Any]:
        result = self._unsigned_dict()
        result["receipt_digest"] = self.receipt_digest
        return result

    @classmethod
    def build(cls, **kwargs: Any) -> "LiveExecutorReceipt":
        values = dict(kwargs)
        values.setdefault("schema_version", LIVE_RECEIPT_SCHEMA)
        unsigned = dict(values)
        unsigned.pop("receipt_digest", None)
        values["receipt_digest"] = canonical_digest(unsigned)
        return cls(**values)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LiveExecutorReceipt":
        keys = {"schema_version", "task_id", "dispatch_id", "attempt_id", "executor_id", "adapter_id", "state", "started_at", "ended_at", "exit_code", "timed_out", "cancel_state", "event_count", "sanitized_event_summary", "response_digest", "structured_result", "session_pointer", "side_effect_class", "side_effect_observation", "workspace_before_digest", "workspace_after_digest", "os_validation_status", "reconciliation_status", "claim_ceiling", "receipt_digest"}
        _strict(data, keys, "LiveExecutorReceipt")
        return cls(**dict(data))


@dataclass(frozen=True)
class LiveTransitionRecord:
    dispatch_id: str
    from_state: str
    to_state: str
    reason: str
    observed_at: str

    def __post_init__(self) -> None:
        _text(self.dispatch_id, "live_transition.dispatch_id")
        object.__setattr__(self, "from_state", _enum(self.from_state, LIVE_DISPATCH_STATES, "live_transition.from_state"))
        object.__setattr__(self, "to_state", _enum(self.to_state, LIVE_DISPATCH_STATES, "live_transition.to_state"))
        _text(self.reason, "live_transition.reason")
        _text(self.observed_at, "live_transition.observed_at")

    def to_dict(self) -> dict[str, str]:
        return {"dispatch_id": self.dispatch_id, "from_state": self.from_state, "to_state": self.to_state, "reason": self.reason, "observed_at": self.observed_at}


class LiveTransitionError(FederationContractError):
    """Raised when a live dispatch attempts an unsafe lifecycle transition."""


class LiveDispatchStateMachine:
    """Small OS-owned state machine with explicit reconciliation stops."""

    def __init__(self, envelope: LiveDispatchEnvelope, *, observed_at: str) -> None:
        if not isinstance(envelope, LiveDispatchEnvelope):
            raise LiveTransitionError("state machine requires a LiveDispatchEnvelope")
        self.envelope = envelope
        self._state = "CREATED"
        self._history: list[LiveTransitionRecord] = []
        self._observed_at = _text(observed_at, "state_machine.observed_at")

    @property
    def state(self) -> str:
        return self._state

    @property
    def history(self) -> tuple[LiveTransitionRecord, ...]:
        return tuple(self._history)

    @property
    def terminal(self) -> bool:
        return self._state in LIVE_TERMINAL_STATES and self._state != "REQUIRES_RECONCILIATION"

    @property
    def retry_allowed(self) -> bool:
        return self._state == "TIMED_OUT_KNOWN_NO_EFFECT"

    def transition(self, to_state: str, reason: str, *, observed_at: str | None = None) -> LiveTransitionRecord:
        to_state = _enum(to_state, LIVE_DISPATCH_STATES, "state_machine.to_state")
        if to_state not in LIVE_TRANSITIONS.get(self._state, frozenset()):
            raise LiveTransitionError(f"illegal live transition {self._state} -> {to_state}")
        if to_state == "COMPLETED_VALIDATED" and self._state != "VALIDATING":
            raise LiveTransitionError("validated completion requires an OS VALIDATING state")
        record = LiveTransitionRecord(self.envelope.dispatch_id, self._state, to_state, reason, observed_at or self._observed_at)
        self._history.append(record)
        self._state = to_state
        return record

    def admit(self, *, allowed: bool, reason: str, cost_authorized: bool = True) -> LiveTransitionRecord:
        if not allowed:
            return self.transition("REJECTED_POLICY", reason)
        if not cost_authorized:
            return self.transition("REJECTED_COST_AUTHORITY", reason)
        return self.transition("ADMITTED", reason)

    def begin_dispatch(self) -> LiveTransitionRecord:
        return self.transition("DISPATCHING", "OS admission passed; bounded dispatch is starting")

    def mark_in_flight(self) -> LiveTransitionRecord:
        return self.transition("IN_FLIGHT", "external process started")

    def record_executor_return(self, *, parsed: bool, returncode: int | None) -> LiveTransitionRecord:
        if not parsed:
            return self.transition("MALFORMED_RESULT", "public result could not be parsed")
        if returncode is None:
            return self.transition("TIMED_OUT_EFFECT_UNKNOWN", "process outcome is unknown")
        return self.transition("RETURNED_UNVALIDATED", f"executor returned exit_code={returncode}; OS validation is pending")

    def mark_timeout(self, *, effect_known_no_effect: bool) -> LiveTransitionRecord:
        return self.transition(
            "TIMED_OUT_KNOWN_NO_EFFECT" if effect_known_no_effect else "TIMED_OUT_EFFECT_UNKNOWN",
            "bounded timeout observed; no automatic completion or replay",
        )

    def request_cancel(self) -> LiveTransitionRecord:
        return self.transition("CANCEL_REQUESTED", "OS cancellation requested; external effect is not inferred undone")

    def confirm_cancel(self, *, effect_known_no_effect: bool) -> LiveTransitionRecord:
        if effect_known_no_effect:
            return self.transition("CANCEL_CONFIRMED", "cancel confirmed with known no external effect")
        return self.transition("REQUIRES_RECONCILIATION", "cancel outcome does not prove external effect absence")

    def start_validation(self) -> LiveTransitionRecord:
        return self.transition("VALIDATING", "independent OS validator started")

    def finish_validation(self, *, passed: bool, workspace_unchanged: bool, no_forbidden_effect: bool) -> LiveTransitionRecord:
        if self._state != "VALIDATING":
            raise LiveTransitionError("validation can finish only from VALIDATING")
        if passed and workspace_unchanged and no_forbidden_effect:
            return self.transition("COMPLETED_VALIDATED", "independent OS validation passed")
        return self.transition("VALIDATION_FAILED", "independent OS validation did not establish bounded completion")

    def reconcile(self, *, no_external_effect: bool) -> LiveTransitionRecord:
        if self._state != "REQUIRES_RECONCILIATION":
            raise LiveTransitionError("reconciliation can start only from REQUIRES_RECONCILIATION")
        if not no_external_effect:
            return self.transition("VALIDATION_FAILED", "reconciliation did not prove no external effect")
        return self.transition("VALIDATING", "reconciliation proved no external effect; validation may proceed")

    def new_lineage_attempt(self, attempt_id: str) -> str:
        if not self.retry_allowed:
            raise LiveTransitionError("retry is allowed only after a timeout with known no effect")
        attempt_id = _text(attempt_id, "state_machine.new_attempt_id")
        if attempt_id == self.envelope.attempt_id:
            raise LiveTransitionError("retry attempt must have a new lineage id")
        return attempt_id


__all__ = [
    "LIVE_BUDGET_AUTHORITIES", "LIVE_DISPATCH_SCHEMA", "LIVE_DISPATCH_STATES", "LIVE_ELIGIBILITY",
    "LIVE_LEASE_SCHEMA", "LIVE_NETWORK_CLASSES", "LIVE_RECEIPT_SCHEMA", "LIVE_RECONCILIATION_POLICIES",
    "LIVE_SIDE_EFFECT_CLASSES", "LIVE_TRANSITIONS", "LiveCapabilityLease", "LiveDispatchEnvelope",
    "LiveDispatchStateMachine", "LiveExecutorReceipt", "LiveTransitionError", "LiveTransitionRecord",
]
