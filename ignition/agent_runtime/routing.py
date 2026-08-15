"""Pack-aware planning and validation routing with explicit authority ceilings."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from .pack_registry import CapabilityRoute, PackBus, PackLoader, PackRegistry, PackRegistryError


class PackRoutingError(PackRegistryError):
    """Raised when a Pack route or scoped validator result crosses its boundary."""


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PackActionProvenance:
    action_id: str
    capability: str
    pack_id: str
    pack_version: str
    object_type: str
    validator_ref: str | None
    hook_ref: str | None
    source: str = "PACK_AWARE_PLANNER"
    authority_boundary: str = "DECLARED_PACK_SCOPE_ONLY_NO_RUNTIME_PERMISSION_OR_TRUTH_UPGRADE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "capability": self.capability,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "object_type": self.object_type,
            "validator_ref": self.validator_ref,
            "hook_ref": self.hook_ref,
            "source": self.source,
            "authority_boundary": self.authority_boundary,
        }


@dataclass(frozen=True)
class PackValidationReceipt:
    pack_id: str
    pack_version: str
    validator_ref: str
    object_type: str
    status: str
    summary: str
    result_sha256: str
    authority_effect: str = "DECLARED_SCOPE_ONLY_NOT_RUNTIME_PERMISSION_OR_TRUTH"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "PACK_VALIDATOR_RESULT",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "validator_ref": self.validator_ref,
            "object_type": self.object_type,
            "validation_status": self.status,
            "summary": self.summary,
            "result_sha256": self.result_sha256,
            "authority_effect": self.authority_effect,
        }


class PackAwareRouter:
    """Connect loaded Pack metadata to plans and validator proposals only."""

    def __init__(self, registry: PackRegistry, loader: PackLoader | None = None, *, allowed_pack_ids: Sequence[str] | None = None) -> None:
        self.registry = registry
        self.loader = loader or PackLoader(registry)
        self.allowed_pack_ids = frozenset(allowed_pack_ids) if allowed_pack_ids is not None else None
        if self.allowed_pack_ids is not None:
            unknown = sorted(self.allowed_pack_ids - set(registry.pack_ids))
            if unknown:
                raise PackRoutingError(f"profile selected unknown Packs: {unknown}")

    @property
    def available_pack_ids(self) -> tuple[str, ...]:
        loaded = {item.manifest.pack_id for item in self.loader.loaded()}
        if self.allowed_pack_ids is not None:
            loaded &= set(self.allowed_pack_ids)
        return tuple(sorted(loaded))

    def catalog(self) -> dict[str, Any]:
        routes = []
        for route in self.registry.routes():
            if route.pack_id in self.available_pack_ids:
                routes.append(route.to_dict())
        return {
            "packs": list(self.available_pack_ids),
            "routes": routes,
            "read_only": True,
            "authority_boundary": "CATALOG_ONLY_NO_IMPORT_NO_LOAD_NO_PERMISSION_OR_TRUTH_AUTHORITY",
        }

    def route(self, capability: str) -> CapabilityRoute:
        routes = self.registry.routes(capability)
        scoped = tuple(route for route in routes if route.pack_id in self.available_pack_ids and self.loader.is_loaded(route.pack_id))
        if len(scoped) != 1:
            raise PackRoutingError(f"capability has no unique loaded scoped Pack route: {capability}")
        return scoped[0]

    def annotate_action(
        self,
        action_id: str,
        capability: str,
        *,
        object_type: str,
        validator_ref: str | None = None,
        hook_ref: str | None = None,
    ) -> PackActionProvenance:
        route = self.route(capability)
        if object_type not in route.object_types:
            raise PackRoutingError(f"object type is outside Pack route scope: {object_type}")
        manifest = self.registry.get(route.pack_id)
        if validator_ref is not None and validator_ref not in manifest.validator_entrypoints:
            raise PackRoutingError(f"validator is not declared by Pack {route.pack_id}: {validator_ref}")
        if hook_ref is not None and hook_ref not in manifest.planning_hooks + manifest.action_hooks:
            raise PackRoutingError(f"hook is not declared by Pack {route.pack_id}: {hook_ref}")
        return PackActionProvenance(
            action_id=action_id, capability=capability, pack_id=route.pack_id,
            pack_version=route.pack_version, object_type=object_type,
            validator_ref=validator_ref, hook_ref=hook_ref,
        )

    def route_validator(
        self,
        pack_id: str,
        validator_ref: str,
        *,
        object_type: str,
        result: Mapping[str, Any],
    ) -> PackValidationReceipt:
        if pack_id not in self.available_pack_ids or not self.loader.is_loaded(pack_id):
            raise PackRoutingError(f"Pack is not loaded in the current scope: {pack_id}")
        manifest = self.registry.get(pack_id)
        if validator_ref not in manifest.validator_entrypoints:
            raise PackRoutingError(f"validator is not declared by Pack {pack_id}: {validator_ref}")
        if object_type not in manifest.object_types:
            raise PackRoutingError(f"validator object type is outside Pack {pack_id}: {object_type}")
        if not isinstance(result, Mapping):
            raise PackRoutingError("Pack validator result must be an object")
        status = result.get("status")
        summary = result.get("summary")
        if status not in {"PASS", "FAIL", "NOT_RUN"} or not isinstance(summary, str) or not summary.strip():
            raise PackRoutingError("Pack validator result must contain typed status and summary")
        forbidden = {
            "truth_authority", "owner_acceptance", "epistemically_accepted", "permission_granted",
            "capability_scope_expanded", "charter_mutation", "runtime_terminal_state",
        }
        escalations = sorted(key for key in forbidden if result.get(key) not in (None, False, "", []))
        if escalations:
            raise PackRoutingError(f"Pack validator result attempted authority crossing: {escalations}")
        return PackValidationReceipt(
            pack_id=pack_id, pack_version=manifest.version, validator_ref=validator_ref,
            object_type=object_type, status=status, summary=summary,
            result_sha256=_digest(dict(result)),
        )

    def propose_hook(self, pack_id: str, hook_ref: str, *, payload: Mapping[str, Any]) -> dict[str, Any]:
        if pack_id not in self.available_pack_ids or not self.loader.is_loaded(pack_id):
            raise PackRoutingError(f"Pack is not loaded in the current scope: {pack_id}")
        manifest = self.registry.get(pack_id)
        if hook_ref not in manifest.planning_hooks + manifest.action_hooks:
            raise PackRoutingError(f"hook is not declared by Pack {pack_id}: {hook_ref}")
        return {
            "status": "PACK_HOOK_PROPOSAL",
            "pack_id": pack_id,
            "pack_version": manifest.version,
            "hook_ref": hook_ref,
            "payload_sha256": _digest(dict(payload)),
            "execution": "NOT_PERFORMED_BY_PACK_AWARE_ROUTER",
            "authority_boundary": "DECLARED_PACK_SCOPE_ONLY_NO_RUNTIME_PERMISSION_OR_TRUTH_UPGRADE",
        }


__all__ = ["PackActionProvenance", "PackAwareRouter", "PackRoutingError", "PackValidationReceipt"]
