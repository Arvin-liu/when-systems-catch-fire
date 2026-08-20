from __future__ import annotations

import unittest

from agent_runtime.namespace import DelegationGrant, NamespaceBinding, NamespaceGuard, NamespaceIsolationError, PrincipalIdentity, PrincipalRegistry, validate_relative_path


def binding(namespace: str, principal: str, workspace: str) -> NamespaceBinding:
    return NamespaceBinding(namespace, principal, workspace, f"episode-{workspace}", f"run-{workspace}", f"memory-{workspace}", f"pack-{workspace}", f"lease-{workspace}", f"snapshot-{workspace}", f"soft-{workspace}")


class DurabilityNamespaceTests(unittest.TestCase):
    def setUp(self) -> None:
        registry = PrincipalRegistry()
        registry.register(PrincipalIdentity("principal-owner", "OWNER", "system-root"))
        registry.register(PrincipalIdentity("principal-a", "OPERATOR", "system-root"))
        registry.register(PrincipalIdentity("principal-b", "OPERATOR", "system-root"))
        self.guard = NamespaceGuard(registry)
        self.a = binding("ns-a", "principal-a", "workspace-a")
        self.b = binding("ns-b", "principal-b", "workspace-b")

    def test_default_cross_namespace_access_is_denied(self) -> None:
        with self.assertRaises(NamespaceIsolationError):
            self.guard.authorize(self.a, self.b, action="memory.read", now=100.0)

    def test_explicit_delegation_scope_expiry_and_issuer_are_required(self) -> None:
        grant = DelegationGrant("delegation-1", "ns-a", "ns-b", "principal-owner", "principal-b", ("snapshot.restore",), 200.0, "approval-1", "a" * 64)
        self.guard.require_snapshot_restore(self.a, self.b, now=100.0, delegation=grant)
        with self.assertRaises(NamespaceIsolationError):
            self.guard.require_soft_context_exposure(self.a, self.b, now=100.0, delegation=grant)
        with self.assertRaises(NamespaceIsolationError):
            self.guard.require_snapshot_restore(self.a, self.b, now=201.0, delegation=grant)

    def test_forged_principal_and_path_traversal_fail_closed(self) -> None:
        with self.assertRaises(NamespaceIsolationError):
            self.guard.bind(self.a, PrincipalIdentity("principal-a", "EXECUTOR", "system-root"))
        for value in ("../escape", "/absolute", "a/../b", "a\\b"):
            with self.assertRaises(NamespaceIsolationError):
                validate_relative_path(value)

    def test_same_namespace_requires_consistent_workspace_and_episode(self) -> None:
        same = binding("ns-a", "principal-b", "workspace-other")
        with self.assertRaises(NamespaceIsolationError):
            self.guard.authorize(self.a, same, action="memory.read", now=100.0)

    def test_snapshot_and_soft_context_scopes_use_same_guard(self) -> None:
        grant = DelegationGrant("delegation-2", "ns-a", "ns-b", "principal-owner", "principal-b", ("snapshot.restore", "soft_context.expose"), 200.0, "approval-2", "b" * 64)
        self.guard.require_snapshot_restore(self.a, self.b, now=100.0, delegation=grant)
        self.guard.require_soft_context_exposure(self.a, self.b, now=100.0, delegation=grant)


if __name__ == "__main__":
    unittest.main()
