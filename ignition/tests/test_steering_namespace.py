from __future__ import annotations

import unittest

from agent_runtime.namespace import DelegationGrant, NamespaceBinding, NamespaceGuard, NamespaceIsolationError, PrincipalIdentity, PrincipalRegistry
from agent_runtime.steering import SteeringNamespaceGuard, SteeringScope


def binding(namespace: str, principal: str, suffix: str) -> NamespaceBinding:
    return NamespaceBinding(namespace, principal, f"workspace-{suffix}", f"episode-{suffix}", f"run-{suffix}", f"memory-{suffix}", f"pack-{suffix}", f"lease-{suffix}", f"snapshot-{suffix}", f"soft-{suffix}")


class SteeringNamespaceTests(unittest.TestCase):
    def setUp(self) -> None:
        registry = PrincipalRegistry()
        registry.register(PrincipalIdentity("principal-a", "OPERATOR", "system-root"))
        registry.register(PrincipalIdentity("principal-b", "OPERATOR", "system-root"))
        self.guard = SteeringNamespaceGuard(NamespaceGuard(registry))
        self.a = binding("ns-a", "principal-a", "a")
        self.b = binding("ns-b", "principal-b", "b")
        self.scope_a = SteeringScope("scope-a", "ns-a", goal_ids=("goal-1",), shared_scope_ref="shared-1")
        self.scope_b = SteeringScope("scope-b", "ns-b", goal_ids=("goal-1",), shared_scope_ref="shared-1")
        self.grant = DelegationGrant("grant-1", "ns-a", "ns-b", "principal-a", "principal-b", ("steering.goal.read",), 200.0, "approval-1", "a" * 64)

    def test_cross_namespace_read_requires_explicit_delegation(self) -> None:
        with self.assertRaises(NamespaceIsolationError):
            self.guard.authorize(self.a, self.scope_a, self.b, self.scope_b, record_kind="goal", record_id="goal-1", action="read", now=100.0)
        self.guard.authorize(self.a, self.scope_a, self.b, self.scope_b, record_kind="goal", record_id="goal-1", action="read", now=100.0, delegation=self.grant)

    def test_record_outside_scope_is_denied(self) -> None:
        with self.assertRaises(NamespaceIsolationError):
            self.guard.authorize(self.a, self.scope_a, self.b, self.scope_b, record_kind="goal", record_id="goal-other", action="read", now=100.0, delegation=self.grant)

    def test_shared_scope_is_required_even_with_grant(self) -> None:
        no_shared = SteeringScope("scope-b2", "ns-b", goal_ids=("goal-1",))
        with self.assertRaises(NamespaceIsolationError):
            self.guard.authorize(self.a, self.scope_a, self.b, no_shared, record_kind="goal", record_id="goal-1", action="read", now=100.0, delegation=self.grant)

    def test_delegation_cannot_grant_canonical_write(self) -> None:
        with self.assertRaises(NamespaceIsolationError):
            self.guard.authorize(self.a, self.scope_a, self.b, self.scope_b, record_kind="intent", record_id="intent-1", action="canonical_write", now=100.0, delegation=self.grant)

    def test_proposal_surface_is_explicitly_scoped(self) -> None:
        proposal_scope = SteeringScope("scope-proposal", "ns-b", proposal_ids=("proposal-1",), shared_scope_ref="shared-1")
        grant = DelegationGrant("grant-proposal", "ns-a", "ns-b", "principal-a", "principal-b", ("steering.proposal.propose",), 200.0, "approval-2", "b" * 64)
        self.guard.authorize_proposal(self.a, self.scope_a, self.b, proposal_scope, record_id="proposal-1", now=100.0, delegation=grant)


if __name__ == "__main__":
    unittest.main()
