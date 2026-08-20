"""Canonical principal and namespace isolation contracts."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import sha256_json


NAMESPACE_SCHEMA = "ignition-durability-namespace-r1"
PRINCIPAL_TYPES = frozenset({"OWNER", "OPERATOR", "SYSTEM", "EXECUTOR"})
DELEGATION_STATES = frozenset({"ACTIVE", "REVOKED", "EXPIRED"})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


class NamespaceIsolationError(ValueError):
    """Raised when a scope, identity or cross-namespace request is unsafe."""


def _safe_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or ".." in value:
        raise NamespaceIsolationError(f"{field} is not a canonical namespace identifier")
    return value


def validate_relative_path(value: Any, field: str = "path") -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value or value.startswith("file:"):
        raise NamespaceIsolationError(f"{field} must be a portable relative path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise NamespaceIsolationError(f"{field} contains traversal or non-canonical components")
    return value


@dataclass(frozen=True)
class PrincipalIdentity:
    principal_id: str
    principal_type: str
    issuer_ref: str
    identity_digest: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.principal_id, "principal_id")
        if self.principal_type not in PRINCIPAL_TYPES:
            raise NamespaceIsolationError("unknown principal type")
        _safe_id(self.issuer_ref, "issuer_ref")
        expected = sha256_json({"principal_id": self.principal_id, "principal_type": self.principal_type, "issuer_ref": self.issuer_ref})
        if self.identity_digest is not None and self.identity_digest != expected:
            raise NamespaceIsolationError("principal identity digest mismatch")
        object.__setattr__(self, "identity_digest", expected)

    def to_dict(self) -> dict[str, str]:
        return {"principal_id": self.principal_id, "principal_type": self.principal_type, "issuer_ref": self.issuer_ref, "identity_digest": self.identity_digest or ""}


class PrincipalRegistry:
    def __init__(self) -> None:
        self._identities: dict[str, PrincipalIdentity] = {}

    def register(self, identity: PrincipalIdentity) -> PrincipalIdentity:
        existing = self._identities.get(identity.principal_id)
        if existing is not None and existing != identity:
            raise NamespaceIsolationError("principal identity cannot be silently replaced")
        self._identities[identity.principal_id] = identity
        return identity

    def resolve(self, principal_id: str) -> PrincipalIdentity:
        _safe_id(principal_id, "principal_id")
        try:
            return self._identities[principal_id]
        except KeyError as exc:
            raise NamespaceIsolationError("unknown principal") from exc

    def verify(self, identity: PrincipalIdentity) -> PrincipalIdentity:
        stored = self.resolve(identity.principal_id)
        if stored != identity:
            raise NamespaceIsolationError("forged or stale principal identity")
        return stored


@dataclass(frozen=True)
class NamespaceBinding:
    namespace_id: str
    principal_id: str
    workspace_id: str
    episode_id: str
    run_id: str
    memory_scope: str
    pack_activation_scope: str
    executor_lease_scope: str
    snapshot_scope: str
    soft_context_scope: str

    def __post_init__(self) -> None:
        for field in ("namespace_id", "principal_id", "workspace_id", "episode_id", "run_id", "memory_scope", "pack_activation_scope", "executor_lease_scope", "snapshot_scope", "soft_context_scope"):
            _safe_id(getattr(self, field), field)

    @property
    def scope_digest(self) -> str:
        return sha256_json(self.to_dict())

    def to_dict(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in ("namespace_id", "principal_id", "workspace_id", "episode_id", "run_id", "memory_scope", "pack_activation_scope", "executor_lease_scope", "snapshot_scope", "soft_context_scope")}


@dataclass(frozen=True)
class DelegationGrant:
    delegation_id: str
    source_namespace_id: str
    target_namespace_id: str
    issuer_principal_id: str
    subject_principal_id: str
    scopes: tuple[str, ...]
    expires_at: float
    approval_ref: str
    policy_digest: str
    status: str = "ACTIVE"
    grant_digest: str | None = None

    def __post_init__(self) -> None:
        for field in ("delegation_id", "source_namespace_id", "target_namespace_id", "issuer_principal_id", "subject_principal_id", "approval_ref"):
            _safe_id(getattr(self, field), field)
        if not self.scopes or any(not isinstance(scope, str) or not scope.strip() or "*" in scope for scope in self.scopes):
            raise NamespaceIsolationError("delegation scopes must be explicit non-wildcard identifiers")
        if len(self.scopes) != len(set(self.scopes)):
            raise NamespaceIsolationError("delegation scopes must be unique")
        if not isinstance(self.expires_at, (int, float)) or self.expires_at <= 0:
            raise NamespaceIsolationError("delegation expiry must be a positive timestamp")
        if not isinstance(self.policy_digest, str) or len(self.policy_digest) != 64 or any(char not in "0123456789abcdef" for char in self.policy_digest):
            raise NamespaceIsolationError("policy_digest must be a SHA-256 digest")
        if self.status not in DELEGATION_STATES:
            raise NamespaceIsolationError("unknown delegation status")
        expected = sha256_json(self._unsigned_dict())
        if self.grant_digest is not None and self.grant_digest != expected:
            raise NamespaceIsolationError("delegation digest mismatch")
        object.__setattr__(self, "grant_digest", expected)

    def _unsigned_dict(self) -> dict[str, Any]:
        return {"delegation_id": self.delegation_id, "source_namespace_id": self.source_namespace_id, "target_namespace_id": self.target_namespace_id, "issuer_principal_id": self.issuer_principal_id, "subject_principal_id": self.subject_principal_id, "scopes": list(self.scopes), "expires_at": self.expires_at, "approval_ref": self.approval_ref, "policy_digest": self.policy_digest, "status": self.status}

    def active_at(self, now: float) -> bool:
        return self.status == "ACTIVE" and now < self.expires_at


class NamespaceGuard:
    """Default-deny guard for all scope-bearing durable operations."""

    def __init__(self, principal_registry: PrincipalRegistry | None = None) -> None:
        self.principals = principal_registry or PrincipalRegistry()

    def bind(self, binding: NamespaceBinding, principal: PrincipalIdentity) -> NamespaceBinding:
        self.principals.verify(principal)
        if binding.principal_id != principal.principal_id:
            raise NamespaceIsolationError("binding principal does not match verified identity")
        return binding

    def authorize(
        self,
        source: NamespaceBinding,
        target: NamespaceBinding,
        *,
        action: str,
        now: float,
        delegation: DelegationGrant | None = None,
    ) -> None:
        _safe_id(action.replace("/", ":"), "action")
        if source.namespace_id == target.namespace_id:
            if source.workspace_id != target.workspace_id or source.episode_id != target.episode_id:
                raise NamespaceIsolationError("same namespace has inconsistent workspace or episode binding")
            return
        if delegation is None:
            raise NamespaceIsolationError("cross-namespace access is denied without explicit delegation")
        if not delegation.active_at(now):
            raise NamespaceIsolationError("delegation is stale, expired or revoked")
        if delegation.source_namespace_id != source.namespace_id or delegation.target_namespace_id != target.namespace_id:
            raise NamespaceIsolationError("delegation namespace pair mismatch")
        if delegation.subject_principal_id != target.principal_id:
            raise NamespaceIsolationError("delegation subject does not match target principal")
        if action not in delegation.scopes:
            raise NamespaceIsolationError("delegation does not cover requested action")
        self.principals.resolve(delegation.issuer_principal_id)

    def require_snapshot_restore(self, source: NamespaceBinding, target: NamespaceBinding, *, now: float, delegation: DelegationGrant | None = None) -> None:
        self.authorize(source, target, action="snapshot.restore", now=now, delegation=delegation)

    def require_soft_context_exposure(self, source: NamespaceBinding, target: NamespaceBinding, *, now: float, delegation: DelegationGrant | None = None) -> None:
        self.authorize(source, target, action="soft_context.expose", now=now, delegation=delegation)


__all__ = ["DELEGATION_STATES", "NAMESPACE_SCHEMA", "PRINCIPAL_TYPES", "DelegationGrant", "NamespaceBinding", "NamespaceGuard", "NamespaceIsolationError", "PrincipalIdentity", "PrincipalRegistry", "validate_relative_path"]
