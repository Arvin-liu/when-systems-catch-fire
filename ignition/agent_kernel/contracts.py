"""Small, provider-neutral contracts for the Ignition Generic Kernel R0.

The kernel persists structured decisions and public summaries.  It does not
persist private model reasoning, infer facts, or grant authority to an
executor.  All constructors and boundary checks fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatchcase
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


class KernelValidationError(ValueError):
    """Raised when a kernel record or boundary check is invalid."""


class Phase(str, Enum):
    OBSERVE = "OBSERVE"
    FRAME = "FRAME"
    PLAN = "PLAN"
    AUTHORIZE = "AUTHORIZE"
    ACT = "ACT"
    VALIDATE = "VALIDATE"
    REMEMBER = "REMEMBER"
    CONTINUE = "CONTINUE"
    STOP = "STOP"


class StopState(str, Enum):
    COMPLETED_VALIDATED = "COMPLETED_VALIDATED"
    BLOCKED_WITH_EVIDENCE = "BLOCKED_WITH_EVIDENCE"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    FAILED_VALIDATION = "FAILED_VALIDATION"
    ABORTED_BY_OWNER = "ABORTED_BY_OWNER"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    CHECKPOINTED_RESUMABLE = "CHECKPOINTED_RESUMABLE"


class AuthorizationStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL"


ALLOWED_PHASES = tuple(item.value for item in Phase)
ALLOWED_STOP_STATES = tuple(item.value for item in StopState)
KERNEL_NON_ESCALATION = "KERNEL_NON_ESCALATION"
KERNEL_FORBIDDEN_AUTHORITY_UPGRADES = frozenset(
    {
        "agent_lifecycle",
        "executor_selection",
        "generic_permission",
        "checkpoint_resume",
        "owner_acceptance",
        "kernel_definition",
    }
)

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")
_HIDDEN_REASON_MARKERS = ("chain-of-thought", "hidden reasoning", "private model reasoning")


def canonical_json(value: Any) -> str:
    """Return deterministic JSON for hashes and receipts."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise KernelValidationError(f"{field} must be a non-empty string")
    if "\x00" in value:
        raise KernelValidationError(f"{field} contains a NUL")
    return value


def _id(value: Any, field: str) -> str:
    value = _string(value, field)
    if not _ID_PATTERN.fullmatch(value):
        raise KernelValidationError(f"{field} has an invalid identifier")
    return value


def _summary(value: Any, field: str = "summary") -> str:
    value = _string(value, field)
    lowered = value.casefold()
    if any(marker in lowered for marker in _HIDDEN_REASON_MARKERS):
        raise KernelValidationError(f"{field} must be a public structured summary")
    return value


