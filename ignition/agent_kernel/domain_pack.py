"""Domain Pack contract owned by the generic boundary, not by a domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import KERNEL_FORBIDDEN_AUTHORITY_UPGRADES, KernelValidationError, _id, _strict_keys, _string, _tuple_strings


FORBIDDEN_PACK_AUTHORITY = KERNEL_FORBIDDEN_AUTHORITY_UPGRADES


@dataclass(frozen=True)
class DomainPackManifest:
    pack_id: str
    display_name: str
    domain: str
    capabilities_provided: tuple[str, ...]
    object_types: tuple[str, ...]
    validators: tuple[str, ...]
    human_entries: tuple[str, ...]
    machine_entries: tuple[str, ...]
    required_kernel_capabilities: tuple[str, ...]
    prohibited_authority_upgrades: tuple[str, ...]
    optional_runtime_hooks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _id(self.pack_id, "pack_id")
        _string(self.display_name, "display_name")
        _string(self.domain, "domain")
        for field in (
            "capabilities_provided",
            "object_types",
            "validators",
            "human_entries",
            "machine_entries",
            "required_kernel_capabilities",
            "prohibited_authority_upgrades",
            "optional_runtime_hooks",
        ):
            object.__setattr__(self, field, _tuple_strings(getattr(self, field), field))
        missing = sorted(FORBIDDEN_PACK_AUTHORITY - set(self.prohibited_authority_upgrades))
        if missing:
            raise KernelValidationError(f"domain pack must prohibit kernel authority upgrades: {missing}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "display_name": self.display_name,
            "domain": self.domain,
            "capabilities_provided": list(self.capabilities_provided),
            "object_types": list(self.object_types),
            "validators": list(self.validators),
            "human_entries": list(self.human_entries),
            "machine_entries": list(self.machine_entries),
            "required_kernel_capabilities": list(self.required_kernel_capabilities),
            "prohibited_authority_upgrades": list(self.prohibited_authority_upgrades),
            "optional_runtime_hooks": list(self.optional_runtime_hooks),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DomainPackManifest":
        _strict_keys(
            data,
            {
                "pack_id",
                "display_name",
                "domain",
                "capabilities_provided",
                "object_types",
                "validators",
                "human_entries",
                "machine_entries",
                "required_kernel_capabilities",
                "prohibited_authority_upgrades",
                "optional_runtime_hooks",
            },
            "DomainPackManifest",
        )
        return cls(**data)
