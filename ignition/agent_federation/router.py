"""Deterministic, data-driven routing for External Agent Federation R1.

The router evaluates observable executor descriptors against an OS task
request and a data policy.  It does not instantiate vendors, widen capability
ceilings, or decide truth.  A Supervisor can consume the resulting
``RoutingDecision`` as a dispatch plan while remaining vendor-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import ApprovalPolicy, ExecutorDescriptor, FederationContractError
from .sdk import AdapterSDKError, CapabilityMismatch, map_capabilities


ROUTING_POLICY_SCHEMA = "federation-routing-policy-r1"
ROUTING_DECISION_STATES = frozenset({"SELECTED", "NO_MATCH", "PIN_UNAVAILABLE"})
HEALTH_RANK = {"HEALTHY": 0, "DEGRADED": 1}


class RoutingError(FederationContractError):
    """Raised when routing policy or an OS request is invalid."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RoutingError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise RoutingError(f"{field} must be an array")
    result = tuple(_text(item, f"{field}[]") for item in value)
    if nonempty and not result:
        raise RoutingError(f"{field} must not be empty")
    if len(result) != len(set(result)):
        raise RoutingError(f"{field} must not contain duplicates")
    return result


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RoutingError(f"{field} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class ExecutorRoutingProfile:
    """Policy data for one executor family, independent of its implementation."""

    executor_id: str
    enabled: bool
    task_types: tuple[str, ...]
    privacy_classes: tuple[str, ...]
    workspace_localities: tuple[str, ...]
    permission_ceiling: tuple[str, ...]
    allowed_effects: tuple[str, ...]
    approval_required_effects: tuple[str, ...]
    default_preference_rank: int
    task_type_preferences: Mapping[str, int]
    requires_external_approval: bool
    sandbox_semantics: str

    def __post_init__(self) -> None:
        _text(self.executor_id, "routing_profile.executor_id")
        for field in ("task_types", "privacy_classes", "workspace_localities", "permission_ceiling", "allowed_effects"):
            object.__setattr__(self, field, _strings(getattr(self, field), f"routing_profile.{field}", nonempty=True))
        object.__setattr__(self, "approval_required_effects", _strings(self.approval_required_effects, "routing_profile.approval_required_effects"))
        if not isinstance(self.enabled, bool) or not isinstance(self.requires_external_approval, bool):
            raise RoutingError("routing profile booleans are required")
        object.__setattr__(self, "default_preference_rank", _positive_int(self.default_preference_rank, "routing_profile.default_preference_rank"))
        if not isinstance(self.task_type_preferences, Mapping):
            raise RoutingError("routing_profile.task_type_preferences must be an object")
        preferences = {str(key): _positive_int(value, f"routing_profile.task_type_preferences[{key}]") for key, value in self.task_type_preferences.items()}
        object.__setattr__(self, "task_type_preferences", preferences)
        _text(self.sandbox_semantics, "routing_profile.sandbox_semantics")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutorRoutingProfile":
        keys = {
            "executor_id", "enabled", "task_types", "privacy_classes", "workspace_localities",
            "permission_ceiling", "allowed_effects", "approval_required_effects",
            "default_preference_rank", "task_type_preferences", "requires_external_approval",
            "sandbox_semantics",
        }
        if not isinstance(data, Mapping) or set(data) != keys:
            raise RoutingError(f"routing profile keys must be exactly {sorted(keys)}")
        return cls(**dict(data))

    def to_dict(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id,
            "enabled": self.enabled,
            "task_types": list(self.task_types),
            "privacy_classes": list(self.privacy_classes),
            "workspace_localities": list(self.workspace_localities),
            "permission_ceiling": list(self.permission_ceiling),
            "allowed_effects": list(self.allowed_effects),
            "approval_required_effects": list(self.approval_required_effects),
            "default_preference_rank": self.default_preference_rank,
            "task_type_preferences": dict(self.task_type_preferences),
            "requires_external_approval": self.requires_external_approval,
            "sandbox_semantics": self.sandbox_semantics,
        }


@dataclass(frozen=True)
class RoutingPolicy:
    policy_id: str
    allow_degraded: bool
    profiles: tuple[ExecutorRoutingProfile, ...]

    def __post_init__(self) -> None:
        _text(self.policy_id, "routing_policy.policy_id")
        if not isinstance(self.allow_degraded, bool):
            raise RoutingError("routing_policy.allow_degraded must be boolean")
        if not isinstance(self.profiles, (list, tuple)) or not self.profiles:
            raise RoutingError("routing_policy.profiles must not be empty")
        if any(not isinstance(profile, ExecutorRoutingProfile) for profile in self.profiles):
            raise RoutingError("routing_policy.profiles must contain ExecutorRoutingProfile values")
        ids = [profile.executor_id for profile in self.profiles]
        if len(ids) != len(set(ids)):
            raise RoutingError("routing policy executor ids must be unique")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RoutingPolicy":
        if not isinstance(data, Mapping) or set(data) != {"schema_version", "policy_id", "allow_degraded", "profiles"}:
            raise RoutingError("routing policy keys are invalid")
        if data["schema_version"] != ROUTING_POLICY_SCHEMA:
            raise RoutingError("routing policy schema is not federation-routing-policy-r1")
        profiles = data["profiles"]
        if not isinstance(profiles, list):
            raise RoutingError("routing policy profiles must be an array")
        return cls(
            policy_id=data["policy_id"],
            allow_degraded=data["allow_degraded"],
            profiles=tuple(ExecutorRoutingProfile.from_dict(item) for item in profiles),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": ROUTING_POLICY_SCHEMA,
            "policy_id": self.policy_id,
            "allow_degraded": self.allow_degraded,
            "profiles": [profile.to_dict() for profile in self.profiles],
        }

    def profile(self, executor_id: str) -> ExecutorRoutingProfile | None:
        return next((profile for profile in self.profiles if profile.executor_id == executor_id), None)


def load_routing_policy(path: str | Path) -> RoutingPolicy:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingError(f"cannot load routing policy: {exc}") from exc
    return RoutingPolicy.from_dict(data)


@dataclass(frozen=True)
class RoutingRequest:
    federation_task_id: str
    owner_ref: str
    profile_ref: str
    task_type: str
    required_capabilities: tuple[str, ...]
    required_effects: tuple[str, ...]
    task_granularity: str
    privacy_class: str
    workspace_locality: str
    approval_policy: ApprovalPolicy
    pinned_executor_id: str | None = None
    pin_strict: bool = False

    def __post_init__(self) -> None:
        for field in ("federation_task_id", "owner_ref", "profile_ref", "task_type", "task_granularity", "privacy_class", "workspace_locality"):
            _text(getattr(self, field), f"routing_request.{field}")
        capabilities = map_capabilities(self.required_capabilities)
        if not capabilities:
            raise RoutingError("routing_request.required_capabilities must not be empty")
        object.__setattr__(self, "required_capabilities", capabilities)
        object.__setattr__(self, "required_effects", _strings(self.required_effects, "routing_request.required_effects"))
        if self.task_granularity not in {"ACTION", "SUBTASK", "EPISODE"}:
            raise RoutingError("routing_request.task_granularity is unsupported")
        if not isinstance(self.approval_policy, ApprovalPolicy):
            raise RoutingError("routing_request.approval_policy must be ApprovalPolicy")
        if self.pinned_executor_id is not None:
            _text(self.pinned_executor_id, "routing_request.pinned_executor_id")
        if not isinstance(self.pin_strict, bool):
            raise RoutingError("routing_request.pin_strict must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "federation_task_id": self.federation_task_id,
            "owner_ref": self.owner_ref,
            "profile_ref": self.profile_ref,
            "task_type": self.task_type,
            "required_capabilities": list(self.required_capabilities),
            "required_effects": list(self.required_effects),
            "task_granularity": self.task_granularity,
            "privacy_class": self.privacy_class,
            "workspace_locality": self.workspace_locality,
            "approval_policy": self.approval_policy.to_dict(),
            "pinned_executor_id": self.pinned_executor_id,
            "pin_strict": self.pin_strict,
        }


@dataclass(frozen=True)
class CandidateEvaluation:
    executor_id: str
    instance_id: str
    eligible: bool
    rejection_reasons: tuple[str, ...]
    ranking_key: tuple[Any, ...]
    health_status: str
    declared_capabilities: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id,
            "instance_id": self.instance_id,
            "eligible": self.eligible,
            "rejection_reasons": list(self.rejection_reasons),
            "ranking_key": list(self.ranking_key),
            "health_status": self.health_status,
            "declared_capabilities": list(self.declared_capabilities),
        }