def _tuple_strings(values: Any, field: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise KernelValidationError(f"{field} must be an array of strings")
    result = tuple(_string(item, f"{field}[]") for item in values)
    if len(result) != len(set(result)):
        raise KernelValidationError(f"{field} must not contain duplicates")
    return result


def normalize_relative_paths(values: Any, field: str) -> tuple[str, ...]:
    """Validate portable relative path patterns used by capability scopes."""

    paths = _tuple_strings(values, field)
    normalized: list[str] = []
    for path in paths:
        if path.startswith("/") or "\\" in path or path.startswith("file:"):
            raise KernelValidationError(f"{field} contains a non-portable path: {path}")
        parts = path.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise KernelValidationError(f"{field} contains a non-canonical path: {path}")
        normalized.append(path)
    return tuple(normalized)


def _strict_keys(data: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise KernelValidationError(f"{name} has unknown fields: {unknown}")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class ObjectRef:
    ref_id: str
    object_type: str
    version: str
    created_by: str

    def __post_init__(self) -> None:
        _id(self.ref_id, "ref_id")
        _string(self.object_type, "object_type")
        _string(self.version, "version")
        _id(self.created_by, "created_by")

    def to_dict(self) -> dict[str, str]:
        return {
            "ref_id": self.ref_id,
            "object_type": self.object_type,
            "version": self.version,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ObjectRef":
        _strict_keys(data, {"ref_id", "object_type", "version", "created_by"}, "ObjectRef")
        return cls(**data)


@dataclass(frozen=True)
class ProvenanceRef:
    source_ref: str
    source_sha256: str | None = None
    relation: str = "observed_from"

    def __post_init__(self) -> None:
        _string(self.source_ref, "source_ref")
        if self.source_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise KernelValidationError("source_sha256 must be a lowercase SHA-256 digest")
        _string(self.relation, "relation")

    def to_dict(self) -> dict[str, str]:
        result = {"source_ref": self.source_ref, "relation": self.relation}
        if self.source_sha256 is not None:
            result["source_sha256"] = self.source_sha256
        return result


@dataclass(frozen=True)
class CapabilityScope:
    scope_id: str
    allowed_reads: tuple[str, ...] = ()
    allowed_writes: tuple[str, ...] = ()
    allowed_commands: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    network_allowed: bool = False
    max_actions: int = 0
    max_seconds: int | None = None
    require_human_approval: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _id(self.scope_id, "scope_id")
        object.__setattr__(self, "allowed_reads", normalize_relative_paths(self.allowed_reads, "allowed_reads"))
        object.__setattr__(self, "allowed_writes", normalize_relative_paths(self.allowed_writes, "allowed_writes"))
        object.__setattr__(self, "allowed_commands", _tuple_strings(self.allowed_commands, "allowed_commands"))
        object.__setattr__(self, "allowed_tools", _tuple_strings(self.allowed_tools, "allowed_tools"))
        object.__setattr__(self, "require_human_approval", _tuple_strings(self.require_human_approval, "require_human_approval"))
        if not isinstance(self.network_allowed, bool):
            raise KernelValidationError("network_allowed must be boolean")
        if not isinstance(self.max_actions, int) or self.max_actions < 0:
            raise KernelValidationError("max_actions must be a non-negative integer")
        if self.max_seconds is not None and (not isinstance(self.max_seconds, int) or self.max_seconds < 0):
            raise KernelValidationError("max_seconds must be null or a non-negative integer")

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "allowed_reads": list(self.allowed_reads),
            "allowed_writes": list(self.allowed_writes),
            "allowed_commands": list(self.allowed_commands),
            "allowed_tools": list(self.allowed_tools),
            "network_allowed": self.network_allowed,
            "max_actions": self.max_actions,
            "max_seconds": self.max_seconds,
            "require_human_approval": list(self.require_human_approval),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CapabilityScope":
        _strict_keys(
            data,
            {"scope_id", "allowed_reads", "allowed_writes", "allowed_commands", "allowed_tools", "network_allowed", "max_actions", "max_seconds", "require_human_approval"},
            "CapabilityScope",
        )
        return cls(**data)


@dataclass(frozen=True)
class AuthorizationRequest:
    action_id: str
    run_id: str
    required_capabilities: tuple[str, ...]
    requested_reads: tuple[str, ...] = ()
    requested_writes: tuple[str, ...] = ()
    requested_commands: tuple[str, ...] = ()
    network_requested: bool = False
    approval_class: str | None = None
    reason_summary: str = ""

    def __post_init__(self) -> None:
        _id(self.action_id, "action_id")
        _id(self.run_id, "run_id")
        object.__setattr__(self, "required_capabilities", _tuple_strings(self.required_capabilities, "required_capabilities"))
        object.__setattr__(self, "requested_reads", normalize_relative_paths(self.requested_reads, "requested_reads"))
        object.__setattr__(self, "requested_writes", normalize_relative_paths(self.requested_writes, "requested_writes"))
        object.__setattr__(self, "requested_commands", _tuple_strings(self.requested_commands, "requested_commands"))
        if not isinstance(self.network_requested, bool):
            raise KernelValidationError("network_requested must be boolean")
        if self.approval_class is not None:
            _string(self.approval_class, "approval_class")
        if self.reason_summary:
            _summary(self.reason_summary, "reason_summary")

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "run_id": self.run_id,
            "required_capabilities": list(self.required_capabilities),
            "requested_reads": list(self.requested_reads),
            "requested_writes": list(self.requested_writes),
            "requested_commands": list(self.requested_commands),
            "network_requested": self.network_requested,
            "approval_class": self.approval_class,
            "reason_summary": self.reason_summary,
        }


@dataclass(frozen=True)
class AuthorizationDecision:
    decision_id: str
    action_id: str
    run_id: str
    status: str
    scope_id: str
    reason_summary: str
    checked_capabilities: tuple[str, ...]
    created_by: str = "kernel"

    def __post_init__(self) -> None:
        _id(self.decision_id, "decision_id")
        _id(self.action_id, "action_id")
        _id(self.run_id, "run_id")
        if self.status not in {item.value for item in AuthorizationStatus}:
            raise KernelValidationError(f"unknown authorization status: {self.status}")
        _id(self.scope_id, "scope_id")
        _summary(self.reason_summary)
        object.__setattr__(self, "checked_capabilities", _tuple_strings(self.checked_capabilities, "checked_capabilities"))
        _id(self.created_by, "created_by")

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "run_id": self.run_id,
            "status": self.status,
            "scope_id": self.scope_id,
            "reason_summary": self.reason_summary,
            "checked_capabilities": list(self.checked_capabilities),
            "created_by": self.created_by,
        }


def _path_allowed(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatchcase(path, pattern) or path == pattern or path.startswith(pattern.rstrip("*") + "/") for pattern in patterns)


def authorize_action(scope: CapabilityScope, request: AuthorizationRequest, *, decision_id: str | None = None) -> AuthorizationDecision:
    """Authorize before execution; unknown capabilities and overreach deny."""

    decision_id = decision_id or f"decision-{request.action_id}"
    missing = sorted(set(request.required_capabilities) - set(scope.allowed_tools))
    denied_reads = sorted(path for path in request.requested_reads if not _path_allowed(path, scope.allowed_reads))
    denied_writes = sorted(path for path in request.requested_writes if not _path_allowed(path, scope.allowed_writes))
    denied_commands = sorted(command for command in request.requested_commands if command not in scope.allowed_commands)
    if missing:
        status = AuthorizationStatus.DENY.value
        reason = f"unknown or unavailable capability: {', '.join(missing)}"
    elif denied_reads or denied_writes or denied_commands:
        status = AuthorizationStatus.DENY.value
        reason = "requested path or command is outside the declared scope"
    elif request.network_requested and not scope.network_allowed:
        status = AuthorizationStatus.DENY.value
        reason = "network is denied by the declared scope"
    elif request.approval_class and request.approval_class in scope.require_human_approval:
        status = AuthorizationStatus.REQUIRE_HUMAN_APPROVAL.value
        reason = f"action class requires explicit human approval: {request.approval_class}"
    else:
        status = AuthorizationStatus.ALLOW.value
        reason = "requested capabilities and paths are within the declared scope"
    return AuthorizationDecision(
        decision_id=decision_id,
        action_id=request.action_id,
        run_id=request.run_id,
        status=status,
        scope_id=scope.scope_id,
        reason_summary=reason,
        checked_capabilities=request.required_capabilities,
    )


@dataclass(frozen=True)
class StateEvent:
    event_id: str
    run_id: str
    sequence: int
    from_phase: str | None
    to_phase: str
    actor_id: str
    summary: str

    def __post_init__(self) -> None:
        _id(self.event_id, "event_id")
        _id(self.run_id, "run_id")
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise KernelValidationError("sequence must be a non-negative integer")
        if self.from_phase is not None and self.from_phase not in ALLOWED_PHASES:
            raise KernelValidationError(f"unknown from_phase: {self.from_phase}")
        if self.to_phase not in ALLOWED_PHASES:
            raise KernelValidationError(f"unknown to_phase: {self.to_phase}")
        _id(self.actor_id, "actor_id")
        _summary(self.summary)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "from_phase": self.from_phase,
            "to_phase": self.to_phase,
            "actor_id": self.actor_id,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    run_id: str
    phase: str
    state_ref: str
    state_sha256: str
    event_count: int
    created_by: str
    parent_checkpoint_id: str | None = None
    reason_summary: str = ""

    def __post_init__(self) -> None:
        _id(self.checkpoint_id, "checkpoint_id")
        _id(self.run_id, "run_id")
        if self.phase not in ALLOWED_PHASES:
            raise KernelValidationError(f"unknown checkpoint phase: {self.phase}")
        _string(self.state_ref, "state_ref")
        if not re.fullmatch(r"[0-9a-f]{64}", self.state_sha256):
            raise KernelValidationError("state_sha256 must be a lowercase SHA-256 digest")
        if not isinstance(self.event_count, int) or self.event_count < 0:
            raise KernelValidationError("event_count must be a non-negative integer")
        _id(self.created_by, "created_by")
        if self.parent_checkpoint_id is not None:
            _id(self.parent_checkpoint_id, "parent_checkpoint_id")
        if self.reason_summary:
            _summary(self.reason_summary, "reason_summary")

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "run_id": self.run_id,
            "phase": self.phase,
            "state_ref": self.state_ref,
            "state_sha256": self.state_sha256,
            "event_count": self.event_count,
            "created_by": self.created_by,
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "reason_summary": self.reason_summary,
        }


