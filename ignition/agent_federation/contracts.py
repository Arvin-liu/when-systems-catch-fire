"""Vendor-neutral External Agent Federation R1 records.

This module is a boundary contract, not an agent runtime.  External session
references are pointers only; canonical task state, permissions, validation
and receipts remain owned by the Ignition OS.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Protocol, Sequence


class FederationContractError(ValueError):
    """Raised when a federation record is incomplete or unsafe."""


TASK_GRANULARITIES = frozenset({"ACTION", "SUBTASK", "EPISODE"})
HEALTH_STATES = frozenset({"HEALTHY", "DEGRADED", "UNAVAILABLE", "UNKNOWN"})
AVAILABILITY_STATES = frozenset({"AVAILABLE", "UNAVAILABLE", "UNKNOWN"})
TERMINAL_STATES = frozenset({
    "COMPLETED_VALIDATED",
    "FAILED_VALIDATION",
    "FAILED",
    "BLOCKED_WITH_EVIDENCE",
    "WAITING_FOR_APPROVAL",
    "REQUIRES_RECONCILIATION",
    "CANCELLED",
})
HIDDEN_FIELD_MARKERS = frozenset({"prompt", "system_prompt", "cot", "chain_of_thought", "thoughts", "reasoning_tokens", "token", "api_key", "cookie", "authorization"})


def _strict(data: Mapping[str, Any], keys: set[str], name: str) -> None:
    if not isinstance(data, Mapping) or set(data) != keys:
        actual = sorted(data) if isinstance(data, Mapping) else type(data).__name__
        raise FederationContractError(f"{name} keys must be exactly {sorted(keys)}; got {actual}")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FederationContractError(f"{field} must be a non-empty string")
    return value


def _enum(value: Any, allowed: set[str] | frozenset[str], field: str) -> str:
    value = _text(value, field)
    if value not in allowed:
        raise FederationContractError(f"{field} is not supported: {value}")
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


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise FederationContractError(f"{field} must be an object")
    result = dict(value)
    forbidden = sorted(key for key in result if str(key).casefold() in HIDDEN_FIELD_MARKERS)
    if forbidden:
        raise FederationContractError(f"{field} contains prohibited hidden/secret fields: {forbidden}")
    return result


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise FederationContractError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _optional_fraction(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
        raise FederationContractError(f"{field} must be null or a fraction between 0 and 1")
    return float(value)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExecutorHealth:
    status: str
    checked_at: str
    reason: str
    latency_ms: float | None = None
    capability_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _enum(self.status, HEALTH_STATES, "health.status"))
        _text(self.checked_at, "health.checked_at")
        _text(self.reason, "health.reason")
        if self.latency_ms is not None and (not isinstance(self.latency_ms, (int, float)) or isinstance(self.latency_ms, bool) or self.latency_ms < 0):
            raise FederationContractError("health.latency_ms must be null or non-negative")
        if self.capability_digest is not None:
            _sha256(self.capability_digest, "health.capability_digest")

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "checked_at": self.checked_at, "reason": self.reason, "latency_ms": self.latency_ms, "capability_digest": self.capability_digest}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutorHealth":
        _strict(data, {"status", "checked_at", "reason", "latency_ms", "capability_digest"}, "ExecutorHealth")
        return cls(**data)


@dataclass(frozen=True)
class ExecutorDescriptor:
    executor_id: str
    family: str
    version: str
    transport_kind: tuple[str, ...]
    availability: str
    health: ExecutorHealth
    capability_tokens: tuple[str, ...]
    supported_task_granularities: tuple[str, ...]
    workspace_semantics: str
    permission_control_semantics: str
    structured_output_support: bool
    progress_support: bool
    cancel_support: bool
    native_resume_support: bool
    external_session_refs: tuple[str, ...]
    network_semantics: str
    max_task_duration_seconds: float | None
    adapter_version: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("executor_id", "family", "version", "workspace_semantics", "permission_control_semantics", "network_semantics", "adapter_version"):
            _text(getattr(self, field), f"descriptor.{field}")
        object.__setattr__(self, "transport_kind", _strings(self.transport_kind, "descriptor.transport_kind", nonempty=True))
        object.__setattr__(self, "availability", _enum(self.availability, AVAILABILITY_STATES, "descriptor.availability"))
        if not isinstance(self.health, ExecutorHealth):
            raise FederationContractError("descriptor.health must be ExecutorHealth")
        object.__setattr__(self, "capability_tokens", _strings(self.capability_tokens, "descriptor.capability_tokens"))
        granularities = _strings(self.supported_task_granularities, "descriptor.supported_task_granularities", nonempty=True)
        if not set(granularities) <= TASK_GRANULARITIES:
            raise FederationContractError("descriptor.supported_task_granularities contains an unknown value")
        object.__setattr__(self, "supported_task_granularities", granularities)
        for field in ("structured_output_support", "progress_support", "cancel_support", "native_resume_support"):
            if not isinstance(getattr(self, field), bool):
                raise FederationContractError(f"descriptor.{field} must be boolean")
        object.__setattr__(self, "external_session_refs", _strings(self.external_session_refs, "descriptor.external_session_refs"))
        if self.max_task_duration_seconds is not None and (not isinstance(self.max_task_duration_seconds, (int, float)) or isinstance(self.max_task_duration_seconds, bool) or self.max_task_duration_seconds <= 0):
            raise FederationContractError("descriptor.max_task_duration_seconds must be null or positive")
        object.__setattr__(self, "limitations", _strings(self.limitations, "descriptor.limitations"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id, "family": self.family, "version": self.version,
            "transport_kind": list(self.transport_kind), "availability": self.availability,
            "health": self.health.to_dict(), "capability_tokens": list(self.capability_tokens),
            "supported_task_granularities": list(self.supported_task_granularities),
            "workspace_semantics": self.workspace_semantics,
            "permission_control_semantics": self.permission_control_semantics,
            "structured_output_support": self.structured_output_support,
            "progress_support": self.progress_support, "cancel_support": self.cancel_support,
            "native_resume_support": self.native_resume_support,
            "external_session_refs": list(self.external_session_refs),
            "network_semantics": self.network_semantics,
            "max_task_duration_seconds": self.max_task_duration_seconds,
            "adapter_version": self.adapter_version, "limitations": list(self.limitations),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutorDescriptor":
        keys = {"executor_id", "family", "version", "transport_kind", "availability", "health", "capability_tokens", "supported_task_granularities", "workspace_semantics", "permission_control_semantics", "structured_output_support", "progress_support", "cancel_support", "native_resume_support", "external_session_refs", "network_semantics", "max_task_duration_seconds", "adapter_version", "limitations"}
        _strict(data, keys, "ExecutorDescriptor")
        values = dict(data)
        values["health"] = ExecutorHealth.from_dict(values["health"])
        return cls(**values)


@dataclass(frozen=True)
class ApprovalPolicy:
    mode: str
    external_approval_allowed: bool
    capability_ceiling: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", _enum(self.mode, {"DENY", "AUTO", "REQUIRE_OWNER", "DELEGATED"}, "approval_policy.mode"))
        if not isinstance(self.external_approval_allowed, bool):
            raise FederationContractError("approval_policy.external_approval_allowed must be boolean")
        object.__setattr__(self, "capability_ceiling", _strings(self.capability_ceiling, "approval_policy.capability_ceiling"))

    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode, "external_approval_allowed": self.external_approval_allowed, "capability_ceiling": list(self.capability_ceiling)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ApprovalPolicy":
        _strict(data, {"mode", "external_approval_allowed", "capability_ceiling"}, "ApprovalPolicy")
        return cls(**data)


@dataclass(frozen=True)
class BudgetContract:
    max_seconds: float
    max_output_bytes: int
    max_actions: int

    def __post_init__(self) -> None:
        if not isinstance(self.max_seconds, (int, float)) or isinstance(self.max_seconds, bool) or self.max_seconds <= 0:
            raise FederationContractError("budget.max_seconds must be positive")
        if not isinstance(self.max_output_bytes, int) or isinstance(self.max_output_bytes, bool) or self.max_output_bytes <= 0:
            raise FederationContractError("budget.max_output_bytes must be positive")
        if not isinstance(self.max_actions, int) or isinstance(self.max_actions, bool) or self.max_actions <= 0:
            raise FederationContractError("budget.max_actions must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {"max_seconds": self.max_seconds, "max_output_bytes": self.max_output_bytes, "max_actions": self.max_actions}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BudgetContract":
        _strict(data, {"max_seconds", "max_output_bytes", "max_actions"}, "BudgetContract")
        return cls(**data)


@dataclass(frozen=True)
class ValidationContract:
    contract_id: str
    required_checks: tuple[str, ...]
    validator_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.contract_id, "validation_contract.contract_id")
        object.__setattr__(self, "required_checks", _strings(self.required_checks, "validation_contract.required_checks", nonempty=True))
        object.__setattr__(self, "validator_refs", _strings(self.validator_refs, "validation_contract.validator_refs"))

    def to_dict(self) -> dict[str, Any]:
        return {"contract_id": self.contract_id, "required_checks": list(self.required_checks), "validator_refs": list(self.validator_refs)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ValidationContract":
        _strict(data, {"contract_id", "required_checks", "validator_refs"}, "ValidationContract")
        return cls(**data)


@dataclass(frozen=True)
class OutputContract:
    format: str
    required_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.format, "output_contract.format")
        object.__setattr__(self, "required_fields", _strings(self.required_fields, "output_contract.required_fields"))

    def to_dict(self) -> dict[str, Any]:
        return {"format": self.format, "required_fields": list(self.required_fields)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OutputContract":
        _strict(data, {"format", "required_fields"}, "OutputContract")
        return cls(**data)


@dataclass(frozen=True)
class HandoffPolicy:
    enabled: bool
    allowed_executor_ids: tuple[str, ...]
    requires_reconciliation: bool

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool) or not isinstance(self.requires_reconciliation, bool):
            raise FederationContractError("handoff policy booleans are required")
        object.__setattr__(self, "allowed_executor_ids", _strings(self.allowed_executor_ids, "handoff_policy.allowed_executor_ids"))

    def to_dict(self) -> dict[str, Any]:
        return {"enabled": self.enabled, "allowed_executor_ids": list(self.allowed_executor_ids), "requires_reconciliation": self.requires_reconciliation}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HandoffPolicy":
        _strict(data, {"enabled", "allowed_executor_ids", "requires_reconciliation"}, "HandoffPolicy")
        return cls(**data)


@dataclass(frozen=True)
class ExternalSessionRef:
    executor_id: str
    session_id: str
    kind: str
    created_at: str
    pointer_only: bool = True

    def __post_init__(self) -> None:
        for field in ("executor_id", "session_id", "kind", "created_at"):
            _text(getattr(self, field), f"session_ref.{field}")
        if self.session_id.startswith("secret:"):
            raise FederationContractError("session_ref.session_id must not contain secret material")
        if self.pointer_only is not True:
            raise FederationContractError("external session refs are always pointer_only")

    def to_dict(self) -> dict[str, Any]:
        return {"executor_id": self.executor_id, "session_id": self.session_id, "kind": self.kind, "created_at": self.created_at, "pointer_only": self.pointer_only}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExternalSessionRef":
        _strict(data, {"executor_id", "session_id", "kind", "created_at", "pointer_only"}, "ExternalSessionRef")
        return cls(**data)


@dataclass(frozen=True)
class FederatedTaskEnvelope:
    federation_task_id: str
    owner_ref: str
    profile_ref: str
    goal: str
    success_criteria: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    allowed_effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    workspace_scope: tuple[str, ...]
    approval_policy: ApprovalPolicy
    context_capsule_refs: tuple[str, ...]
    pack_refs: tuple[str, ...]
    validation_contract: ValidationContract
    output_contract: OutputContract
    budget: BudgetContract
    idempotency_key: str
    privacy_class: str
    handoff_policy: HandoffPolicy
    reason_summary: str

    def __post_init__(self) -> None:
        for field in ("federation_task_id", "owner_ref", "profile_ref", "goal", "idempotency_key", "privacy_class", "reason_summary"):
            _text(getattr(self, field), f"envelope.{field}")
        object.__setattr__(self, "success_criteria", _strings(self.success_criteria, "envelope.success_criteria", nonempty=True))
        object.__setattr__(self, "required_capabilities", _strings(self.required_capabilities, "envelope.required_capabilities", nonempty=True))
        object.__setattr__(self, "allowed_effects", _strings(self.allowed_effects, "envelope.allowed_effects"))
        object.__setattr__(self, "forbidden_effects", _strings(self.forbidden_effects, "envelope.forbidden_effects"))
        object.__setattr__(self, "workspace_scope", _strings(self.workspace_scope, "envelope.workspace_scope", nonempty=True))
        if not isinstance(self.approval_policy, ApprovalPolicy) or not isinstance(self.validation_contract, ValidationContract) or not isinstance(self.output_contract, OutputContract) or not isinstance(self.budget, BudgetContract) or not isinstance(self.handoff_policy, HandoffPolicy):
            raise FederationContractError("envelope nested contracts have invalid types")
        object.__setattr__(self, "context_capsule_refs", _strings(self.context_capsule_refs, "envelope.context_capsule_refs"))
        object.__setattr__(self, "pack_refs", _strings(self.pack_refs, "envelope.pack_refs"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "federation_task_id": self.federation_task_id, "owner_ref": self.owner_ref, "profile_ref": self.profile_ref,
            "goal": self.goal, "success_criteria": list(self.success_criteria),
            "required_capabilities": list(self.required_capabilities), "allowed_effects": list(self.allowed_effects),
            "forbidden_effects": list(self.forbidden_effects), "workspace_scope": list(self.workspace_scope),
            "approval_policy": self.approval_policy.to_dict(), "context_capsule_refs": list(self.context_capsule_refs),
            "pack_refs": list(self.pack_refs), "validation_contract": self.validation_contract.to_dict(),
            "output_contract": self.output_contract.to_dict(), "budget": self.budget.to_dict(),
            "idempotency_key": self.idempotency_key, "privacy_class": self.privacy_class,
            "handoff_policy": self.handoff_policy.to_dict(), "reason_summary": self.reason_summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FederatedTaskEnvelope":
        keys = {"federation_task_id", "owner_ref", "profile_ref", "goal", "success_criteria", "required_capabilities", "allowed_effects", "forbidden_effects", "workspace_scope", "approval_policy", "context_capsule_refs", "pack_refs", "validation_contract", "output_contract", "budget", "idempotency_key", "privacy_class", "handoff_policy", "reason_summary"}
        _strict(data, keys, "FederatedTaskEnvelope")
        values = dict(data)
        values["approval_policy"] = ApprovalPolicy.from_dict(values["approval_policy"])
        values["validation_contract"] = ValidationContract.from_dict(values["validation_contract"])
        values["output_contract"] = OutputContract.from_dict(values["output_contract"])
        values["budget"] = BudgetContract.from_dict(values["budget"])
        values["handoff_policy"] = HandoffPolicy.from_dict(values["handoff_policy"])
        return cls(**values)


@dataclass(frozen=True)
class FederatedProgressEvent:
    federation_task_id: str
    executor_id: str
    sequence: int
    state: str
    public_summary: str
    refs: tuple[str, ...]
    progress_fraction: float | None = None

    def __post_init__(self) -> None:
        _text(self.federation_task_id, "progress.federation_task_id")
        _text(self.executor_id, "progress.executor_id")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 0:
            raise FederationContractError("progress.sequence must be a non-negative integer")
        _text(self.state, "progress.state")
        _text(self.public_summary, "progress.public_summary")
        object.__setattr__(self, "refs", _strings(self.refs, "progress.refs"))
        object.__setattr__(self, "progress_fraction", _optional_fraction(self.progress_fraction, "progress.progress_fraction"))

    def to_dict(self) -> dict[str, Any]:
        return {"federation_task_id": self.federation_task_id, "executor_id": self.executor_id, "sequence": self.sequence, "state": self.state, "public_summary": self.public_summary, "refs": list(self.refs), "progress_fraction": self.progress_fraction}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FederatedProgressEvent":
        _strict(data, {"federation_task_id", "executor_id", "sequence", "state", "public_summary", "refs", "progress_fraction"}, "FederatedProgressEvent")
        return cls(**data)


@dataclass(frozen=True)
class ArtifactRef:
    ref: str
    sha256: str
    kind: str

    def __post_init__(self) -> None:
        _text(self.ref, "artifact.ref")
        _sha256(self.sha256, "artifact.sha256")
        _text(self.kind, "artifact.kind")

    def to_dict(self) -> dict[str, str]:
        return {"ref": self.ref, "sha256": self.sha256, "kind": self.kind}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ArtifactRef":
        _strict(data, {"ref", "sha256", "kind"}, "ArtifactRef")
        return cls(**data)


@dataclass(frozen=True)
class HandoffEligibility:
    eligible: bool
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.eligible, bool):
            raise FederationContractError("handoff_eligibility.eligible must be boolean")
        _text(self.reason, "handoff_eligibility.reason")

    def to_dict(self) -> dict[str, Any]:
        return {"eligible": self.eligible, "reason": self.reason}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HandoffEligibility":
        _strict(data, {"eligible", "reason"}, "HandoffEligibility")
        return cls(**data)


def _telemetry(value: Mapping[str, Any]) -> dict[str, Any]:
    result = _mapping(value, "executor_telemetry")
    for key, item in result.items():
        _text(str(key), "executor_telemetry.key")
        if isinstance(item, (dict, list, tuple)):
            raise FederationContractError("executor_telemetry must remain flat and public")
        if str(key).casefold() in HIDDEN_FIELD_MARKERS:
            raise FederationContractError("executor_telemetry contains hidden/secret field")
    return result


@dataclass(frozen=True)
class FederatedResultReceipt:
    federation_task_id: str
    executor_id: str
    terminal_state: str
    claimed_actions: tuple[str, ...]
    artifact_refs: tuple[ArtifactRef, ...]
    validation_refs: tuple[str, ...]
    external_session_ref: ExternalSessionRef | None
    executor_telemetry: Mapping[str, Any]
    unresolveds: tuple[str, ...]
    handoff_eligibility: HandoffEligibility
    receipt_digest: str

    def __post_init__(self) -> None:
        _text(self.federation_task_id, "receipt.federation_task_id")
        _text(self.executor_id, "receipt.executor_id")
        object.__setattr__(self, "terminal_state", _enum(self.terminal_state, TERMINAL_STATES, "receipt.terminal_state"))
        object.__setattr__(self, "claimed_actions", _strings(self.claimed_actions, "receipt.claimed_actions"))
        if not isinstance(self.artifact_refs, (list, tuple)) or any(not isinstance(item, ArtifactRef) for item in self.artifact_refs):
            raise FederationContractError("receipt.artifact_refs must contain ArtifactRef values")
        if len({item.ref for item in self.artifact_refs}) != len(self.artifact_refs):
            raise FederationContractError("receipt.artifact_refs must not duplicate refs")
        object.__setattr__(self, "validation_refs", _strings(self.validation_refs, "receipt.validation_refs"))
        if self.external_session_ref is not None and not isinstance(self.external_session_ref, ExternalSessionRef):
            raise FederationContractError("receipt.external_session_ref must be ExternalSessionRef or null")
        object.__setattr__(self, "executor_telemetry", _telemetry(self.executor_telemetry))
        object.__setattr__(self, "unresolveds", _strings(self.unresolveds, "receipt.unresolveds"))
        if not isinstance(self.handoff_eligibility, HandoffEligibility):
            raise FederationContractError("receipt.handoff_eligibility must be HandoffEligibility")
        digest = _sha256(self.receipt_digest, "receipt.receipt_digest")
        expected = canonical_digest(self._unsigned_dict())
        if digest != expected:
            raise FederationContractError("receipt_digest does not match the canonical unsigned receipt")

    def _unsigned_dict(self) -> dict[str, Any]:
        return {
            "federation_task_id": self.federation_task_id, "executor_id": self.executor_id,
            "terminal_state": self.terminal_state, "claimed_actions": list(self.claimed_actions),
            "artifact_refs": [item.to_dict() for item in self.artifact_refs], "validation_refs": list(self.validation_refs),
            "external_session_ref": self.external_session_ref.to_dict() if self.external_session_ref else None,
            "executor_telemetry": dict(self.executor_telemetry), "unresolveds": list(self.unresolveds),
            "handoff_eligibility": self.handoff_eligibility.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        result = self._unsigned_dict()
        result["receipt_digest"] = self.receipt_digest
        return result

    @classmethod
    def build(cls, *, federation_task_id: str, executor_id: str, terminal_state: str, claimed_actions: Sequence[str], artifact_refs: Sequence[ArtifactRef], validation_refs: Sequence[str], external_session_ref: ExternalSessionRef | None, executor_telemetry: Mapping[str, Any], unresolveds: Sequence[str], handoff_eligibility: HandoffEligibility) -> "FederatedResultReceipt":
        unsigned = {
            "federation_task_id": federation_task_id, "executor_id": executor_id,
            "terminal_state": terminal_state, "claimed_actions": list(claimed_actions),
            "artifact_refs": [item.to_dict() for item in artifact_refs], "validation_refs": list(validation_refs),
            "external_session_ref": external_session_ref.to_dict() if external_session_ref else None,
            "executor_telemetry": dict(executor_telemetry), "unresolveds": list(unresolveds),
            "handoff_eligibility": handoff_eligibility.to_dict(),
        }
        return cls(
            federation_task_id=federation_task_id,
            executor_id=executor_id,
            terminal_state=terminal_state,
            claimed_actions=tuple(claimed_actions),
            artifact_refs=tuple(artifact_refs),
            validation_refs=tuple(validation_refs),
            external_session_ref=external_session_ref,
            executor_telemetry=dict(executor_telemetry),
            unresolveds=tuple(unresolveds),
            handoff_eligibility=handoff_eligibility,
            receipt_digest=canonical_digest(unsigned),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FederatedResultReceipt":
        keys = {"federation_task_id", "executor_id", "terminal_state", "claimed_actions", "artifact_refs", "validation_refs", "external_session_ref", "executor_telemetry", "unresolveds", "handoff_eligibility", "receipt_digest"}
        _strict(data, keys, "FederatedResultReceipt")
        values = dict(data)
        values["artifact_refs"] = tuple(ArtifactRef.from_dict(item) for item in values["artifact_refs"])
        values["external_session_ref"] = ExternalSessionRef.from_dict(values["external_session_ref"]) if values["external_session_ref"] is not None else None
        values["handoff_eligibility"] = HandoffEligibility.from_dict(values["handoff_eligibility"])
        return cls(**values)


@dataclass(frozen=True)
class FederatedHandoffBundle:
    handoff_id: str
    federation_task_id: str
    source_executor_id: str
    goal: str
    validated_completed_work: tuple[str, ...]
    pending_work: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]
    workspace_refs: tuple[str, ...]
    artifact_refs: tuple[ArtifactRef, ...]
    acceptance_criteria: tuple[str, ...]
    operational_memory_capsule_refs: tuple[str, ...]
    external_session_refs: tuple[ExternalSessionRef, ...]
    unresolveds: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("handoff_id", "federation_task_id", "source_executor_id", "goal"):
            _text(getattr(self, field), f"handoff.{field}")
        for field in ("validated_completed_work", "pending_work", "allowed_capabilities", "workspace_refs", "acceptance_criteria", "operational_memory_capsule_refs", "unresolveds"):
            object.__setattr__(self, field, _strings(getattr(self, field), f"handoff.{field}"))
        if not isinstance(self.artifact_refs, (list, tuple)) or any(not isinstance(item, ArtifactRef) for item in self.artifact_refs):
            raise FederationContractError("handoff.artifact_refs must contain ArtifactRef values")
        if not isinstance(self.external_session_refs, (list, tuple)) or any(not isinstance(item, ExternalSessionRef) for item in self.external_session_refs):
            raise FederationContractError("handoff.external_session_refs must contain pointer refs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id, "federation_task_id": self.federation_task_id,
            "source_executor_id": self.source_executor_id, "goal": self.goal,
            "validated_completed_work": list(self.validated_completed_work), "pending_work": list(self.pending_work),
            "allowed_capabilities": list(self.allowed_capabilities), "workspace_refs": list(self.workspace_refs),
            "artifact_refs": [item.to_dict() for item in self.artifact_refs],
            "acceptance_criteria": list(self.acceptance_criteria),
            "operational_memory_capsule_refs": list(self.operational_memory_capsule_refs),
            "external_session_refs": [item.to_dict() for item in self.external_session_refs],
            "unresolveds": list(self.unresolveds),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FederatedHandoffBundle":
        keys = {"handoff_id", "federation_task_id", "source_executor_id", "goal", "validated_completed_work", "pending_work", "allowed_capabilities", "workspace_refs", "artifact_refs", "acceptance_criteria", "operational_memory_capsule_refs", "external_session_refs", "unresolveds"}
        _strict(data, keys, "FederatedHandoffBundle")
        values = dict(data)
        values["artifact_refs"] = tuple(ArtifactRef.from_dict(item) for item in values["artifact_refs"])
        values["external_session_refs"] = tuple(ExternalSessionRef.from_dict(item) for item in values["external_session_refs"])
        return cls(**values)


class UnsupportedExecutorOperation(FederationContractError):
    """An adapter does not claim an optional lifecycle operation."""


class FederatedExecutor(Protocol):
    """The narrow adapter boundary; no internal agent runtime is prescribed."""

    def probe(self) -> ExecutorHealth: ...

    def describe(self) -> ExecutorDescriptor: ...

    def dispatch(self, envelope: FederatedTaskEnvelope) -> FederatedProgressEvent: ...

    def status(self, federation_task_id: str) -> FederatedProgressEvent: ...

    def cancel(self, federation_task_id: str) -> FederatedProgressEvent: ...

    def resume(self, bundle: FederatedHandoffBundle) -> FederatedProgressEvent: ...
