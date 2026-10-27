"""Provider-neutral Agent Profile R0 contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import KERNEL_FORBIDDEN_AUTHORITY_UPGRADES, KernelValidationError, _id, _strict_keys, _string, _tuple_strings


_PROFILE_EXTRA_KEYS = {
    "allowed_packs",
    "preferred_tool_classes",
    "forbidden_tool_classes",
    "approval_thresholds",
    "budget_defaults",
    "update_authority",
    "prohibited_authority_upgrades",
}
_APPROVAL_LEVELS = {
    "AUTO_ALLOWED_SAFE",
    "BOUNDED_WRITE_REQUIRES_APPROVAL",
    "COMMAND_REQUIRES_APPROVAL",
}
_DEFAULT_PROHIBITED_AUTHORITY_UPGRADES = tuple(sorted(KERNEL_FORBIDDEN_AUTHORITY_UPGRADES))


def _pairs(value: Any, field: str, *, numeric: bool = False) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        items = list(value.items())
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        raise KernelValidationError(f"{field} must be an object or pair array")
    normalized: list[tuple[str, Any]] = []
    for item in items:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise KernelValidationError(f"{field} must contain key/value pairs")
        key, item_value = item
        _string(key, f"{field}.key")
        if numeric:
            if not isinstance(item_value, (int, float)) or isinstance(item_value, bool) or item_value <= 0:
                raise KernelValidationError(f"{field}.{key} must be positive numeric")
        else:
            _string(item_value, f"{field}.{key}")
        normalized.append((key, item_value))
    if len({key for key, _ in normalized}) != len(normalized):
        raise KernelValidationError(f"{field} keys must be unique")
    return tuple(sorted(normalized, key=lambda pair: pair[0]))


@dataclass(frozen=True)
class AgentProfile:
    stable_agent_id: str
    owner_ref: str
    authority_refs: tuple[str, ...]
    charter_refs: tuple[str, ...]
    role: str
    allowed_capability_classes: tuple[str, ...]
    mutable_preference_refs: tuple[str, ...]
    update_policy: str
    memory_policy: str
    prohibited_self_escalation: bool = True
    allowed_packs: tuple[str, ...] = ()
    preferred_tool_classes: tuple[str, ...] = ()
    forbidden_tool_classes: tuple[str, ...] = ()
    approval_thresholds: tuple[tuple[str, str], ...] = ()
    budget_defaults: tuple[tuple[str, int | float], ...] = ()
    update_authority: str = "owner-only"
    prohibited_authority_upgrades: tuple[str, ...] = _DEFAULT_PROHIBITED_AUTHORITY_UPGRADES

    def __post_init__(self) -> None:
        _id(self.stable_agent_id, "stable_agent_id")
        _string(self.owner_ref, "owner_ref")
        object.__setattr__(self, "authority_refs", _tuple_strings(self.authority_refs, "authority_refs"))
        object.__setattr__(self, "charter_refs", _tuple_strings(self.charter_refs, "charter_refs"))
        _string(self.role, "role")
        object.__setattr__(self, "allowed_capability_classes", _tuple_strings(self.allowed_capability_classes, "allowed_capability_classes"))
        object.__setattr__(self, "mutable_preference_refs", _tuple_strings(self.mutable_preference_refs, "mutable_preference_refs"))
        _string(self.update_policy, "update_policy")
        _string(self.memory_policy, "memory_policy")
        if self.prohibited_self_escalation is not True:
            raise KernelValidationError("R0 profiles must prohibit self-escalation")
        object.__setattr__(self, "allowed_packs", tuple(sorted(_tuple_strings(self.allowed_packs, "allowed_packs"))))
        object.__setattr__(self, "preferred_tool_classes", tuple(sorted(_tuple_strings(self.preferred_tool_classes, "preferred_tool_classes"))))
        object.__setattr__(self, "forbidden_tool_classes", tuple(sorted(_tuple_strings(self.forbidden_tool_classes, "forbidden_tool_classes"))))
        thresholds = _pairs(self.approval_thresholds, "approval_thresholds")
        invalid_levels = sorted(set(value for _, value in thresholds) - _APPROVAL_LEVELS)
        if invalid_levels:
            raise KernelValidationError(f"approval_thresholds contain unknown levels: {invalid_levels}")
        object.__setattr__(self, "approval_thresholds", thresholds)
        budgets = _pairs(self.budget_defaults, "budget_defaults", numeric=True)
        invalid_budget_keys = sorted(set(key for key, _ in budgets) - {"max_actions", "max_seconds", "max_output_bytes", "max_writes"})
        if invalid_budget_keys:
            raise KernelValidationError(f"budget_defaults contain unknown keys: {invalid_budget_keys}")
        object.__setattr__(self, "budget_defaults", budgets)
        _string(self.update_authority, "update_authority")
        object.__setattr__(self, "prohibited_authority_upgrades", _tuple_strings(self.prohibited_authority_upgrades, "prohibited_authority_upgrades"))
        missing = sorted(set(_DEFAULT_PROHIBITED_AUTHORITY_UPGRADES) - set(self.prohibited_authority_upgrades))
        if missing:
            raise KernelValidationError(f"profile must prohibit kernel authority upgrades: {missing}")

    @property
    def approval_threshold_map(self) -> dict[str, str]:
        return dict(self.approval_thresholds)

    @property
    def budget_default_map(self) -> dict[str, int | float]:
        return dict(self.budget_defaults)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stable_agent_id": self.stable_agent_id,
            "owner_ref": self.owner_ref,
            "authority_refs": list(self.authority_refs),
            "charter_refs": list(self.charter_refs),
            "role": self.role,
            "allowed_capability_classes": list(self.allowed_capability_classes),
            "mutable_preference_refs": list(self.mutable_preference_refs),
            "update_policy": self.update_policy,
            "memory_policy": self.memory_policy,
            "prohibited_self_escalation": self.prohibited_self_escalation,
            "allowed_packs": list(self.allowed_packs),
            "preferred_tool_classes": list(self.preferred_tool_classes),
            "forbidden_tool_classes": list(self.forbidden_tool_classes),
            "approval_thresholds": dict(self.approval_thresholds),
            "budget_defaults": dict(self.budget_defaults),
            "update_authority": self.update_authority,
            "prohibited_authority_upgrades": list(self.prohibited_authority_upgrades),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AgentProfile":
        base_keys = {
            "stable_agent_id",
            "owner_ref",
            "authority_refs",
            "charter_refs",
            "role",
            "allowed_capability_classes",
            "mutable_preference_refs",
            "update_policy",
            "memory_policy",
            "prohibited_self_escalation",
        }
        _strict_keys(data, base_keys | _PROFILE_EXTRA_KEYS, "AgentProfile")
        missing_base = sorted(base_keys - set(data))
        if missing_base:
            raise KernelValidationError(f"AgentProfile is missing fields: {missing_base}")
        raw = dict(data)
        raw.setdefault("allowed_packs", ())
        raw.setdefault("preferred_tool_classes", ())
        raw.setdefault("forbidden_tool_classes", ())
        raw.setdefault("approval_thresholds", {})
        raw.setdefault("budget_defaults", {})
        raw.setdefault("update_authority", "owner-only")
        raw.setdefault("prohibited_authority_upgrades", _DEFAULT_PROHIBITED_AUTHORITY_UPGRADES)
        return cls(**raw)