@dataclass(frozen=True)
class ResumeCapsule:
    capsule_id: str
    run_id: str
    checkpoint_id: str
    state_ref: str
    state_sha256: str
    pending_action_ids: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    created_by: str
    handoff: "Handoff"

    def __post_init__(self) -> None:
        _id(self.capsule_id, "capsule_id")
        _id(self.run_id, "run_id")
        _id(self.checkpoint_id, "checkpoint_id")
        _string(self.state_ref, "state_ref")
        if not re.fullmatch(r"[0-9a-f]{64}", self.state_sha256):
            raise KernelValidationError("state_sha256 must be a lowercase SHA-256 digest")
        object.__setattr__(self, "pending_action_ids", tuple(_id(item, "pending_action_ids[]") for item in self.pending_action_ids))
        object.__setattr__(self, "required_capabilities", _tuple_strings(self.required_capabilities, "required_capabilities"))
        _id(self.created_by, "created_by")

    def to_dict(self) -> dict[str, Any]:
        return {
            "capsule_id": self.capsule_id,
            "run_id": self.run_id,
            "checkpoint_id": self.checkpoint_id,
            "state_ref": self.state_ref,
            "state_sha256": self.state_sha256,
            "pending_action_ids": list(self.pending_action_ids),
            "required_capabilities": list(self.required_capabilities),
            "created_by": self.created_by,
            "handoff": self.handoff.to_dict(),
        }