@dataclass(frozen=True)
class RoutingDecision:
    federation_task_id: str
    status: str
    selected_executor_id: str | None
    selected_instance_id: str | None
    selection_reason: str
    effective_permission: Mapping[str, Any]
    fallback_order: tuple[str, ...]
    candidates: tuple[CandidateEvaluation, ...]
    policy_id: str

    def __post_init__(self) -> None:
        _text(self.federation_task_id, "routing_decision.federation_task_id")
        if self.status not in ROUTING_DECISION_STATES:
            raise RoutingError("routing_decision.status is unsupported")
        _text(self.selection_reason, "routing_decision.selection_reason")
        _text(self.policy_id, "routing_decision.policy_id")
        if not isinstance(self.effective_permission, Mapping):
            raise RoutingError("routing_decision.effective_permission must be an object")
        object.__setattr__(self, "fallback_order", _strings(self.fallback_order, "routing_decision.fallback_order"))
        if not isinstance(self.candidates, (list, tuple)):
            raise RoutingError("routing_decision.candidates must be an array")

    @property
    def selected(self) -> bool:
        return self.status == "SELECTED" and self.selected_executor_id is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "federation_task_id": self.federation_task_id,
            "status": self.status,
            "selected_executor_id": self.selected_executor_id,
            "selected_instance_id": self.selected_instance_id,
            "selection_reason": self.selection_reason,
            "effective_permission": dict(self.effective_permission),
            "fallback_order": list(self.fallback_order),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "policy_id": self.policy_id,
        }


