"""Provider-neutral Pack Registry and Bus for Agent Runtime R2.

Pack loading is deliberately declarative in R1: manifests are parsed and
validated, capabilities are routed, and health is reported.  No pack module
is imported and no hook is executed by this layer.  Domain code remains behind
the declared pack boundary and cannot expand Kernel or Workspace authority.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import KERNEL_FORBIDDEN_AUTHORITY_UPGRADES


class PackRegistryError(ValueError):
    """Raised when Pack discovery, validation, loading, or routing fails."""


PACK_SCHEMA_VERSION = "1.0.0"
SUPPORTED_KERNEL_APIS = ("r0",)
SUPPORTED_RUNTIME_APIS = ("r1", "r2")
LOAD_POLICIES = frozenset({"DECLARATIVE_METADATA_ONLY", "EXPLICIT_ACTIVATION"})
UNLOAD_POLICIES = frozenset({"SAFE_IF_NO_ACTIVE_RUNS", "RETAIN_UNTIL_EPISODE_END"})
PERMISSION_KEYS = frozenset({"read_paths", "write_paths", "command_classes", "tool_classes", "network"})
HEALTH_CHECK_KINDS = frozenset({"DECLARATIVE_MANIFEST"})
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise PackRegistryError(f"{field} must be a non-empty string")
    return value


def _id(value: Any, field: str) -> str:
    value = _string(value, field)
    if not ID_PATTERN.fullmatch(value):
        raise PackRegistryError(f"{field} has an invalid identifier")
    return value


def _strings(value: Any, field: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise PackRegistryError(f"{field} must be an array of strings")
    result = tuple(_string(item, f"{field}[]") for item in value)
    if len(result) != len(set(result)):
        raise PackRegistryError(f"{field} must not contain duplicates")
    return result


def _relative_paths(value: Any, field: str) -> tuple[str, ...]:
    paths = _strings(value, field)
    for path in paths:
        if path.startswith("/") or "\\" in path or path.startswith("file:"):
            raise PackRegistryError(f"{field} contains a non-portable path: {path}")
        parts = path.rstrip("/").split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise PackRegistryError(f"{field} contains a non-canonical path: {path}")
    return paths


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PackRegistryError(f"{field} must be an object")
    return {str(key): copy.deepcopy(item) for key, item in value.items()}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PackManifest:
    schema_version: str
    pack_id: str
    version: str
    display_name: str
    domain: str
    compatibility: tuple[tuple[str, str], ...]
    capabilities_provided: tuple[str, ...]
    required_kernel_capabilities: tuple[str, ...]
    required_runtime_capabilities: tuple[str, ...]
    object_types: tuple[str, ...]
    validator_entrypoints: tuple[str, ...]
    action_hooks: tuple[str, ...]
    planning_hooks: tuple[str, ...]
    human_entries: tuple[str, ...]
    machine_entries: tuple[str, ...]
    permissions_requested: Mapping[str, Any]
    prohibited_authority_upgrades: tuple[str, ...]
    load_policy: str
    unload_policy: str
    optional_dependencies: tuple[str, ...]
    health_check: Mapping[str, Any]

    def __post_init__(self) -> None:
        _id(self.pack_id, "pack_id")
        _string(self.schema_version, "schema_version")
        _string(self.version, "version")
        _string(self.display_name, "display_name")
        _id(self.domain, "domain")
        object.__setattr__(self, "compatibility", self._normalize_compatibility(self.compatibility))
        for field in (
            "capabilities_provided",
            "required_kernel_capabilities",
            "required_runtime_capabilities",
            "object_types",
            "validator_entrypoints",
            "action_hooks",
            "planning_hooks",
            "optional_dependencies",
            "prohibited_authority_upgrades",
        ):
            object.__setattr__(self, field, _strings(getattr(self, field), field))
        object.__setattr__(self, "human_entries", _relative_paths(self.human_entries, "human_entries"))
        object.__setattr__(self, "machine_entries", _relative_paths(self.machine_entries, "machine_entries"))
        permissions = _mapping(self.permissions_requested, "permissions_requested")
        unknown_permissions = sorted(set(permissions) - PERMISSION_KEYS)
        if unknown_permissions:
            raise PackRegistryError(f"permissions_requested has unknown fields: {unknown_permissions}")
        for field in ("read_paths", "write_paths"):
            permissions[field] = list(_relative_paths(permissions.get(field, []), f"permissions_requested.{field}"))
        for field in ("command_classes", "tool_classes"):
            permissions[field] = list(_strings(permissions.get(field, []), f"permissions_requested.{field}"))
        network = permissions.get("network", False)
        if not isinstance(network, bool):
            raise PackRegistryError("permissions_requested.network must be boolean")
        permissions["network"] = network
        object.__setattr__(self, "permissions_requested", permissions)
        prohibited = set(self.prohibited_authority_upgrades)
        missing = sorted(KERNEL_FORBIDDEN_AUTHORITY_UPGRADES - prohibited)
        if missing:
            raise PackRegistryError(f"pack must prohibit Kernel authority upgrades: {missing}")
        if self.load_policy not in LOAD_POLICIES:
            raise PackRegistryError(f"unsupported load_policy: {self.load_policy}")
        if self.unload_policy not in UNLOAD_POLICIES:
            raise PackRegistryError(f"unsupported unload_policy: {self.unload_policy}")
        health = _mapping(self.health_check, "health_check")
        if health.get("kind") not in HEALTH_CHECK_KINDS or health.get("expected") != "PASS":
            raise PackRegistryError("health_check must be a declarative PASS check")
        if health.get("side_effects", False) is not False:
            raise PackRegistryError("pack health checks must declare side_effects=false")
        object.__setattr__(self, "health_check", health)

    @staticmethod
    def _normalize_compatibility(value: Any) -> tuple[tuple[str, str], ...]:
        mapping = _mapping(value, "compatibility")
        unknown = sorted(set(mapping) - {"kernel_api", "runtime_api", "schema"})
        if unknown:
            raise PackRegistryError(f"compatibility has unknown fields: {unknown}")
        return tuple(sorted((_string(key, "compatibility key"), _string(item, f"compatibility.{key}") ) for key, item in mapping.items()))

    @property
    def compatibility_map(self) -> dict[str, str]:
        return dict(self.compatibility)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "pack_id": self.pack_id,
            "version": self.version,
            "display_name": self.display_name,
            "domain": self.domain,
            "compatibility": self.compatibility_map,
            "capabilities_provided": list(self.capabilities_provided),
            "required_kernel_capabilities": list(self.required_kernel_capabilities),
            "required_runtime_capabilities": list(self.required_runtime_capabilities),
            "object_types": list(self.object_types),
            "validator_entrypoints": list(self.validator_entrypoints),
            "action_hooks": list(self.action_hooks),
            "planning_hooks": list(self.planning_hooks),
            "human_entries": list(self.human_entries),
            "machine_entries": list(self.machine_entries),
            "permissions_requested": copy.deepcopy(dict(self.permissions_requested)),
            "prohibited_authority_upgrades": list(self.prohibited_authority_upgrades),
            "load_policy": self.load_policy,
            "unload_policy": self.unload_policy,
            "optional_dependencies": list(self.optional_dependencies),
            "health_check": copy.deepcopy(dict(self.health_check)),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PackManifest":
        allowed = {
            "schema_version", "pack_id", "version", "display_name", "domain", "compatibility",
            "capabilities_provided", "required_kernel_capabilities", "required_runtime_capabilities",
            "object_types", "validator_entrypoints", "validators", "action_hooks", "planning_hooks",
            "human_entries", "machine_entries", "permissions_requested", "prohibited_authority_upgrades",
            "load_policy", "unload_policy", "optional_dependencies", "health_check",
        }
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise PackRegistryError(f"PackManifest has unknown fields: {unknown}")
        values = dict(data)
        if "validator_entrypoints" not in values:
            values["validator_entrypoints"] = values.pop("validators", [])
        else:
            values.pop("validators", None)
        return cls(**values)

    def validate_root(self, root: Path) -> list[str]:
        errors: list[str] = []
        compatibility = self.compatibility_map
        if compatibility.get("schema") not in {None, PACK_SCHEMA_VERSION}:
            errors.append(f"schema incompatibility: {compatibility.get('schema')}")
        for path in self.human_entries + self.machine_entries + self.validator_entrypoints:
            candidate = root / path
            if not candidate.exists():
                errors.append(f"declared path missing: {path}")
        if self.permissions_requested.get("network"):
            errors.append("network permission is unavailable in offline Pack Bus R1")
        return errors


@dataclass(frozen=True)
class CapabilityRoute:
    capability: str
    pack_id: str
    pack_version: str
    object_types: tuple[str, ...]
    required_kernel_capabilities: tuple[str, ...]
    required_runtime_capabilities: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "object_types": list(self.object_types),
            "required_kernel_capabilities": list(self.required_kernel_capabilities),
            "required_runtime_capabilities": list(self.required_runtime_capabilities),
        }


@dataclass(frozen=True)
class LoadedPack:
    manifest: PackManifest
    load_digest: str
    health: str = "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {"pack_id": self.manifest.pack_id, "version": self.manifest.version, "load_digest": self.load_digest, "health": self.health}


class PackRegistry:
    """Deterministic manifest registry; it never imports a Pack implementation."""

    def __init__(self, root: Path, manifests: Sequence[PackManifest]):
        self.root = root.resolve()
        self._manifests = {manifest.pack_id: manifest for manifest in manifests}
        if len(self._manifests) != len(tuple(manifests)):
            raise PackRegistryError("duplicate pack_id")
        self._routes: dict[str, tuple[CapabilityRoute, ...]] = {}
        for manifest in sorted(self._manifests.values(), key=lambda item: item.pack_id):
            for capability in manifest.capabilities_provided:
                route = CapabilityRoute(
                    capability=capability,
                    pack_id=manifest.pack_id,
                    pack_version=manifest.version,
                    object_types=manifest.object_types,
                    required_kernel_capabilities=manifest.required_kernel_capabilities,
                    required_runtime_capabilities=manifest.required_runtime_capabilities,
                )
                self._routes.setdefault(capability, tuple())
                self._routes[capability] = self._routes[capability] + (route,)

    @classmethod
    def discover(cls, packs_root: Path) -> "PackRegistry":
        root = packs_root.resolve()
        if not root.is_dir():
            raise PackRegistryError(f"packs root is not a directory: {packs_root}")
        paths = sorted(root.glob("*/manifest.json"))
        if not paths:
            raise PackRegistryError(f"no Pack manifests found under: {packs_root}")
        manifests: list[PackManifest] = []
        for path in paths:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                manifests.append(PackManifest.from_dict(data))
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                raise PackRegistryError(f"invalid Pack manifest {path}: {exc}") from exc
        return cls(root.parent, manifests)

    @property
    def pack_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._manifests))

    def get(self, pack_id: str) -> PackManifest:
        try:
            return self._manifests[pack_id]
        except KeyError as exc:
            raise PackRegistryError(f"unknown Pack: {pack_id}") from exc

    def validate(self) -> dict[str, Any]:
        results = []
        for pack_id in self.pack_ids:
            manifest = self.get(pack_id)
            errors = manifest.validate_root(self.root)
            optional_dependencies_available = sorted(dep for dep in manifest.optional_dependencies if dep in self._manifests)
            results.append({"pack_id": pack_id, "version": manifest.version, "status": "PASS" if not errors else "FAIL", "errors": errors, "optional_dependencies_available": optional_dependencies_available})
        status = "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL"
        return {"status": status, "packs": results, "pack_count": len(results), "capability_count": len(self._routes)}

    def routes(self, capability: str | None = None) -> tuple[CapabilityRoute, ...]:
        if capability is None:
            return tuple(route for name in sorted(self._routes) for route in self._routes[name])
        return self._routes.get(capability, tuple())


class PackLoader:
    """Loads validated metadata only; no Python entrypoint is imported or run."""

    def __init__(self, registry: PackRegistry, *, kernel_capabilities: Sequence[str] = ("read_declared", "run_validator", "write_declared"), runtime_capabilities: Sequence[str] = ("runtime.pack_registry", "runtime.pack_bus")):
        self.registry = registry
        self.kernel_capabilities = frozenset(kernel_capabilities)
        self.runtime_capabilities = frozenset(runtime_capabilities)
        self._loaded: dict[str, LoadedPack] = {}

    def load(self, pack_id: str) -> LoadedPack:
        manifest = self.registry.get(pack_id)
        errors = self.registry.validate()
        pack_result = next(item for item in errors["packs"] if item["pack_id"] == pack_id)
        if pack_result["status"] != "PASS":
            raise PackRegistryError(f"Pack {pack_id} failed validation: {pack_result['errors']}")
        compatibility = manifest.compatibility_map
        if compatibility.get("kernel_api") not in SUPPORTED_KERNEL_APIS:
            raise PackRegistryError(f"unsupported Kernel API for {pack_id}: {compatibility.get('kernel_api')}")
        if compatibility.get("runtime_api") not in SUPPORTED_RUNTIME_APIS:
            raise PackRegistryError(f"unsupported Runtime API for {pack_id}: {compatibility.get('runtime_api')}")
        missing_kernel = sorted(set(manifest.required_kernel_capabilities) - self.kernel_capabilities)
        missing_runtime = sorted(set(manifest.required_runtime_capabilities) - self.runtime_capabilities)
        if missing_kernel or missing_runtime:
            raise PackRegistryError(f"capability requirements unavailable for {pack_id}: kernel={missing_kernel}, runtime={missing_runtime}")
        load_digest = _digest({"pack": manifest.to_dict(), "root": str(self.registry.root)})
        loaded = LoadedPack(manifest=manifest, load_digest=load_digest)
        self._loaded[pack_id] = loaded
        return loaded

    def load_all(self) -> tuple[LoadedPack, ...]:
        return tuple(self.load(pack_id) for pack_id in self.registry.pack_ids)

    def unload(self, pack_id: str, *, active_pack_ids: Sequence[str] = ()) -> dict[str, Any]:
        manifest = self.registry.get(pack_id)
        if manifest.unload_policy == "SAFE_IF_NO_ACTIVE_RUNS" and pack_id in set(active_pack_ids):
            raise PackRegistryError(f"cannot unload active Pack: {pack_id}")
        self._loaded.pop(pack_id, None)
        return {"pack_id": pack_id, "status": "UNLOADED"}

    def loaded(self) -> tuple[LoadedPack, ...]:
        return tuple(self._loaded[pack_id] for pack_id in sorted(self._loaded))

    def is_loaded(self, pack_id: str) -> bool:
        return pack_id in self._loaded


class PackBus:
    """Route typed capability proposals without executing domain hooks."""

    def __init__(self, registry: PackRegistry, loader: PackLoader):
        self.registry = registry
        self.loader = loader

    def route(self, capability: str) -> CapabilityRoute:
        routes = tuple(route for route in self.registry.routes(capability) if self.loader.is_loaded(route.pack_id))
        if not routes:
            raise PackRegistryError(f"no loaded Pack provides capability: {capability}")
        if len(routes) > 1:
            raise PackRegistryError(f"ambiguous Pack capability route: {capability}")
        return routes[0]

    def propose(self, capability: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        route = self.route(capability)
        if not isinstance(payload, Mapping):
            raise PackRegistryError("Pack Bus payload must be an object")
        return {
            "status": "ROUTED_PROPOSAL",
            "capability": capability,
            "pack_id": route.pack_id,
            "pack_version": route.pack_version,
            "payload_sha256": _digest(dict(payload)),
            "execution": "NOT_PERFORMED_BY_PACK_BUS",
            "authority_boundary": "Pack hooks remain explicit runtime actions; routing cannot grant permissions or truth authority.",
        }

    def trace(self) -> list[dict[str, Any]]:
        return [route.to_dict() for route in self.registry.routes() if self.loader.is_loaded(route.pack_id)]
