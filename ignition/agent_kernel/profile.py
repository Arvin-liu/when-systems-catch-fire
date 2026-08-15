"""Provider-neutral Agent Profile R0 contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import KernelValidationError, _id, _strict_keys, _string, _tuple_strings


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
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AgentProfile":
        _strict_keys(
            data,
            {
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
            },
            "AgentProfile",
        )
        return cls(**data)