class FederationRouter:
    """Choose an executor by observable policy facts, never by vendor code."""

    def __init__(
        self,
        policy: RoutingPolicy,
        descriptors: Sequence[ExecutorDescriptor],
        *,
        instance_ids: Mapping[str, str] | None = None,
    ) -> None:
        if not isinstance(policy, RoutingPolicy):
            raise RoutingError("FederationRouter requires RoutingPolicy")
        self.policy = policy
        self.descriptors = tuple(descriptors)
        if any(not isinstance(descriptor, ExecutorDescriptor) for descriptor in self.descriptors):
            raise RoutingError("FederationRouter descriptors must be ExecutorDescriptor values")
        ids = [descriptor.executor_id for descriptor in self.descriptors]
        if len(ids) != len(set(ids)):
            raise RoutingError("executor descriptors must have unique executor ids")
        self.instance_ids = dict(instance_ids or {})
        for executor_id, instance_id in self.instance_ids.items():
            _text(executor_id, "instance_ids.executor_id")
            _text(instance_id, "instance_ids.instance_id")

    def _instance_id(self, executor_id: str) -> str:
        return self.instance_ids.get(executor_id, f"{executor_id}.instance-1")

    def _evaluate(self, request: RoutingRequest, descriptor: ExecutorDescriptor) -> CandidateEvaluation:
        executor_id = descriptor.executor_id
        instance_id = self._instance_id(executor_id)
        profile = self.policy.profile(executor_id)
        reasons: list[str] = []
        if profile is None:
            reasons.append("POLICY_PROFILE_MISSING")
            return CandidateEvaluation(executor_id, instance_id, False, tuple(reasons), (99, 99, 99, 99, executor_id, instance_id), descriptor.health.status, descriptor.capability_tokens)
        if not profile.enabled:
            reasons.append("DISABLED_BY_POLICY")
        try:
            declared = set(map_capabilities(descriptor.capability_tokens))
            required = set(map_capabilities(request.required_capabilities))
            missing = sorted(required - declared)
            if missing:
                reasons.append("CAPABILITY_MISMATCH:" + ",".join(missing))
            ceiling_missing = sorted(required - set(profile.permission_ceiling))
            if ceiling_missing:
                reasons.append("PERMISSION_CEILING_MISMATCH:" + ",".join(ceiling_missing))
        except (AdapterSDKError, CapabilityMismatch, RoutingError) as exc:
            reasons.append(f"CAPABILITY_MAPPING_INVALID:{type(exc).__name__}")
        effect_missing = sorted(set(request.required_effects) - set(profile.allowed_effects))
        if effect_missing:
            reasons.append("EFFECT_PERMISSION_MISMATCH:" + ",".join(effect_missing))
        approval_required = set(request.required_effects) & set(profile.approval_required_effects)
        if approval_required and (request.approval_policy.mode == "DENY" or not request.approval_policy.external_approval_allowed):
            reasons.append("EXTERNAL_APPROVAL_REQUIRED:" + ",".join(sorted(approval_required)))
        if profile.requires_external_approval and (request.approval_policy.mode == "DENY" or not request.approval_policy.external_approval_allowed):
            reasons.append("EXTERNAL_APPROVAL_REQUIRED:profile")
        if descriptor.availability != "AVAILABLE" or descriptor.health.status == "UNAVAILABLE":
            reasons.append("EXECUTOR_UNAVAILABLE")
        if descriptor.health.status == "UNKNOWN":
            reasons.append("HEALTH_UNKNOWN")
        if descriptor.health.status == "DEGRADED" and not self.policy.allow_degraded:
            reasons.append("DEGRADED_NOT_ALLOWED")
        if request.task_granularity not in descriptor.supported_task_granularities:
            reasons.append("GRANULARITY_UNSUPPORTED")
        if request.privacy_class not in profile.privacy_classes and "*" not in profile.privacy_classes:
            reasons.append("PRIVACY_INCOMPATIBLE")
        if request.workspace_locality not in profile.workspace_localities and "ANY" not in profile.workspace_localities:
            reasons.append("WORKSPACE_LOCALITY_INCOMPATIBLE")
        if request.task_type not in profile.task_types and "*" not in profile.task_types:
            reasons.append("TASK_TYPE_UNSUPPORTED")
        eligible = not reasons
        pin_rank = 0 if request.pinned_executor_id == executor_id else 1
        health_rank = HEALTH_RANK.get(descriptor.health.status, 99)
        preference_rank = profile.task_type_preferences.get(request.task_type, profile.default_preference_rank)
        surplus = len(set(descriptor.capability_tokens) - set(request.required_capabilities))
        permission_surplus = len(set(profile.permission_ceiling) - set(request.required_capabilities))
        ranking_key = (pin_rank, health_rank, preference_rank, surplus, permission_surplus, executor_id, instance_id)
        return CandidateEvaluation(executor_id, instance_id, eligible, tuple(reasons), ranking_key, descriptor.health.status, descriptor.capability_tokens)

    def route(self, request: RoutingRequest) -> RoutingDecision:
        if not isinstance(request, RoutingRequest):
            raise RoutingError("FederationRouter.route requires RoutingRequest")
        evaluations = tuple(self._evaluate(request, descriptor) for descriptor in self.descriptors)
        eligible = sorted((item for item in evaluations if item.eligible), key=lambda item: item.ranking_key)
        pinned = next((item for item in evaluations if item.executor_id == request.pinned_executor_id), None) if request.pinned_executor_id else None
        if request.pin_strict and request.pinned_executor_id and (pinned is None or not pinned.eligible):
            return RoutingDecision(
                request.federation_task_id, "PIN_UNAVAILABLE", None, None,
                "strict Owner/Profile pin is unavailable or incompatible; no fallback was selected",
                {"capabilities": list(request.required_capabilities), "effects": list(request.required_effects), "approval_mode": request.approval_policy.mode},
                (), evaluations, self.policy.policy_id,
            )
        if not eligible:
            reason = "no executor satisfied capability, permission, health, privacy, workspace and task constraints"
            if request.pinned_executor_id:
                reason = f"requested pin {request.pinned_executor_id} was not eligible and no matching fallback exists"
            return RoutingDecision(
                request.federation_task_id, "NO_MATCH", None, None, reason,
                {"capabilities": list(request.required_capabilities), "effects": list(request.required_effects), "approval_mode": request.approval_policy.mode},
                (), evaluations, self.policy.policy_id,
            )
        selected = eligible[0]
        selected_descriptor = next(descriptor for descriptor in self.descriptors if descriptor.executor_id == selected.executor_id)
        selected_profile = self.policy.profile(selected.executor_id)
        assert selected_profile is not None
        fallback_order = tuple(item.executor_id for item in eligible[1:])
        pin_reason = "explicit pin priority; " if request.pinned_executor_id == selected.executor_id else ""
        reason = f"{pin_reason}selected healthy/compatible executor by configured preference, least privilege and stable executor-id tie-break"
        effective_permission = {
            "capabilities": list(request.required_capabilities),
            "effects": list(request.required_effects),
            "approval_mode": request.approval_policy.mode,
            "external_approval_allowed": request.approval_policy.external_approval_allowed,
            "executor_permission_ceiling": list(selected_profile.permission_ceiling),
            "sandbox_semantics": selected_profile.sandbox_semantics,
            "descriptor_health": selected_descriptor.health.status,
        }
        return RoutingDecision(
            request.federation_task_id, "SELECTED", selected.executor_id, selected.instance_id,
            reason, effective_permission, fallback_order, evaluations, self.policy.policy_id,
        )


__all__ = [
    "CandidateEvaluation",
    "ExecutorRoutingProfile",
    "FederationRouter",
    "RoutingDecision",
    "RoutingError",
    "RoutingPolicy",
    "RoutingRequest",
    "load_routing_policy",
]