@dataclass(frozen=True)
class Handoff:
    from_executor_id: str
    to_executor_id: str
    reason_summary: str
    resume_ref: str

    def __post_init__(self) -> None:
        _id(self.from_executor_id, "from_executor_id")
        _id(self.to_executor_id, "to_executor_id")
        if self.from_executor_id == self.to_executor_id:
            raise KernelValidationError("handoff must identify a different executor")
        _summary(self.reason_summary, "reason_summary")
        _string(self.resume_ref, "resume_ref")

    def to_dict(self) -> dict[str, str]:
        return {
            "from_executor_id": self.from_executor_id,
            "to_executor_id": self.to_executor_id,
            "reason_summary": self.reason_summary,
            "resume_ref": self.resume_ref,
        }


@dataclass(frozen=True)
class MemoryEvent:
    event_id: str
    run_id: str
    event_type: str
    source_refs: tuple[str, ...]
    public_summary: str
    created_by: str
    retention: str = "run"
    supersession_state: str = "active"
    domain_metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        _id(self.event_id, "event_id")
        _id(self.run_id, "run_id")
        _string(self.event_type, "event_type")
        object.__setattr__(self, "source_refs", _tuple_strings(self.source_refs, "source_refs"))
        _summary(self.public_summary, "public_summary")
        _id(self.created_by, "created_by")
        _string(self.retention, "retention")
        _string(self.supersession_state, "supersession_state")
        if self.domain_metadata is not None and not isinstance(self.domain_metadata, Mapping):
            raise KernelValidationError("domain_metadata must be an object when provided")

    def to_dict(self) -> dict[str, Any]:
        result = {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "event_type": self.event_type,
            "source_refs": list(self.source_refs),
            "public_summary": self.public_summary,
            "created_by": self.created_by,
            "retention": self.retention,
            "supersession_state": self.supersession_state,
        }
        if self.domain_metadata is not None:
            result["domain_metadata"] = _jsonable(dict(self.domain_metadata))
        return result


@dataclass(frozen=True)
class InvariantVerdict:
    invariant_id: str
    passed: bool
    reason_summary: str
    checked_at_event: int

    def __post_init__(self) -> None:
        _id(self.invariant_id, "invariant_id")
        if not isinstance(self.passed, bool):
            raise KernelValidationError("passed must be boolean")
        _summary(self.reason_summary, "reason_summary")
        if not isinstance(self.checked_at_event, int) or self.checked_at_event < 0:
            raise KernelValidationError("checked_at_event must be a non-negative integer")

    def to_dict(self) -> dict[str, Any]:
        return {
            "invariant_id": self.invariant_id,
            "passed": self.passed,
            "reason_summary": self.reason_summary,
            "checked_at_event": self.checked_at_event,
        }


def assert_no_authority_upgrade(authority_tokens: Sequence[str]) -> None:
    """Reject a generic boundary record that tries to grant Kernel authority."""

    tokens = set(_tuple_strings(authority_tokens, "authority_tokens"))
    violations = sorted(tokens & KERNEL_FORBIDDEN_AUTHORITY_UPGRADES)
    if violations:
        raise KernelValidationError(f"{KERNEL_NON_ESCALATION} rejected authority upgrades: {violations}")


def validate_resume_lineage(checkpoint: Checkpoint, capsule: ResumeCapsule, current_state_sha256: str, *, executor_id: str) -> None:
    """Fail closed when a capsule is detached from its checkpoint or state."""

    if checkpoint.run_id != capsule.run_id:
        raise KernelValidationError("resume capsule run_id does not match checkpoint")
    if checkpoint.checkpoint_id != capsule.checkpoint_id:
        raise KernelValidationError("resume capsule checkpoint_id does not match checkpoint")
    if checkpoint.state_sha256 != capsule.state_sha256 or current_state_sha256 != capsule.state_sha256:
        raise KernelValidationError("resume capsule state digest does not match persisted state")
    if capsule.handoff.to_executor_id != executor_id:
        raise KernelValidationError("resume executor does not match the recorded handoff")
    if capsule.handoff.from_executor_id == executor_id:
        raise KernelValidationError("resume executor must be different from checkpoint executor")
